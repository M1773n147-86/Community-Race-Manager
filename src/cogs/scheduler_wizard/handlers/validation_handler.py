"""
Archivo: validation_handler.py
Ubicación: src/cogs/scheduler_wizard/handlers/

Descripción:
Proporciona funciones de validación centralizadas para el Scheduler Wizard.
Verifica la coherencia y validez de los datos de programación de eventos antes
de permitir su guardado o publicación.

Incluye:
- Validación de nombre de evento (unicidad y longitud)
- Validación de zonas horarias (compatibles con ZoneInfo)
- Validación de fechas (orden cronológico y posterioridad)
- Validación de recordatorios automáticos
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Tuple
from database.db import Database


class SchedulerValidation:
    """Validador estático para el Scheduler Wizard."""

    # --------------------------------------------------------
    # 🏷️ Validación de nombre de evento
    # --------------------------------------------------------
    @staticmethod
    async def validate_event_name(guild_id: int, title: str) -> Tuple[bool, str]:
        """
        Verifica que el título del evento sea válido y no duplicado
        dentro del mismo servidor (guild_id). La comparación es case-insensitive.
        """
        if not title or len(title.strip()) < 3:
            return False, "❌ El título del evento es demasiado corto o está vacío."

        db = await Database.get_instance()
        conn = await db.get_connection()
        cur = await conn.execute(
            "SELECT COUNT(*) FROM events WHERE LOWER(title) = LOWER(?) AND guild_id = ?",
            (title.strip(), guild_id)
        )
        count = (await cur.fetchone())[0]
        await cur.close()

        if count > 0:
            return False, f"⚠️ Ya existe un evento con el nombre **{title.strip()}** en este servidor."

        return True, ""

    # --------------------------------------------------------
    # 🌍 Validación de zona horaria
    # --------------------------------------------------------
    @staticmethod
    def validate_timezone(tz_str: str) -> Tuple[bool, str]:
        """Comprueba que el identificador de zona horaria sea válido."""
        try:
            ZoneInfo(tz_str)
            return True, ""
        except Exception:
            return False, f"❌ Zona horaria inválida: `{tz_str}`"

    # --------------------------------------------------------
    # 🕓 Validación de fechas y horas
    # --------------------------------------------------------
    @staticmethod
    def validate_datetimes(publish_dt: datetime, registration_dt: datetime) -> List[str]:
        """
        Valida la coherencia de las fechas:
        - Deben ser futuras.
        - La apertura de inscripciones no puede ser posterior a la publicación.
        """
        errors = []
        now = datetime.now(timezone.utc)

        if publish_dt < now:
            errors.append("⚠️ La fecha de publicación debe ser futura.")

        if registration_dt and registration_dt < now:
            errors.append(
                "⚠️ La fecha de apertura de inscripciones debe ser futura.")

        if registration_dt and registration_dt > publish_dt:
            errors.append(
                "❌ La apertura de inscripciones no puede ser posterior a la publicación del evento.")

        return errors

    # --------------------------------------------------------
    # 🔔 Validación de recordatorios automáticos
    # --------------------------------------------------------
    @staticmethod
    def validate_reminders(reminders: List[int]) -> List[str]:
        """
        Verifica que los recordatorios sean positivos y razonables (≤ 72 h antes del evento).
        """
        errors = []
        for r in reminders:
            if r <= 0:
                errors.append(
                    f"⚠️ Recordatorio inválido: {r} minutos (debe ser positivo).")
            elif r > 4320:  # 72 horas = 4320 minutos
                errors.append(
                    f"⚠️ Recordatorio demasiado anticipado: {r} minutos (máximo 72 h).")
        return errors

    # --------------------------------------------------------
    # 🧩 Validación general completa
    # --------------------------------------------------------
    @staticmethod
    async def validate_all(guild_id: int, session_data: Dict[str, Any]) -> List[str]:
        """
        Ejecuta todas las validaciones en conjunto y devuelve
        una lista con todos los errores encontrados.
        """
        errors = []

        # 1️⃣ Nombre del evento
        title = session_data.get("title")
        ok, msg = await SchedulerValidation.validate_event_name(guild_id, title)
        if not ok:
            errors.append(msg)

        # 2️⃣ Zona horaria
        tz = session_data.get("timezone")
        if tz:
            ok, msg = SchedulerValidation.validate_timezone(tz)
            if not ok:
                errors.append(msg)
        else:
            errors.append("⚠️ No se ha definido zona horaria para el evento.")

        # 3️⃣ Fechas
        publish_str = session_data.get("publish_datetime_utc")
        registration_str = session_data.get("registration_open_utc")

        if publish_str:
            try:
                publish_dt = datetime.fromisoformat(publish_str)
                registration_dt = (
                    datetime.fromisoformat(registration_str)
                    if registration_str else None
                )
                errors.extend(SchedulerValidation.validate_datetimes(
                    publish_dt, registration_dt))
            except Exception:
                errors.append(
                    "❌ Error al interpretar las fechas. Formato ISO esperado.")
        else:
            errors.append(
                "⚠️ No se ha definido fecha de publicación del evento.")

        # 4️⃣ Recordatorios
        reminders = session_data.get("reminders", [])
        if reminders:
            errors.extend(SchedulerValidation.validate_reminders(reminders))

        return errors
