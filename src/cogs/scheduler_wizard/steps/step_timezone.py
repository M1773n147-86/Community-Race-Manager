"""
Archivo: step_timezone.py
Ubicación: src/cogs/scheduler_wizard/steps/

Descripción:
Define el paso de configuración de zona horaria y fecha del evento dentro del 
Scheduler Wizard. Permite al usuario seleccionar una región, una zona horaria 
y establecer una fecha y hora local, convirtiéndola automáticamente a UTC para 
su uso en los módulos de programación y publicación de eventos.
"""

import discord
from discord import ui, Interaction, SelectOption
from datetime import datetime
from zoneinfo import ZoneInfo
from src.utils import manager_timezones as tz
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView

# --------------------------------------------------------
# 🔹 Vista principal de selección de zona y fecha
# --------------------------------------------------------


class StepTimezoneView(ui.View):
    """Vista principal: selección de región, zona horaria y fecha/hora."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(RegionSelect(self))

    async def update_timezone_select(self, interaction: Interaction, region: str):
        """Actualiza el selector de zonas horarias según la región elegida."""
        self.clear_items()
        self.add_item(TimezoneSelect(self, region))
        await interaction.response.edit_message(
            content=f"🌍 Selecciona una zona horaria dentro de **{region}**:",
            view=self,
        )


# --------------------------------------------------------
# 🔹 Selector de región
# --------------------------------------------------------
class RegionSelect(ui.Select):
    def __init__(self, parent: StepTimezoneView):
        options = [SelectOption(label=name, value=key)
                   for key, name in tz.REGIONS.items()]
        super().__init__(placeholder="🌎 Selecciona una región", options=options)
        self.view_ref = parent

    async def callback(self, interaction: Interaction):
        await self.view_ref.update_timezone_select(interaction, self.values[0])


# --------------------------------------------------------
# 🔹 Selector de zona horaria
# --------------------------------------------------------
class TimezoneSelect(ui.Select):
    def __init__(self, parent: StepTimezoneView, region: str):
        options = [
            SelectOption(label=f"{offset} – {cities}", value=tzid)
            for offset, cities, tzid in tz.list_timezones_by_region(region)
        ]
        super().__init__(placeholder="🕒 Selecciona zona horaria", options=options)
        self.view_ref = parent

    async def callback(self, interaction: Interaction):
        tz_name = self.values[0]
        EventWizardSession.update(interaction.user.id, "timezone", tz_name)
        await interaction.response.send_modal(EventDateTimeModal(interaction.user.id, tz_name))


# --------------------------------------------------------
# 🔹 Modal: ingresar fecha y hora local
# --------------------------------------------------------
class EventDateTimeModal(ui.Modal, title="🗓️ Fecha y hora del evento"):
    event_datetime = ui.TextInput(
        label="Fecha y hora (AAAA-MM-DD HH:MM)",
        placeholder="Ejemplo: 2025-11-12 21:30",
        style=discord.TextStyle.short,
    )

    def __init__(self, user_id: int, timezone_str: str):
        super().__init__()
        self.user_id = user_id
        self.timezone_str = timezone_str

    async def on_submit(self, interaction: Interaction):
        dt_str = self.event_datetime.value.strip()
        try:
            # Conversión a UTC
            utc_iso = tz.convert_to_utc(dt_str, self.timezone_str)

            # Validación de futuro
            if not tz.validate_future_datetime(utc_iso):
                await interaction.response.send_message(
                    "⚠️ No puedes establecer una fecha en el pasado. Intenta nuevamente.",
                    ephemeral=True,
                )
                return

            # Guardar sesión
            EventWizardSession.update(
                self.user_id, "event_datetime_utc", utc_iso)
            EventWizardSession.update(
                self.user_id, "timezone", self.timezone_str)

            # Confirmar visualmente
            local_zone = ZoneInfo(self.timezone_str)
            local_dt = datetime.strptime(
                dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_zone)
            await interaction.response.send_message(
                f"✅ Fecha configurada correctamente.\n"
                f"🕒 Hora local: **{local_dt.strftime('%Y-%m-%d %H:%M')} ({self.timezone_str})**\n"
                f"🌐 Equivalente UTC: **{datetime.fromisoformat(utc_iso).strftime('%Y-%m-%d %H:%M')} UTC**",
                ephemeral=True,
            )

            # Navegación al siguiente paso del scheduler
            from src.cogs.scheduler_wizard.steps.step_publish_date import show_publish_date_step
            await show_publish_date_step(interaction)

        except ValueError:
            await interaction.response.send_message(
                "⚠️ Formato incorrecto. Usa `AAAA-MM-DD HH:MM`.",
                ephemeral=True,
            )


# --------------------------------------------------------
# 🔹 Función principal del paso
# --------------------------------------------------------
async def show_timezone_step(interaction: Interaction):
    """Lanza el paso de selección de zona horaria."""
    view = StepTimezoneView(interaction.user.id)
    await interaction.followup.send(
        "🕓 Define la **fecha, hora y zona horaria** para el evento.",
        view=view,
        ephemeral=True,
    )

    nav = WizardNavigationView(interaction.user.id, current_step=2)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para avanzar o retroceder.",
        view=nav,
        ephemeral=True,
    )
