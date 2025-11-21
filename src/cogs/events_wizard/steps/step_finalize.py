"""
Archivo: step_finalize.py
Ubicación: src/cogs/events_wizard/steps/

Descripción general:
Este módulo representa el paso final (6) del asistente de creación de eventos (Events Wizard).
Su función es mostrar un resumen completo de los datos recopilados y ofrecer
opciones finales de gestión:

🟢 Publicar ahora → cambia el estado a 'active' e inserta el evento en la base de datos.  
💾 Guardar borrador → almacena el evento como 'draft' para su posterior edición.  
🗓️ Programar evento → delega la publicación al Scheduler Wizard (status = 'scheduled').  
🗂️ Archivar → marca el evento como 'archived' con caducidad de 30 días.  
❌ Cancelar → cierra el asistente y elimina la sesión temporal.

Cada acción actualiza las columnas de trazabilidad (`created_by`, `last_edited_by`,
`published_at`, `archived_at`, etc.) y aplica la estructura de estado definida
en el modelo de datos de la aplicación.
"""

import discord
from discord import ui, Interaction, Embed, ButtonStyle
from datetime import datetime, timedelta, timezone
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.database.db import Database
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView


# --------------------------------------------------------
# 🧭 Vista Final — Confirmación, guardado y publicación
# --------------------------------------------------------
class FinalizeEventView(ui.View):
    """Vista principal del paso 6 — revisión y publicación del evento."""

    def __init__(self, user_id: int, event_data: dict):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.event_data = event_data

        # Controles principales
        self.add_item(PublishButton())
        self.add_item(SaveDraftButton())
        self.add_item(ScheduleButton())
        self.add_item(ArchiveButton())
        self.add_item(CancelButton())

        # Navegación final (retroceder, cancelar)
        self.add_item(WizardNavigationView(user_id, current_step=6))


# --------------------------------------------------------
# 🟢 Publicar evento inmediatamente (status = active)
# --------------------------------------------------------
class PublishButton(ui.Button):
    def __init__(self):
        super().__init__(label="🟢 Publicar ahora", style=ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        """Publica el evento inmediatamente."""
        user_id = interaction.user.id
        data = EventWizardSession.get(user_id)
        if not data:
            return await interaction.response.send_message(
                "⚠️ No hay datos de evento para publicar.", ephemeral=True
            )

        db = await Database.get_instance()
        now = datetime.now(timezone.utc)

        try:
            data.update({
                "guild_id": interaction.guild_id,
                "created_by": interaction.user.id,
                "is_published": 1,
                "status": "active",
                "published_at": now.isoformat(),
                "last_edited_by": interaction.user.id,
                "last_edited_date": now.isoformat(),
            })

            await db.events.insert_event(data)
            EventWizardSession.end(user_id)

            print(
                f"[EVENT] Evento publicado: {data.get('title', 'Sin título')}")
            await interaction.response.send_message(
                f"{event_step_header(6, 'Publicación del evento')}\n✅ **Evento publicado con éxito.** 🎉",
                ephemeral=True,
            )

        except Exception as e:
            print(f"[ERROR] Error al publicar evento: {e}")
            await interaction.response.send_message(
                f"❌ Error al publicar el evento: `{e}`", ephemeral=True
            )


# --------------------------------------------------------
# 💾 Guardar como borrador (status = draft)
# --------------------------------------------------------
class SaveDraftButton(ui.Button):
    def __init__(self):
        super().__init__(label="💾 Guardar borrador", style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        """Guarda el evento como borrador."""
        user_id = interaction.user.id
        data = EventWizardSession.get(user_id)
        if not data:
            return await interaction.response.send_message(
                "⚠️ No hay datos de evento para guardar.", ephemeral=True
            )

        db = await Database.get_instance()
        now = datetime.now(timezone.utc)

        try:
            data.update({
                "guild_id": interaction.guild_id,
                "created_by": interaction.user.id,
                "is_published": 0,
                "status": "draft",
                "last_edited_by": interaction.user.id,
                "last_edited_date": now.isoformat(),
            })

            await db.events.insert_event(data)
            EventWizardSession.end(user_id)

            print(
                f"[EVENT] Borrador guardado: {data.get('title', 'Sin título')}")
            await interaction.response.send_message(
                f"{event_step_header(6, 'Guardado de borrador')}\n💾 **Evento guardado como borrador.**",
                ephemeral=True,
            )

        except Exception as e:
            print(f"[ERROR] Error al guardar borrador: {e}")
            await interaction.response.send_message(
                f"❌ Error al guardar el evento: `{e}`", ephemeral=True
            )


# --------------------------------------------------------
# 🗓️ Programar publicación (status = scheduled)
# --------------------------------------------------------
class ScheduleButton(ui.Button):
    """Abre el Scheduler Wizard para programar el evento."""

    def __init__(self):
        super().__init__(label="🗓️ Programar evento", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        data = EventWizardSession.get(user_id)

        if not data:
            await interaction.response.send_message(
                "⚠️ No hay datos de evento para programar.",
                ephemeral=True
            )
            return

        try:
            # ✅ Nuevo flujo centralizado
            from src.cogs.scheduler_wizard.handlers.scheduler_handler import start_scheduler_for_current_event
            await start_scheduler_for_current_event(interaction)
        except Exception as e:
            # Fallback seguro en caso de error durante la importación
            EventWizardSession.update(user_id, "intent_to_schedule", True)
            await interaction.response.send_message(
                f"⚠️ No se pudo iniciar el planificador automáticamente.\n"
                f"Error: `{e}`\n"
                "El evento fue marcado para programación. Puedes completarlo más tarde con `/schedule_saved_event`.",
                ephemeral=True
            )


# --------------------------------------------------------
# 🗂️ Archivar evento (status = archived)
# --------------------------------------------------------
class ArchiveButton(ui.Button):
    def __init__(self):
        super().__init__(label="🗂️ Archivar evento", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        """Envía el evento a la papelera (caduca en 30 días)."""
        user_id = interaction.user.id
        data = EventWizardSession.get(user_id)
        if not data:
            return await interaction.response.send_message(
                "⚠️ No hay datos de evento para archivar.", ephemeral=True
            )

        db = await Database.get_instance()
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=30)

        try:
            data.update({
                "guild_id": interaction.guild_id,
                "created_by": interaction.user.id,
                "is_published": 0,
                "status": "archived",
                "archived_at": now.isoformat(),
                "archive_expires_at": expiry.isoformat(),
                "last_edited_by": interaction.user.id,
                "last_edited_date": now.isoformat(),
            })

            await db.events.insert_event(data)
            EventWizardSession.end(user_id)

            print(
                f"[EVENT] Evento archivado: {data.get('title', 'Sin título')}")
            await interaction.response.send_message(
                f"{event_step_header(6, 'Archivado del evento')}\n"
                f"🗂️ **Evento archivado correctamente.** Será eliminado automáticamente el "
                f"**{expiry.strftime('%Y-%m-%d %H:%M UTC')}**.",
                ephemeral=True,
            )

        except Exception as e:
            print(f"[ERROR] Error al archivar evento: {e}")
            await interaction.response.send_message(
                f"❌ Error al archivar el evento: `{e}`", ephemeral=True
            )


# --------------------------------------------------------
# ❌ Cancelar creación
# --------------------------------------------------------
class CancelButton(ui.Button):
    def __init__(self):
        super().__init__(label="❌ Cancelar", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        EventWizardSession.end(interaction.user.id)
        print(f"[SESSION] Wizard cancelado por {interaction.user.name}")
        await interaction.response.send_message("🛑 Creación de evento cancelada.", ephemeral=True)


# --------------------------------------------------------
# 🔹 Paso Final — Revisión general
# --------------------------------------------------------
async def show_finalize_step(interaction: Interaction):
    """Muestra el resumen del evento y las opciones finales."""
    user_id = interaction.user.id
    data = EventWizardSession.get(user_id)
    if not data:
        return await interaction.response.send_message(
            "⚠️ No se encontró información del evento actual.", ephemeral=True
        )

    print(
        f"[STEP 6] {interaction.user.name} llegó al paso final (revisión y publicación).")

    embed = Embed(
        title=f"📋 Resumen del evento: {data.get('title', 'Sin título')}",
        description=data.get("description", "Sin descripción."),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="🏁 Circuito", value=data.get(
        "track_name", "N/A"), inline=False)
    embed.add_field(name="🕓 Fecha", value=data.get(
        "event_datetime_utc", "N/A"), inline=True)
    embed.add_field(name="🌍 Zona horaria", value=data.get(
        "timezone", "N/A"), inline=True)
    embed.add_field(name="🏎️ Duración",
                    value=f"{data.get('race_time', 'N/A')} min", inline=True)
    embed.add_field(name="🔧 Asistencias", value=data.get(
        "assists", "N/A"), inline=True)
    embed.add_field(name="🌤️ Clima", value=data.get(
        "weather", "N/A"), inline=True)
    embed.set_footer(
        text="Revisa toda la información antes de publicar o guardar el evento.")

    await interaction.followup.send(
        f"🧾 {event_step_header(6, 'Revisión y publicación del evento')}\n"
        "Verifica que todos los datos sean correctos antes de continuar:",
        embed=embed,
        view=FinalizeEventView(user_id, data),
        ephemeral=True,
    )

    await interaction.followup.send(
        "🧭 Fin del asistente — revisa o retrocede si necesitas cambios.",
        view=WizardNavigationView(interaction.user.id, current_step=6),
        ephemeral=True,
    )
