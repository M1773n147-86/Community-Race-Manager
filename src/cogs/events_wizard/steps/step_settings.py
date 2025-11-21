"""
Archivo: step_settings.py
Ubicación: src/cogs/events_wizard/steps/

Descripción:
Define el paso 4 del asistente de creación de eventos — configuración técnica.
Permite establecer parámetros como duraciones, consumos y condiciones de carrera.
Guarda los valores en la sesión del usuario antes de pasar a la fase final.
"""

import discord
from discord import ui, Interaction
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView


# --------------------------------------------------------
# MODAL — CONFIGURACIÓN TÉCNICA DEL EVENTO
# --------------------------------------------------------
class StepSettingsModal(ui.Modal, title="⚙️ Configuración técnica del evento"):
    """Solicita los parámetros técnicos principales del evento."""

    practice_time = ui.TextInput(
        label="Duración práctica (minutos)",
        placeholder="Ej. 30",
        required=False
    )

    qualy_time = ui.TextInput(
        label="Duración clasificación (minutos)",
        placeholder="Ej. 15",
        required=False
    )

    race_time = ui.TextInput(
        label="Duración carrera (minutos o vueltas)",
        placeholder="Ej. 45",
        required=True
    )

    fuel_rate = ui.TextInput(
        label="Consumo de combustible (%)",
        placeholder="Ej. 100",
        required=False
    )

    tire_wear_rate = ui.TextInput(
        label="Desgaste de neumáticos (%)",
        placeholder="Ej. 100",
        required=False
    )

    damage_multiplier = ui.TextInput(
        label="Daños (%)",
        placeholder="Ej. 80",
        required=False
    )

    weather = ui.TextInput(
        label="Climatología",
        placeholder="Ej. Despejado / Lluvia / Nublado",
        required=False
    )

    assists = ui.TextInput(
        label="Asistencias activas (ABS, TC, etc.)",
        placeholder="Ej. ABS: medio, TC: bajo",
        required=False
    )

    async def on_submit(self, interaction: Interaction):
        """Guarda la configuración técnica en la sesión."""
        user_id = interaction.user.id

        def safe_int(value, default=0):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        def safe_float(value, default=100.0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        data = {
            "practice_time": safe_int(self.practice_time.value or 0),
            "qualy_time": safe_int(self.qualy_time.value or 0),
            "race_time": safe_int(self.race_time.value or 0),
            "fuel_rate": safe_float(self.fuel_rate.value or 100.0),
            "tire_wear_rate": safe_float(self.tire_wear_rate.value or 100.0),
            "damage_multiplier": safe_float(self.damage_multiplier.value or 100.0),
            "weather": (self.weather.value or "Despejado").strip(),
            "assists": (self.assists.value or "Sin asistencias").strip(),
        }

        for key, value in data.items():
            EventWizardSession.update(user_id, key, value)

        print(
            f"[STEP 4] Configuración técnica guardada para user_id={user_id}")

        await interaction.response.send_message(
            f"{event_step_header(4, 'Configuración técnica del evento')}\n"
            "✅ Configuración técnica guardada correctamente.\n"
            "A continuación definiremos los **detalles finales** del evento.",
            ephemeral=True
        )

        # Avanzar al siguiente paso
        from src.cogs.events_wizard.steps.step_rules import show_rules_step
        await show_rules_step(interaction)


# --------------------------------------------------------
# FUNCIÓN PRINCIPAL DEL PASO
# --------------------------------------------------------
async def show_settings_step(interaction: Interaction):
    """Lanza el paso 4 del asistente — configuración técnica del evento."""
    print(
        f"[STEP 4] Usuario {interaction.user.name} accedió a la configuración técnica del evento.")

    await interaction.followup.send(
        f"{event_step_header(4, 'Configuración técnica del evento')}\n"
        "Define los parámetros técnicos del evento antes de continuar:",
        ephemeral=True
    )

    modal = StepSettingsModal()
    await interaction.response.send_modal(modal)

    view_nav = WizardNavigationView(interaction.user.id, current_step=4)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para revisar o continuar.",
        view=view_nav,
        ephemeral=True
    )
