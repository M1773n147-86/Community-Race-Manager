"""
Archivo: navigation_view.py
Ubicación: src/cogs/wizards_general/views/

Descripción:
Define la vista y los controles de navegación universales para todos los asistentes (wizards)
del Community Race Manager. Gestiona la transición entre pasos, el avance y retroceso 
dentro del flujo y la cancelación controlada del proceso.

Este componente es totalmente reutilizable por cualquier wizard (eventos, circuitos, vehículos)
gracias a su integración con el sistema de sesiones temporales `EventWizardSession`.
"""

import discord
from discord import ui, Interaction, ButtonStyle
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession

# --------------------------------------------------------
# 🔹 Mapa de pasos del wizard principal (eventos)
# --------------------------------------------------------
STEP_MAP = {
    1: "step_schedule",
    2: "step_track",
    3: "step_vehicles",
    4: "step_settings",
    5: "step_rules",
    6: "step_finalize",
}

# --------------------------------------------------------
# 🔹 Vista universal para los pasos del asistente
# --------------------------------------------------------


class WizardNavigationView(ui.View):
    """Vista reutilizable para todos los pasos del asistente."""

    def __init__(self, user_id: int, current_step: int, total_steps: int = len(STEP_MAP)):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_step = current_step
        self.total_steps = total_steps

        # Botones de navegación dinámicos
        if current_step > 1:
            self.add_item(PreviousStepButton())
        if current_step < total_steps:
            self.add_item(NextStepButton())

        # Botón de cancelación siempre disponible
        self.add_item(CancelWizardButton())


# --------------------------------------------------------
# 🔹 Botón — Paso anterior
# --------------------------------------------------------
class PreviousStepButton(ui.Button):
    def __init__(self):
        super().__init__(label="⬅️ Paso anterior", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        current_step = EventWizardSession.get(user_id).get("step", 1)
        prev_step = current_step - 1

        if prev_step < 1:
            await interaction.response.send_message(
                "⚠️ Ya estás en el primer paso del asistente.",
                ephemeral=True
            )
            return

        EventWizardSession.update(user_id, "step", prev_step)
        await interaction.response.defer(ephemeral=True)
        await load_step(interaction, prev_step)


# --------------------------------------------------------
# 🔹 Botón — Paso siguiente
# --------------------------------------------------------
class NextStepButton(ui.Button):
    def __init__(self):
        super().__init__(label="➡️ Siguiente paso", style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        current_step = EventWizardSession.get(user_id).get("step", 1)
        next_step = current_step + 1
        total_steps = len(STEP_MAP)

        if next_step > total_steps:
            await interaction.response.send_message(
                "✅ Ya has completado todos los pasos del asistente.",
                ephemeral=True
            )
            return

        EventWizardSession.update(user_id, "step", next_step)
        await interaction.response.defer(ephemeral=True)
        await load_step(interaction, next_step)


# --------------------------------------------------------
# 🔹 Botón — Cancelar asistente
# --------------------------------------------------------
class CancelWizardButton(ui.Button):
    def __init__(self):
        super().__init__(label="❌ Cancelar", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        view = CancelConfirmationView(interaction.user.id)
        await interaction.response.send_message(
            "⚠️ ¿Seguro que deseas cancelar la creación del evento?\n"
            "Esto eliminará todos los datos registrados hasta el momento.",
            view=view,
            ephemeral=True
        )


# --------------------------------------------------------
# 🔹 Vista — Confirmación de cancelación
# --------------------------------------------------------
class CancelConfirmationView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(ConfirmCancelButton())
        self.add_item(AbortCancelButton())


class ConfirmCancelButton(ui.Button):
    def __init__(self):
        super().__init__(label="✅ Sí, cancelar", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        EventWizardSession.end(interaction.user.id)
        await interaction.response.edit_message(
            content="🛑 Has cancelado la creación del evento. Todos los datos han sido eliminados.",
            view=None
        )


class AbortCancelButton(ui.Button):
    def __init__(self):
        super().__init__(label="↩️ No, continuar", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(
            content="✅ Continuemos donde lo dejaste.",
            view=None
        )


# --------------------------------------------------------
# 🔹 Función universal — Cargar paso dinámicamente
# --------------------------------------------------------
async def load_step(interaction: Interaction, step_number: int):
    """Carga dinámicamente el paso correspondiente del wizard activo."""
    step_module_name = STEP_MAP.get(step_number)

    if not step_module_name:
        await interaction.response.send_message(
            f"⚠️ Paso {step_number} no definido en el flujo del asistente.",
            ephemeral=True
        )
        return

    try:
        module_path = f"src.cogs.events_wizard.steps.{step_module_name}"
        module = __import__(module_path, fromlist=["show_step"])
        function_name = [f for f in dir(module) if f.startswith("show_")][0]
        show_func = getattr(module, function_name)

        print(f"[NAVIGATION] Cargando paso {step_number}: {step_module_name}")
        await show_func(interaction)

    except Exception as e:
        print(f"[ERROR] Fallo al cargar el paso {step_number}: {e}")
        await interaction.response.send_message(
            f"❌ Error al intentar cargar el paso {step_number}: `{e}`",
            ephemeral=True
        )
