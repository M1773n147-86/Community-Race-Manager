"""
Archivo: step_title_legacy.py
Ubicación: src/archive/

Descripción:
Versión preliminar del primer paso del asistente de creación de eventos.
Recoge el título y la descripción del evento usando el antiguo sistema 
`EventWizardSession` y vistas de navegación. Reemplazado completamente por 
`EventTitleModal` en `wizards_general/modals/title_modal.py`, pero se conserva 
como referencia para futuras mejoras de UX (por ejemplo, encabezados dinámicos 
o validaciones extendidas).
"""


import discord
from discord import ui, Interaction
from utils.wizard_session import EventWizardSession
from .step_schedule import show_schedule_step
from utils.wizard_constants import wizard_step_header


class StepTitleModal(ui.Modal, title="🎯 Título y descripción del evento"):
    """Primer paso: obtener el título y descripción del evento."""

    title_input = ui.TextInput(
        label="Título del evento",
        placeholder="Ejemplo: Gran Premio de Monza",
        required=True
    )

    description_input = ui.TextInput(
        label="Agrega una descripción breve",
        placeholder="Ejemplo: Carrera amistosa de GT3 en Monza.",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )

    async def on_submit(self, interaction: Interaction):
        """Guarda los datos en sesión y pasa al siguiente paso."""
        user_id = interaction.user.id
        EventWizardSession.update(
            user_id, "title", str(self.title_input.value))
        EventWizardSession.update(
            user_id, "description", str(self.description_input.value))

        # 🧾 Encabezado del paso con numeración dinámica
        await interaction.response.send_message(
            f"{wizard_step_header(1, 'Título y descripción del evento')}\n"
            "✅ Título y descripción guardados. Continuando con el asistente...",
            ephemeral=True
        )

        print(
            f"[STEP 1] Usuario {interaction.user.name} completó título y descripción.")

        # Agregar vista de navegación universal (Inicio del wizard)
        from cogs.wizard.managers.navigation_manager import WizardNavigationView
        view = WizardNavigationView(interaction.user.id, current_step=1)

        await interaction.followup.send(
            "🧭 Controles del asistente:",
            view=view,
            ephemeral=True
        )

        # El flujo continuará con el botón "➡ Siguiente"
        print("[WIZARD] Esperando confirmación del usuario para avanzar al paso 2.")


# 🔹 Esta función es la que se importa desde create_event.py
async def show_title_step(interaction: Interaction):
    """Muestra el modal para ingresar título y descripción."""
    modal = StepTitleModal()
    await interaction.response.send_modal(modal)
