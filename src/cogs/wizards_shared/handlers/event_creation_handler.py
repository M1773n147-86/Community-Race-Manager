"""
Archivo: event_creation_handler.py
Ubicación: src/cogs/wizards_general/handlers/

Descripción:
Contiene el manejador (handler) responsable de iniciar el flujo del wizard de 
creación de eventos. Este archivo actúa como punto intermedio entre el comando 
de barra `/create_event` y la interfaz visual del asistente (View + Modal).
Su propósito es mantener la lógica de inicialización desacoplada del comando 
y centralizar el arranque del proceso.
"""

import discord
from discord.ext import commands
from src.cogs.wizards_shared.views.event_creation_view import EventCreationWizardView


class EventCreationHandler(commands.Cog):
    """
    Manejador del flujo de creación de eventos.
    Se encarga de iniciar la vista interactiva y preparar el entorno temporal 
    para el usuario que lanza el comando.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def start_wizard(self, interaction: discord.Interaction):
        """
        Lanza la vista principal del wizard de creación de eventos.
        """
        view = EventCreationWizardView(interaction.user.id)
        await interaction.response.send_message(
            "🚀 **Asistente de creación de evento iniciado.**\nPor favor, indica el título del evento.",
            view=view,
            ephemeral=True
        )
        await view.step_1_title(interaction)


async def setup(bot: commands.Bot):
    """Registra el Cog en el bot principal."""
    await bot.add_cog(EventCreationHandler(bot))
