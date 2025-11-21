"""
Archivo: step_name.py
Ubicación: src/cogs/scheduler_wizard/steps/

Descripción:
Primer paso del Scheduler Wizard. Permite definir o validar el nombre del evento
antes de continuar con la programación. Si el evento ya existe, carga el nombre
actual y permite editarlo; si no existe, exige uno nuevo y verifica que no esté
duplicado dentro del mismo servidor.
"""

import discord
from discord import ui, Interaction
from database.db import Database
from src.cogs.scheduler_wizard.handlers.scheduler_handler import SchedulerWizardSession, go_to_step
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView


# --------------------------------------------------------
# 🔹 MODAL — Introducir o editar nombre del evento
# --------------------------------------------------------

class SchedulerNameModal(ui.Modal, title="📝 Nombre del evento"):
    event_name = ui.TextInput(
        label="Título del evento",
        placeholder="Ejemplo: Campeonato GT3 — Ronda 3",
        required=True,
        max_length=100,
    )

    def __init__(self, user_id: int, existing_name: str = "", guild_id: int | None = None):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
        if existing_name:
            self.event_name.default = existing_name

    async def on_submit(self, interaction: Interaction):
        name = self.event_name.value.strip()
        if not name:
            await interaction.response.send_message(
                "⚠️ Debes proporcionar un nombre para el evento.",
                ephemeral=True
            )
            return

        # Validar duplicado (case-insensitive por guild)
        db = await Database.get_instance()
        conn = await db.get_connection()
        cur = await conn.execute(
            "SELECT COUNT(*) FROM events WHERE LOWER(title) = LOWER(?) AND guild_id = ?",
            (name, self.guild_id or interaction.guild_id)
        )
        count = (await cur.fetchone())[0]
        if count > 0:
            await interaction.response.send_message(
                f"⚠️ Ya existe un evento con el nombre **{name}** en este servidor. Usa otro nombre.",
                ephemeral=True
            )
            return

        # Guardar en sesión
        SchedulerWizardSession.update(self.user_id, "title", name)
        SchedulerWizardSession.update(
            self.user_id, "guild_id", interaction.guild_id)

        await interaction.response.send_message(
            f"✅ Nombre del evento establecido: **{name}**",
            ephemeral=True
        )

        # Avanzar al siguiente paso (Paso 2)
        await go_to_step(interaction, 2)


# --------------------------------------------------------
# 🔹 VISTA PRINCIPAL DEL PASO
# --------------------------------------------------------

class SchedulerNameView(ui.View):
    """Vista principal del Paso 1 — validación o creación de nombre."""

    def __init__(self, user_id: int, existing_name: str = "", guild_id: int | None = None):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.add_item(SetNameButton(user_id, existing_name, guild_id))


class SetNameButton(ui.Button):
    def __init__(self, user_id: int, existing_name: str = "", guild_id: int | None = None):
        label = "✏️ Editar nombre" if existing_name else "🆕 Asignar nombre"
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.user_id = user_id
        self.existing_name = existing_name
        self.guild_id = guild_id

    async def callback(self, interaction: Interaction):
        modal = SchedulerNameModal(
            self.user_id, self.existing_name, self.guild_id)
        await interaction.response.send_modal(modal)


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL — Mostrar paso 1
# --------------------------------------------------------

async def show_step(interaction: Interaction):
    """Muestra el paso 1 del Scheduler Wizard."""
    user_id = interaction.user.id
    session = SchedulerWizardSession.get(user_id)
    existing_name = session.get("title", "")
    guild_id = session.get("guild_id") or interaction.guild_id

    # Encabezado informativo
    await interaction.followup.send(
        "📝 **Paso 1/5 — Definir nombre del evento**\n"
        "Cada evento debe tener un nombre único dentro del servidor. "
        "Puedes mantener el actual o asignar uno nuevo.",
        view=SchedulerNameView(user_id, existing_name, guild_id),
        ephemeral=True
    )

    # Controles de navegación universales
    nav = WizardNavigationView(user_id, current_step=1, total_steps=5)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para continuar o cancelar.",
        view=nav,
        ephemeral=True
    )
