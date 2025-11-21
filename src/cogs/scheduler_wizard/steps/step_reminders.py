"""
Archivo: step_reminders.py
Ubicación: src/cogs/scheduler_wizard/steps/

Descripción:
Define el Paso 4 del Scheduler Wizard — configuración de recordatorios automáticos.
Permite definir alertas preconfiguradas (48h, 24h, 3h antes) o personalizadas, que
serán enviadas automáticamente antes del inicio del evento o su publicación.
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
# 🔹 VISTA PRINCIPAL — Selección de recordatorios
# --------------------------------------------------------
class StepRemindersView(ui.View):
    """Vista de selección y configuración de recordatorios automáticos."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(ReminderPresetSelect(self.user_id))
        self.add_item(AddCustomReminderButton(self.user_id))


class ReminderPresetSelect(ui.Select):
    """Selector con intervalos predefinidos para los recordatorios."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            SelectOption(label="📅 48 horas antes", value="48"),
            SelectOption(label="⏰ 24 horas antes", value="24"),
            SelectOption(label="⚡ 3 horas antes", value="3"),
        ]
        super().__init__(
            placeholder="Selecciona recordatorios automáticos",
            options=options,
            min_values=1,
            max_values=len(options)
        )

    async def callback(self, interaction: Interaction):
        user_id = self.user_id
        session_data = SchedulerWizardSession.get(user_id)
        event_time_str = session_data.get("event_datetime_utc")

        if not event_time_str:
            await interaction.response.send_message(
                "⚠️ No se encontró la fecha del evento. Completa el paso de horario antes de configurar recordatorios.",
                ephemeral=True
            )
            return

        event_time = datetime.fromisoformat(event_time_str)
        reminders = []

        for hours in self.values:
            delta = timedelta(hours=int(hours))
            reminder_utc = event_time - delta
            reminders.append({
                "label": f"{hours}h antes",
                "utc": reminder_utc.isoformat()
            })

        SchedulerWizardSession.update(user_id, "reminders_list", reminders)
        SchedulerWizardSession.update(user_id, "reminders_enabled", True)

        await interaction.response.send_message(
            f"✅ Se configuraron recordatorios automáticos: {', '.join([r['label'] for r in reminders])}",
            ephemeral=True
        )

        # Avanzar al paso final (Paso 5)
        await go_to_step(interaction, 5)


# --------------------------------------------------------
# 🔹 BOTÓN — Agregar recordatorio personalizado
# --------------------------------------------------------
class AddCustomReminderButton(ui.Button):
    """Abre el modal para crear un recordatorio manual."""

    def __init__(self, user_id: int):
        super().__init__(label="📝 Añadir recordatorio manual",
                         style=discord.ButtonStyle.primary)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        modal = CustomReminderModal(self.user_id)
        await interaction.response.send_modal(modal)


# --------------------------------------------------------
# 🔹 MODAL — Recordatorio manual personalizado
# --------------------------------------------------------
class CustomReminderModal(ui.Modal, title="🕓 Crear recordatorio manual"):
    """Permite ingresar manualmente la fecha/hora de un recordatorio."""

    reminder_datetime = ui.TextInput(
        label="Fecha y hora local (AAAA-MM-DD HH:MM)",
        placeholder="Ejemplo: 2025-11-12 20:00",
        required=True
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        user_id = self.user_id
        session = SchedulerWizardSession.get(user_id)
        tz_name = session.get("timezone", "UTC")

        try:
            if not SchedulerValidation.validate_timezone(tz_name):
                tz_name = "UTC"

            tz = ZoneInfo(tz_name)
            reminder_local = datetime.strptime(
                self.reminder_datetime.value.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            reminder_utc = reminder_local.astimezone(ZoneInfo("UTC"))

            event_time_str = session.get("event_datetime_utc")
            if not event_time_str:
                await interaction.response.send_message(
                    "⚠️ No se encontró la fecha del evento. Completa el paso anterior antes de configurar recordatorios.",
                    ephemeral=True
                )
                return

            event_time = datetime.fromisoformat(event_time_str)

            # Validación: el recordatorio debe ser anterior al evento
            if reminder_utc >= event_time:
                await interaction.response.send_message(
                    "⚠️ El recordatorio debe programarse antes del evento.",
                    ephemeral=True
                )
                return

            # Obtener lista existente y evitar duplicados
            reminders = session.get("reminders_list", [])
            if len(reminders) >= 3:
                await interaction.response.send_message(
                    "⚠️ Solo puedes configurar hasta 3 recordatorios por evento.",
                    ephemeral=True
                )
                return

            for r in reminders:
                if abs((datetime.fromisoformat(r["utc"]) - reminder_utc).total_seconds()) < 60:
                    await interaction.response.send_message(
                        "⚠️ Ya existe un recordatorio en un horario muy cercano.",
                        ephemeral=True
                    )
                    return

            reminders.append({
                "label": f"Personalizado ({reminder_local.strftime('%Y-%m-%d %H:%M')})",
                "utc": reminder_utc.isoformat(),
                "local": reminder_local.strftime('%Y-%m-%d %H:%M'),
            })

            SchedulerWizardSession.update(user_id, "reminders_list", reminders)
            SchedulerWizardSession.update(user_id, "reminders_enabled", True)

            await interaction.response.send_message(
                f"✅ Recordatorio agregado para {reminder_local.strftime('%Y-%m-%d %H:%M')} ({tz_name})",
                ephemeral=True
            )

            # Avanzar al siguiente paso (final)
            await go_to_step(interaction, 5)

        except ValueError:
            await interaction.response.send_message(
                "⚠️ Formato incorrecto. Usa `AAAA-MM-DD HH:MM`.",
                ephemeral=True
            )


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL — Mostrar paso 4
# --------------------------------------------------------
async def show_step(interaction: Interaction):
    """Lanza el paso 4 — Configuración de recordatorios automáticos."""
    user_id = interaction.user.id
    view = StepRemindersView(user_id)

    await interaction.followup.send(
        f"{event_step_header(4, 'Recordatorios automáticos')}\n"
        "Configura recordatorios que se enviarán antes del evento.\n"
        "Puedes seleccionar intervalos predefinidos o agregar uno manual.",
        view=view,
        ephemeral=True
    )

    nav = WizardNavigationView(user_id, current_step=4, total_steps=5)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para avanzar o retroceder.",
        view=nav,
        ephemeral=True
    )
