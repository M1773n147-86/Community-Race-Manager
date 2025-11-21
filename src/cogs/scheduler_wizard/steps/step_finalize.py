"""
Archivo: step_finalize.py
Ubicación: src/cogs/scheduler_wizard/steps/

Descripción:
Define el Paso 5 del asistente de programación de eventos (Scheduler Wizard).
Reúne todos los datos configurados durante el proceso (nombre, fechas,
recordatorios, etc.) y permite al usuario confirmar la programación final.
El evento quedará con estado 'scheduled' en la base de datos, y se marcará
para publicación y notificaciones automáticas.
"""

import discord
from discord import ui, Interaction, Embed, ButtonStyle
from datetime import datetime, timezone
from src.cogs.scheduler_wizard.handlers.scheduler_handler import SchedulerWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView
from database.db import Database


# --------------------------------------------------------
# 🔹 VISTA PRINCIPAL — Confirmación final
# --------------------------------------------------------
class SchedulerFinalizeView(ui.View):
    """Vista principal del paso final — confirmación y guardado."""

    def __init__(self, user_id: int, event_data: dict):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.event_data = event_data

        self.add_item(ConfirmScheduleButton())
        self.add_item(CancelScheduleButton())


# --------------------------------------------------------
# 🟢 CONFIRMAR PROGRAMACIÓN
# --------------------------------------------------------
class ConfirmScheduleButton(ui.Button):
    """Guarda la programación en base de datos y marca el evento como 'scheduled'."""

    def __init__(self):
        super().__init__(label="🟢 Confirmar programación", style=ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        session_data = SchedulerWizardSession.get(user_id)

        if not session_data:
            await interaction.response.send_message(
                "⚠️ No se encontró información del evento actual.",
                ephemeral=True
            )
            return

        try:
            # 1️⃣ Validación completa de datos antes de guardar
            from src.cogs.scheduler_wizard.handlers.validation_handler import SchedulerValidation
            errors = await SchedulerValidation.validate_all(interaction.guild_id, session_data)

            if errors:
                error_text = "\n".join(errors)
                await interaction.response.send_message(
                    f"❌ No se puede programar el evento por los siguientes errores:\n{error_text}",
                    ephemeral=True
                )
                print(f"[SCHEDULER] Validación fallida:\n{error_text}")
                return

            # 2️⃣ Si todo es válido, proceder al guardado
            db = await Database.get_instance()
            conn = await db.get_connection()
            now = datetime.now(timezone.utc)

            session_data.update({
                "status": "scheduled",
                "is_published": 0,
                "scheduled_at": now.isoformat(),
                "last_edited_by": interaction.user.id,
                "last_edited_date": now.isoformat(),
                "guild_id": interaction.guild_id,
                "created_by": interaction.user.id,
            })

            await db.events.insert_event(session_data)
            SchedulerWizardSession.end(user_id)

            await interaction.response.send_message(
                "✅ El evento ha sido programado correctamente y quedará pendiente de publicación automática.",
                ephemeral=True
            )

            print(
                f"[SCHEDULER] Evento '{session_data.get('title')}' programado correctamente.")

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error al guardar la programación: `{e}`",
                ephemeral=True
            )
            print(f"[ERROR] Fallo al guardar programación: {e}")

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error al guardar la programación: `{e}`",
                ephemeral=True
            )
            print(f"[ERROR] Fallo al guardar programación: {e}")


# --------------------------------------------------------
# ❌ CANCELAR PROGRAMACIÓN
# --------------------------------------------------------
class CancelScheduleButton(ui.Button):
    """Cancela el proceso de programación y elimina la sesión temporal."""

    def __init__(self):
        super().__init__(label="❌ Cancelar programación", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        SchedulerWizardSession.end(interaction.user.id)
        await interaction.response.send_message(
            "🛑 Se canceló la programación del evento. No se guardaron cambios.",
            ephemeral=True
        )
        print(
            f"[SCHEDULER] Programación cancelada por {interaction.user.name}")


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL — Mostrar paso 5
# --------------------------------------------------------
async def show_step(interaction: Interaction):
    """Lanza el paso 5 — Confirmación final del Scheduler Wizard."""
    user_id = interaction.user.id
    session_data = SchedulerWizardSession.get(user_id)

    if not session_data:
        await interaction.response.send_message(
            "⚠️ No se encontró información del evento actual.",
            ephemeral=True
        )
        return

    title = session_data.get("title", "Sin título")
    tz = session_data.get("timezone", "UTC")
    publish_mode = session_data.get("publish_mode", "scheduled")
    publish_dt = session_data.get("publish_datetime_utc", "N/A")
    registration_dt = session_data.get("registration_open_datetime_utc", "N/A")
    reminders = session_data.get("reminders_list", [])

    embed = Embed(
        title=f"🗓️ Resumen de programación: {title}",
        description="Verifica la información antes de confirmar la programación.",
        color=discord.Color.blurple(),
    )

    embed.add_field(name="📅 Publicación",
                    value=f"{publish_mode.upper()} — {publish_dt}", inline=False)
    embed.add_field(name="🕓 Apertura de inscripciones",
                    value=f"{registration_dt}", inline=False)
    embed.add_field(name="🌍 Zona horaria", value=tz, inline=True)

    if reminders:
        reminders_text = "\n".join(
            [f"• {r.get('label', 'Recordatorio')}" for r in reminders])
        embed.add_field(name="🔔 Recordatorios configurados",
                        value=reminders_text, inline=False)
    else:
        embed.add_field(name="🔔 Recordatorios configurados",
                        value="Sin recordatorios definidos", inline=False)

    embed.set_footer(
        text="Confirma la programación o cancela para revisar los pasos anteriores.")

    await interaction.followup.send(
        f"{event_step_header(5, 'Confirmación final de programación')}\n"
        "Verifica toda la información antes de guardar.",
        embed=embed,
        view=SchedulerFinalizeView(user_id, session_data),
        ephemeral=True,
    )

    # Controles universales
    nav = WizardNavigationView(user_id, current_step=5, total_steps=5)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación si deseas revisar los pasos anteriores.",
        view=nav,
        ephemeral=True
    )
