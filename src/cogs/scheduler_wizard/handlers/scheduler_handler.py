"""
Archivo: scheduler_handler.py
Ubicación: src/cogs/scheduler_wizard/handlers/

Descripción:
Punto de entrada principal del Scheduler Wizard.
Este módulo inicia el flujo de programación de eventos creados o en borrador,
ya sea desde el botón "🗓️ Programar evento" del `events_wizard` o desde el
comando `/schedule_saved_event`.

Flujo general:
1️⃣ Recuperar datos del evento desde `EventWizardSession` o base de datos.
2️⃣ Crear una sesión temporal (`SchedulerWizardSession`).
3️⃣ Determinar el punto de inicio (nombre, zona horaria o fecha de publicación).
4️⃣ Cargar el primer paso correspondiente.
"""

import discord
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.scheduler_wizard.utils.scheduler_session import SchedulerWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL: iniciar el Scheduler Wizard
# --------------------------------------------------------
async def start_scheduler_for_current_event(interaction: discord.Interaction):
    """
    Inicia el flujo de programación del evento actual.
    Se llama desde:
      - `events_wizard.steps.step_finalize.ScheduleButton`
      - Comando `/schedule_saved_event`
    """
    user_id = interaction.user.id
    event_data = EventWizardSession.get(user_id)

    if not event_data:
        await interaction.response.send_message(
            "⚠️ No se encontró un evento activo para programar.",
            ephemeral=True,
        )
        return

    # 🧠 Crear o reiniciar la sesión del scheduler
    SchedulerWizardSession.start(user_id, event_data)
    print(f"[SCHEDULER] Sesión iniciada para user_id={user_id}")

    # --------------------------------------------------------
    # 🔍 Determinar primer paso del flujo
    # --------------------------------------------------------
    title = event_data.get("title")
    timezone = event_data.get("timezone")

    if not title:
        await _redirect_to_step_name(interaction)
        return

    if not timezone:
        await _redirect_to_step_timezone(interaction)
        return

    # Si todo está definido → iniciar en el paso de publicación
    await _redirect_to_step_publish_date(interaction)


# --------------------------------------------------------
# 🔹 FUNCIONES AUXILIARES DE REDIRECCIÓN
# --------------------------------------------------------
async def _redirect_to_step_name(interaction: discord.Interaction):
    """Redirige al paso de definición de nombre."""
    from src.cogs.scheduler_wizard.steps.step_name import show_step

    await interaction.response.send_message(
        f"{event_step_header(1, 'Definir nombre del evento')}\n"
        "Por favor, indica o confirma el nombre del evento antes de continuar.",
        ephemeral=True,
    )
    await show_step(interaction)


async def _redirect_to_step_timezone(interaction: discord.Interaction):
    """Redirige al paso de selección de zona horaria."""
    from src.cogs.scheduler_wizard.steps.step_timezone import show_step

    await interaction.response.send_message(
        f"{event_step_header(2, 'Seleccionar zona horaria')}\n"
        "Selecciona la zona horaria que se usará para la programación del evento.",
        ephemeral=True,
    )
    await show_step(interaction)


async def _redirect_to_step_publish_date(interaction: discord.Interaction):
    """Redirige al paso de fecha/hora de publicación."""
    from src.cogs.scheduler_wizard.steps.step_publish_date import show_step

    await interaction.response.send_message(
        f"{event_step_header(3, 'Definir fecha de publicación')}\n"
        "Ahora configuraremos cuándo se publicará automáticamente este evento.",
        ephemeral=True,
    )
    await show_step(interaction)


# --------------------------------------------------------
# 🔹 MAPA DE PASOS Y NAVEGACIÓN GENERAL
# --------------------------------------------------------
STEP_MAP = {
    1: "name",
    2: "timezone",
    3: "publish_date",
    4: "registration",
    5: "reminders",
    6: "finalize",
}


async def go_to_step(interaction: discord.Interaction, step_number: int):
    """Carga dinámicamente el paso correspondiente del Scheduler Wizard."""
    step_module = STEP_MAP.get(step_number)
    if not step_module:
        await interaction.response.send_message(
            f"⚠️ Paso {step_number} no definido en el flujo del scheduler.",
            ephemeral=True,
        )
        return

    try:
        module_path = f"src.cogs.scheduler_wizard.steps.step_{step_module}"
        module = __import__(module_path, fromlist=["show_step"])
        await module.show_step(interaction)
    except Exception as e:
        print(f"[ERROR] Error al cargar el paso {step_number}: {e}")
        await interaction.response.send_message(
            f"❌ Error al intentar cargar el paso {step_number}: `{e}`",
            ephemeral=True,
        )
