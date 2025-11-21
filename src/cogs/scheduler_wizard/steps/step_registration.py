"""
Archivo: step_registration.py
Ubicación: src/cogs/scheduler_wizard/steps/

Descripción:
Define el Paso 3 del asistente de programación de eventos (Scheduler Wizard).
Permite configurar la apertura (y cierre opcional) de inscripciones de pilotos o equipos,
ya sea de forma inmediata o programada. Gestiona validaciones horarias y persistencia
en la sesión temporal del usuario.
"""

import discord
from discord import ui, Interaction, SelectOption
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.cogs.scheduler_wizard.handlers.validation_handler import SchedulerValidation
from src.cogs.scheduler_wizard.handlers.scheduler_handler import SchedulerWizardSession, go_to_step
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView
from src.cogs.events_wizard.utils.helpers import event_step_header


# --------------------------------------------------------
# 🔹 VISTA PRINCIPAL — Modo de apertura de inscripciones
# --------------------------------------------------------
class RegistrationModeView(ui.View):
    """Vista de selección del modo de apertura de inscripciones."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(RegistrationModeSelect(user_id))


class RegistrationModeSelect(ui.Select):
    """Selector del tipo de apertura de inscripciones."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            SelectOption(label="🟢 Abrir inmediatamente", value="instant"),
            SelectOption(label="🗓️ Programar apertura manual",
                         value="scheduled"),
        ]
        super().__init__(
            placeholder="Selecciona el modo de apertura de inscripciones", options=options)

    async def callback(self, interaction: Interaction):
        mode = self.values[0]
        if mode == "instant":
            now_utc = datetime.now(ZoneInfo("UTC"))
            SchedulerWizardSession.update(
                self.user_id, "registration_open_mode", "instant")
            SchedulerWizardSession.update(
                self.user_id, "registration_open_datetime_utc", now_utc.isoformat())

            await interaction.response.send_message(
                "✅ Las inscripciones se abrirán inmediatamente tras la publicación del evento.",
                ephemeral=True
            )

            # Avanzar directamente al paso siguiente (recordatorios)
            await go_to_step(interaction, 4)

        else:
            modal = RegistrationDatetimeModal(self.user_id)
            await interaction.response.send_modal(modal)


# --------------------------------------------------------
# 🔹 MODAL — Definir fecha/hora manualmente
# --------------------------------------------------------
class RegistrationDatetimeModal(ui.Modal, title="🗓️ Programar apertura de inscripciones"):
    """Solicita la fecha y hora local de apertura de inscripciones."""

    open_datetime = ui.TextInput(
        label="Fecha y hora de apertura (AAAA-MM-DD HH:MM)",
        placeholder="Ejemplo: 2025-11-10 20:00",
        required=True,
    )
    close_datetime = ui.TextInput(
        label="Fecha y hora de cierre (opcional)",
        placeholder="Ejemplo: 2025-11-14 23:00",
        required=False,
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        data = SchedulerWizardSession.get(self.user_id)
        tz_name = data.get("timezone", "UTC")

        try:
            if not SchedulerValidation.validate_timezone(tz_name):
                tz_name = "UTC"
            tz = ZoneInfo(tz_name)

            open_dt_local = datetime.strptime(
                self.open_datetime.value.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            open_dt_utc = open_dt_local.astimezone(ZoneInfo("UTC"))

            # Validación: no en el pasado
            if open_dt_utc < datetime.now(ZoneInfo("UTC")):
                await interaction.response.send_message(
                    "⚠️ No puedes establecer una fecha de apertura en el pasado.",
                    ephemeral=True
                )
                return

            # Validación: cierre posterior a apertura (si aplica)
            close_value = self.close_datetime.value.strip()
            close_dt_utc = None
            if close_value:
                close_dt_local = datetime.strptime(
                    close_value, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
                close_dt_utc = close_dt_local.astimezone(ZoneInfo("UTC"))

                if close_dt_utc <= open_dt_utc + timedelta(minutes=10):
                    await interaction.response.send_message(
                        "⚠️ El cierre debe ser al menos 10 minutos posterior a la apertura.",
                        ephemeral=True
                    )
                    return

            # Guardar datos en sesión
            SchedulerWizardSession.update(
                self.user_id, "registration_open_mode", "scheduled")
            SchedulerWizardSession.update(
                self.user_id, "registration_open_datetime_utc", open_dt_utc.isoformat())
            if close_dt_utc:
                SchedulerWizardSession.update(
                    self.user_id, "registration_close_datetime_utc", close_dt_utc.isoformat())

            # Mensaje de confirmación
            msg = (
                f"✅ Inscripciones programadas correctamente.\n"
                f"📅 **Apertura:** {open_dt_local.strftime('%Y-%m-%d %H:%M')} ({tz_name})\n"
            )
            if close_dt_utc:
                msg += f"📅 **Cierre:** {close_dt_local.strftime('%Y-%m-%d %H:%M')} ({tz_name})\n"
            msg += f"🌐 (UTC: {open_dt_utc.strftime('%Y-%m-%d %H:%M')})"

            await interaction.response.send_message(msg, ephemeral=True)

            # Avanzar al siguiente paso
            await go_to_step(interaction, 4)

        except ValueError:
            await interaction.response.send_message(
                "⚠️ Formato incorrecto. Usa `AAAA-MM-DD HH:MM`.",
                ephemeral=True
            )


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL — Mostrar paso 3
# --------------------------------------------------------
async def show_step(interaction: Interaction):
    """Lanza el paso 3 — Configurar apertura de inscripciones."""
    user_id = interaction.user.id
    view = RegistrationModeView(user_id)

    await interaction.followup.send(
        f"{event_step_header(3, 'Apertura de inscripciones')}\n"
        "Define cuándo se abrirán las inscripciones al público. "
        "Puedes abrirlas inmediatamente o programar una fecha específica.",
        view=view,
        ephemeral=True
    )

    # Controles universales del wizard
    nav = WizardNavigationView(user_id, current_step=3, total_steps=5)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para avanzar o retroceder.",
        view=nav,
        ephemeral=True
    )
