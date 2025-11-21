# ========================================================
# Archivo: step_event_type.py
# Ubicación: src/cogs/events_wizard/steps/
# ========================================================

"""
Paso 2 del Event Wizard → Selección del tipo de evento.

Tipos disponibles:
- standard → Evento individual
- league → Evento de liga
- tournament → Torneo estructurado
- championship → Campeonato completo (multirondas)

El resultado se almacena en EventWizardSession y se usa para configurar
ramas posteriores del wizard, scheduler, listados y dashboard.
"""

import discord
from discord import ui, Interaction, SelectOption

from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView


# --------------------------------------------------------
# 🔹 SELECT — Elección del tipo de evento
# --------------------------------------------------------
class EventTypeSelect(ui.Select):
    """Menú desplegable con los 4 tipos de evento estándar."""

    def __init__(self):
        options = [
            SelectOption(label="🏁 Evento individual", value="standard"),
            SelectOption(label="🏎️ Evento de liga", value="league"),
            SelectOption(label="🏆 Evento de torneo", value="tournament"),
            SelectOption(label="🥇 Evento de campeonato", value="championship"),
        ]
        super().__init__(
            placeholder="Selecciona el tipo de evento",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        event_type = self.values[0]

        # Guardar tipo de evento en la sesión
        EventWizardSession.update(
            interaction.user.id, "event_type", event_type)
        EventWizardSession.update(interaction.user.id, "championship_id", None)

        await interaction.response.send_message(
            f"✅ Tipo de evento seleccionado: **{event_type.capitalize()}**",
            ephemeral=True
        )

        # Avanzar inmediatamente al siguiente paso
        from src.cogs.events_wizard.steps.step_track import show_track_step
        await show_track_step(interaction)


# --------------------------------------------------------
# 🔹 VIEW — Contenedor del paso
# --------------------------------------------------------
class StepEventTypeView(ui.View):
    """Vista principal del paso de selección del tipo de evento."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.add_item(EventTypeSelect())


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL DEL PASO
# --------------------------------------------------------
async def show_event_type_step(interaction: Interaction):
    """
    Renderiza el Paso 2 del Event Wizard.
    Se ejecuta inmediatamente después del título del evento.
    """
    user_id = interaction.user.id

    header = event_step_header(2, "Clasificación del evento")

    view = StepEventTypeView(user_id)

    await interaction.followup.send(
        f"{header}\n"
        "Selecciona el tipo de evento antes de continuar con la configuración.",
        view=view,
        ephemeral=True,
    )

    # Navegación estándar
    nav = WizardNavigationView(user_id, current_step=2)
    await interaction.followup.send(
        "🧭 Usa los botones para navegar entre pasos.",
        view=nav,
        ephemeral=True,
    )
