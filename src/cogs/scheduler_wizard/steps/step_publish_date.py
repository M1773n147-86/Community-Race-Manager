"""
Archivo: step_publish_date.py
Ubicación: src/cogs/scheduler_wizard/steps/

Descripción:
Define el Paso 2 del asistente de programación de eventos (Scheduler Wizard).
El usuario elige si desea publicar el evento de forma inmediata o programar una
fecha y hora específicas. Gestiona validaciones básicas y la conversión horaria a UTC.
"""

import discord
from discord import ui, Interaction, SelectOption
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.cogs.scheduler_wizard.utils.scheduler_session import SchedulerWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView


# --------------------------------------------------------
# 🔹 VISTA PRINCIPAL — Selección del modo de publicación
# --------------------------------------------------------
class SchedulerPublishDateView(ui.View):
    """Vista que permite seleccionar el modo de publicación."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(PublishModeSelect(self.user_id))


class PublishModeSelect(ui.Select):
    """Selector del modo de publicación."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            SelectOption(label="🟢 Publicar ahora", value="instant"),
            SelectOption(label="🗓️ Programar fecha y hora", value="scheduled")
        ]
        super().__init__(placeholder="Selecciona cómo deseas publicar el evento", options=options)

    async def callback(self, interaction: Interaction):
        mode = self.values[0]

        if mode == "instant":
            now_utc = datetime.utcnow().isoformat()
            SchedulerWizardSession.update(
                self.user_id, "publish_mode", "instant")
            SchedulerWizardSession.update(
                self.user_id, "publish_datetime_utc", now_utc)

            await interaction.response.send_message(
                "✅ El evento se publicará **inmediatamente** al finalizar el asistente.",
                ephemeral=True
            )
            return

        # Si selecciona programar fecha/hora, abrir modal
        modal = PublishDatetimeModal(self.user_id)
        await interaction.response.send_modal(modal)


# --------------------------------------------------------
# 🔹 MODAL — Ingreso manual de fecha y hora programada
# --------------------------------------------------------
class PublishDatetimeModal(ui.Modal, title="🗓️ Programar fecha y hora de publicación"):
    """Modal para ingresar fecha y hora de publicación programada."""

    publish_datetime = ui.TextInput(
        label="Fecha y hora local (AAAA-MM-DD HH:MM)",
        placeholder="Ejemplo: 2025-11-15 21:30",
        required=True
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        dt_str = self.publish_datetime.value.strip()
        try:
            # Obtener zona horaria del usuario desde la sesión o usar UTC
            user_data = SchedulerWizardSession.get(self.user_id)
            tz_name = user_data.get("timezone", "UTC")
            local_zone = ZoneInfo(tz_name)

            # Convertir fecha local a UTC
            local_dt = datetime.strptime(
                dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_zone)
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

            # Validaciones
            now_utc = datetime.now(ZoneInfo("UTC"))
            if utc_dt < now_utc + timedelta(minutes=10):
                await interaction.response.send_message(
                    "⚠️ La fecha de publicación debe ser al menos **10 minutos posterior** a la hora actual.",
                    ephemeral=True
                )
                return

            SchedulerWizardSession.update(
                self.user_id, "publish_mode", "scheduled")
            SchedulerWizardSession.update(
                self.user_id, "publish_datetime_utc", utc_dt.isoformat())

            await interaction.response.send_message(
                f"✅ Publicación programada correctamente.\n"
                f"🕒 Hora local: **{local_dt.strftime('%Y-%m-%d %H:%M')} ({tz_name})**\n"
                f"🌐 Equivalente UTC: **{utc_dt.strftime('%Y-%m-%d %H:%M')} UTC**",
                ephemeral=True
            )

        except ValueError:
            await interaction.response.send_message(
                "⚠️ Formato incorrecto. Usa `AAAA-MM-DD HH:MM`.",
                ephemeral=True
            )


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL — Mostrar el paso
# --------------------------------------------------------
async def show_step(interaction: Interaction):
    """Lanza el paso 2 — Selección de modo de publicación."""
    user_id = interaction.user.id

    view = SchedulerPublishDateView(user_id)
    await interaction.followup.send(
        f"{event_step_header(2, 'Modo de publicación del evento')}\n"
        "Decide si deseas **publicar ahora** o **programar el evento** para una fecha específica.",
        view=view,
        ephemeral=True
    )

    # Controles universales del wizard
    view_nav = WizardNavigationView(user_id, current_step=2)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para avanzar o retroceder.",
        view=view_nav,
        ephemeral=True
    )
