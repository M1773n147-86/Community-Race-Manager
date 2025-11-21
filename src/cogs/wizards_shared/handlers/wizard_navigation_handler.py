"""
Archivo: wizard_navigation_handler.py
Ubicación: src/cogs/wizards_general/handlers/

Descripción:
Este módulo implementa el controlador universal de navegación para los asistentes
(wizards) de Community Race Manager. Gestiona las acciones de paso anterior,
siguiente, cancelación y guardado, asegurando una navegación coherente entre los
módulos de pasos (`step_*.py`) sin duplicar lógica.

La validación de campos requeridos por paso se centraliza aquí para garantizar
que el usuario complete la información mínima antes de continuar. Los pasos se
cargan dinámicamente según la estructura definida en el mapa STEP_MAP del
wizard correspondiente (por ejemplo, `events_wizard`).
"""

import importlib
import discord
from discord import Interaction
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession


class WizardNavigationHandler:
    """Controlador universal de navegación y validación de pasos."""

    def __init__(self, user_id: int, current_step: int, total_steps: int = 6):
        self.user_id = user_id
        self.current_step = current_step
        self.total_steps = total_steps

    # ------------------------------------------------------------
    # Mapa de pasos por defecto (para el Events Wizard)
    # ------------------------------------------------------------
    STEP_MAP_EVENTS = {
        1: "step_title",
        2: "step_schedule",
        3: "step_track",
        4: "step_vehicles",
        5: "step_rules",
        6: "step_finalize"
    }

    # ------------------------------------------------------------
    # Validaciones mínimas por paso
    # ------------------------------------------------------------
    REQUIRED_FIELDS = {
        1: ["title"],
        2: ["event_datetime_utc"],
        3: ["track_name", "track_list_id"],
        4: ["vehicle_text", "vehicle_list_id"],
        5: ["race_time"],
    }

    # ------------------------------------------------------------
    # Validación genérica de datos antes de avanzar
    # ------------------------------------------------------------
    def validate_step(self, step_data: dict, step_number: int) -> tuple[bool, list[str]]:
        """Valida si los campos requeridos para el paso están completos."""
        missing = []
        required = self.REQUIRED_FIELDS.get(step_number, [])
        for field in required:
            value = step_data.get(field)
            if value in (None, "", [], {}):
                missing.append(field)
        return (len(missing) == 0, missing)

    # ------------------------------------------------------------
    # Acción: ir al paso anterior
    # ------------------------------------------------------------
    async def previous_step(self, interaction: Interaction, step_map: dict | None = None):
        """Retrocede un paso, salvo si ya está en el primero."""
        if self.current_step <= 1:
            await interaction.response.send_message(
                "⚠️ Ya estás en el primer paso del asistente.",
                ephemeral=True
            )
            return

        prev_step = self.current_step - 1
        EventWizardSession.update(self.user_id, "step", prev_step)
        await self.load_step(interaction, prev_step, step_map or self.STEP_MAP_EVENTS)

    # ------------------------------------------------------------
    # Acción: ir al siguiente paso
    # ------------------------------------------------------------
    async def next_step(self, interaction: Interaction, step_map: dict | None = None):
        """Avanza al siguiente paso si la validación del actual es correcta."""
        session = EventWizardSession.get(self.user_id) or {}
        valid, missing = self.validate_step(session, self.current_step)

        if not valid:
            msg = "⚠️ No puedes continuar. Faltan los siguientes datos:\n"
            msg += "\n".join([f"❌ `{f}`" for f in missing])
            await interaction.response.send_message(msg, ephemeral=True)
            return

        next_step = self.current_step + 1
        if next_step > self.total_steps:
            await interaction.response.send_message(
                "✅ Has completado todos los pasos del asistente.",
                ephemeral=True
            )
            return

        EventWizardSession.update(self.user_id, "step", next_step)
        await self.load_step(interaction, next_step, step_map or self.STEP_MAP_EVENTS)

    # ------------------------------------------------------------
    # Acción: cancelar asistente
    # ------------------------------------------------------------
    async def cancel_wizard(self, interaction: Interaction):
        """Cancela el proceso y elimina la sesión activa."""
        EventWizardSession.end(self.user_id)
        await interaction.response.send_message(
            "🛑 Asistente cancelado. Todos los datos han sido eliminados.",
            ephemeral=True
        )

    # ------------------------------------------------------------
    # Acción: guardar progreso manualmente (si aplica)
    # ------------------------------------------------------------
    async def save_wizard(self, interaction: Interaction):
        """Guarda los datos actuales sin finalizar el asistente."""
        session_data = EventWizardSession.get(self.user_id)
        if not session_data:
            await interaction.response.send_message(
                "⚠️ No hay datos activos para guardar.",
                ephemeral=True
            )
            return

        # Futuro: integración directa con base de datos o export temporal
        await interaction.response.send_message(
            "💾 Progreso guardado temporalmente en la sesión.",
            ephemeral=True
        )

    # ------------------------------------------------------------
    # Cargador dinámico de pasos
    # ------------------------------------------------------------
    async def load_step(self, interaction: Interaction, step_number: int, step_map: dict):
        """Carga dinámicamente el paso del wizard indicado por el mapa de pasos."""
        module_name = step_map.get(step_number)
        if not module_name:
            await interaction.response.send_message(
                f"⚠️ Paso {step_number} no definido en el mapa de pasos.",
                ephemeral=True
            )
            return

        try:
            module_path = f"cogs.events_wizard.steps.{module_name}"
            module = importlib.import_module(module_path)
            show_func = getattr(module, [f for f in dir(
                module) if f.startswith('show_')][0])
            await show_func(interaction)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error al cargar el paso {step_number}: `{e}`",
                ephemeral=True
            )
