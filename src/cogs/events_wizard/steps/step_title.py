"""
Archivo: step_title.py
Ubicación: src/cogs/events_wizard/steps/

Descripción:
Define el paso 1 del asistente de creación de eventos (Event Wizard).
Su función es solicitar y almacenar el título del evento, garantizando
una validación básica antes de continuar al siguiente paso (selección de circuito).
"""

import discord
from discord import Interaction, TextStyle
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header


class StepTitleModal(discord.ui.Modal, title="📝 Título del evento"):
    """Paso 1 del Event Wizard — Solicita el título del evento."""

    event_title = discord.ui.TextInput(
        label="Título del evento",
        placeholder="Ejemplo: Carrera GT3 - Spa Francorchamps",
        max_length=100,
        style=TextStyle.short
    )

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: Interaction):
        """Valida y guarda el título introducido por el usuario."""
        title = self.event_title.value.strip()

        # Validación básica
        if len(title) < 3:
            await interaction.response.send_message(
                "⚠️ El título es demasiado corto. Intenta de nuevo.",
                ephemeral=True
            )
            return

        # Guardar título en la sesión del wizard
        user_id = interaction.user.id
        EventWizardSession.update(user_id, "title", title)

        await interaction.response.send_message(
            f"{event_step_header(1, 'Título del evento')}\n"
            f"✅ El título **{title}** ha sido registrado correctamente.",
            ephemeral=True
        )

        # Avanzar directamente al paso siguiente (selección de circuito)
        from src.cogs.events_wizard.steps.step_track import show_track_step
        await show_track_step(interaction)
