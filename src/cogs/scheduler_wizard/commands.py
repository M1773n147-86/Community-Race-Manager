"""
Archivo: commands.py
Ubicación: src/cogs/scheduler_wizard/

Descripción:
Define el comando `/schedule_saved_event`, que permite programar un evento existente
(previamente creado como borrador mediante el Events Wizard) para su publicación o gestión automatizada.

Flujo general:
1️⃣ Seleccionar el evento guardado (en estado 'draft')
2️⃣ Mostrar los detalles del evento y confirmar la programación
3️⃣ Iniciar el Scheduler Wizard completo (step_name → step_publish_date → ... → step_finalize)

El tipo de evento (individual, liga, torneo, campeonato) ahora se gestiona
desde `events_wizard/steps/step_event_type.py`, para mantener la coherencia
con el flujo de creación de eventos.
"""

import discord
from discord import app_commands, ui, Interaction
from discord.ext import commands
from database.db import Database
from src.cogs.scheduler_wizard.utils.scheduler_session import SchedulerWizardSession


# --------------------------------------------------------
# 🔹 COG PRINCIPAL
# --------------------------------------------------------
class ScheduleSavedEvent(commands.Cog):
    """Cog principal para programar eventos ya existentes (en estado 'draft')."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="schedule_saved_event",
        description="Programa un evento existente para publicación o recordatorios automáticos."
    )
    async def schedule_saved_event(self, interaction: Interaction):
        """Comando principal: inicia el flujo de selección de evento a programar."""
        db = await Database.get_instance()
        conn = await db.get_connection()

        # Recuperar eventos en borrador
        cur = await conn.execute("""
            SELECT event_id, title, description, event_type, status, created_by, created_at,
                   last_edited_by, last_edited_date
            FROM events
            WHERE status = 'draft'
            ORDER BY created_at DESC
        """)
        rows = await cur.fetchall()
        await cur.close()

        if not rows:
            await interaction.response.send_message(
                "⚠️ No hay eventos en borrador disponibles para programar.",
                ephemeral=True
            )
            return

        # Convertir filas a diccionarios
        events = [{
            "event_id": r[0],
            "title": r[1],
            "description": r[2],
            "event_type": r[3] or "standard",
            "status": r[4],
            "created_by": r[5],
            "created_at": r[6],
            "last_edited_by": r[7],
            "last_edited_date": r[8],
        } for r in rows]

        # Mostrar selector inicial de eventos (sin clasificación por tipo)
        await interaction.response.send_message(
            "📋 **Selecciona un evento guardado para programar:**",
            view=EventSelectView(interaction.user.id, events),
            ephemeral=True
        )


# --------------------------------------------------------
# 🔹 VISTA — Selección del evento específico
# --------------------------------------------------------
class EventSelectView(ui.View):
    """Vista que muestra la lista de eventos disponibles para programar."""

    def __init__(self, user_id: int, events: list[dict]):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(EventSelect(self, events))


class EventSelect(ui.Select):
    """Selector de evento con descripción extendida y metadatos."""

    def __init__(self, parent, events):
        options = []
        for ev in events:
            created = (ev.get("created_at") or "N/A")[:16]
            edited = (ev.get("last_edited_date") or "N/A")[:16]
            label = ev.get("title", "Sin título")
            description = f"📅 Creado: {created} | ✏️ Editado: {edited}"
            options.append(discord.SelectOption(
                label=label, description=description, value=str(ev["event_id"])
            ))
        super().__init__(placeholder="Selecciona un evento para programar", options=options)
        self.parent = parent

    async def callback(self, interaction: Interaction):
        selected_id = int(self.values[0])
        db = await Database.get_instance()
        event = await db.events.get_event(selected_id)

        # Iniciar sesión temporal del Scheduler Wizard
        SchedulerWizardSession.start(interaction.user.id, event)

        # Embed con metadatos del evento
        embed = discord.Embed(
            title=f"📋 {event['title']}",
            description=event.get("description", "Sin descripción."),
            color=discord.Color.blurple()
        )
        embed.add_field(name="🧩 Tipo", value=event.get(
            "event_type", "standard"), inline=True)
        embed.add_field(name="⚙️ Estado", value=event.get(
            "status", "draft"), inline=True)
        embed.add_field(name="👤 Creado por", value=event.get(
            "created_by", "Desconocido"), inline=True)
        embed.add_field(name="🗓️ Creado el", value=event.get(
            "created_at", "N/A")[:16], inline=True)
        embed.add_field(name="✏️ Editado por", value=event.get(
            "last_edited_by", "N/A"), inline=True)
        embed.add_field(name="🕓 Última edición", value=event.get(
            "last_edited_date", "N/A")[:16], inline=True)

        await interaction.response.send_message(
            "¿Deseas programar este evento?",
            embed=embed,
            view=ConfirmScheduleView(interaction.user.id),
            ephemeral=True
        )


# --------------------------------------------------------
# 🔹 VISTA — Confirmación final
# --------------------------------------------------------
class ConfirmScheduleView(ui.View):
    """Confirma si se lanza el Scheduler Wizard o se cancela."""

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.add_item(StartSchedulerButton())
        self.add_item(CancelButton())


class StartSchedulerButton(ui.Button):
    """Botón para iniciar el flujo del Scheduler Wizard."""

    def __init__(self):
        super().__init__(label="🗓️ Programar evento", style=discord.ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        from src.cogs.scheduler_wizard.steps.step_name import show_step
        await show_step(interaction)


class CancelButton(ui.Button):
    """Botón para cancelar la operación."""

    def __init__(self):
        super().__init__(label="❌ Cancelar", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        SchedulerWizardSession.end(interaction.user.id)
        await interaction.response.send_message("❌ Operación cancelada.", ephemeral=True)


# --------------------------------------------------------
# 🔹 REGISTRO DEL COG
# --------------------------------------------------------
async def setup(bot: commands.Bot):
    """Registra el comando en el bot principal."""
    await bot.add_cog(ScheduleSavedEvent(bot))
