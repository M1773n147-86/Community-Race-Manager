"""
Archivo: event_creation_view.py
Ubicación: src/cogs/wizards_general/views/

Descripción:
Define la vista principal del asistente de creación de eventos (wizard). 
Gestiona la navegación paso a paso y coordina las interacciones del usuario 
durante el proceso de configuración del evento. Esta clase se apoya en las 
sesiones temporales almacenadas en memoria (utils.session_manager) y puede 
ser reutilizada o extendida por otros módulos de wizard.
"""

import discord
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession


class EventCreationWizardView(discord.ui.View):
    """
    Vista principal del wizard de creación de eventos.
    Controla la navegación entre pasos, el estado de la sesión y las acciones
    básicas como avanzar o cancelar el proceso.
    """

    def __init__(self, user_id: int):
        super().__init__(timeout=600)  # 10 minutos de inactividad
        self.user_id = user_id
        self.current_step = 1

        # Crear sesión temporal
        EventWizardSession.start(user_id, {"step": 1, "data": {}})

    async def update_message(self, interaction: discord.Interaction, content: str):
        """Actualiza el mensaje ephemeral con nuevo contenido."""
        await interaction.response.edit_message(content=content, view=self)

    async def next_step(self, interaction: discord.Interaction):
        """Avanza al siguiente paso del wizard."""
        self.current_step += 1
        EventWizardSession.update(self.user_id, "step", self.current_step)

        if self.current_step == 2:
            await self.step_2_description(interaction)
        else:
            await self.finish_wizard(interaction)

    async def cancel_wizard(self, interaction: discord.Interaction):
        """Cancela el proceso y elimina la sesión temporal."""
        EventWizardSession.delete(self.user_id)
        await interaction.response.edit_message(
            content="❌ **Creación de evento cancelada.**",
            view=None
        )

    # ---------- PASO 1: Título del evento ----------
    async def step_1_title(self, interaction: discord.Interaction):
        """Solicita el título del evento (abre un modal específico)."""
        from src.cogs.events_wizard.steps.step_title import EventTitleModal
        modal = EventTitleModal(self)
        await interaction.response.send_modal(modal)

    # ---------- PASO 2: Descripción (placeholder) ----------
    async def step_2_description(self, interaction: discord.Interaction):
        """Placeholder para el segundo paso del wizard."""
        await self.update_message(
            interaction,
            "✅ **Título registrado correctamente.**\nAhora, escribe una breve descripción del evento."
        )

    async def finish_wizard(self, interaction: discord.Interaction):
        """Finaliza el proceso y muestra los datos recopilados."""
        session_data = EventWizardSession.get(self.user_id)
        data = session_data.get("data", {})
        EventWizardSession.delete(self.user_id)
        await interaction.response.edit_message(
            content=f"🎉 **Evento creado parcialmente (pasos iniciales OK)**\nDatos recopilados: `{data}`",
            view=None
        )
