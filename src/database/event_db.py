"""
Archivo: event_db.py
Ubicación: src/database/

Descripción:
Este módulo implementa la capa de acceso a datos para la tabla `events`, incluyendo
creación, lectura, actualización y borrado (CRUD), así como la gestión completa de
estados del evento (`draft`, `scheduled`, `active`, `archived`, `closed`) y trazabilidad.

Funciones clave:
- insert_event(data, overwrite=False): inserta un evento o actualiza si overwrite=True.
- get_event(event_id): devuelve un evento por ID.
- list_events(...): lista eventos con filtros por servidor, estado, tipo o rango temporal.
- update_event(event_id, fields): actualiza campos arbitrarios.
- schedule_event(event_id, user_id, publish_dt): programa publicación futura.
- publish_event(event_id, user_id): marca como publicado (`active`).
- archive_event(event_id, user_id): marca como archivado (papelera).
- delete_event(event_id): elimina un evento por ID.

Notas:
- `status` es la fuente de verdad; `is_published` actúa como flag derivado.
- Control de duplicados por (`guild_id`, `title`); usar `overwrite=True` para sobrescribir.
- Auto-root de campeonatos: si `is_championship=1` y no hay `championship_id`, se autoasigna.
- Compatible con Scheduler Wizard (campos `publish_datetime_utc`, `registration_open_utc`, etc.).
"""

import aiosqlite
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from database.db import Database


class EventDB:
    """
    CRUD completo para la tabla 'events' con soporte extendido de estados:
    - draft → evento guardado sin publicar
    - scheduled → programado para publicación futura
    - active → evento publicado (registro abierto)
    - archived → archivado (papelera o backup)
    - closed → evento finalizado manual o automáticamente
    """

    def __init__(self, db: Database):
        self.db = db

    # ---------------------------------------------------------
    # 🧩 HELPERS INTERNOS
    # ---------------------------------------------------------
    @staticmethod
    def _dict_from_row(cursor, row) -> Dict[str, Any]:
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    async def _conn(self) -> aiosqlite.Connection:
        return await self.db.get_connection()

    # ---------------------------------------------------------
    # 🟢 CREATE / INSERT
    # ---------------------------------------------------------
    async def insert_event(self, data: dict, overwrite: bool = False) -> int:
        """
        Inserta un nuevo evento o lo actualiza si existe y overwrite=True.
        Compatible con todos los campos del modelo actualizado.
        """
        conn = await self._conn()

        # 🔎 Comprobar duplicado
        cur = await conn.execute(
            "SELECT event_id FROM events WHERE guild_id = ? AND title = ?",
            (data.get("guild_id"), data.get("title"))
        )
        existing = await cur.fetchone()

        now_iso = datetime.utcnow().isoformat()
        data.setdefault("created_at", now_iso)
        data.setdefault("last_edited_date", now_iso)
        data.setdefault("last_edited_by", data.get("created_by"))

        # Asegurar nuevos campos y defaults
        data.setdefault("event_type", "standard")
        data.setdefault("status", data.get("status", "draft"))
        data.setdefault("publish_datetime_utc", None)
        data.setdefault("registration_open_utc", None)
        data.setdefault("registration_close_utc", None)

        # Si ya existe y se solicita sobreescritura
        if existing and overwrite:
            event_id = existing[0]
            fields = {**data, "last_edited_date": now_iso}
            await self.update_event(event_id, fields)
            print(f"♻️ Evento actualizado: {data.get('title')}")
            return event_id

        # Si existe y no se permite overwrite → error
        if existing and not overwrite:
            raise ValueError(
                "Ya existe un evento con este nombre en este servidor.")

        # Inserción
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        columns = ", ".join(data.keys())
        query = f"INSERT INTO events ({columns}) VALUES ({placeholders})"
        await conn.execute(query, data)
        await conn.commit()

        cur = await conn.execute("SELECT last_insert_rowid()")
        new_id = (await cur.fetchone())[0]
        print(f"🗓️ Nuevo evento insertado: {data.get('title')} (ID={new_id})")

        # Auto-root de campeonatos
        if int(data.get("is_championship", 0)) and not data.get("championship_id"):
            await conn.execute(
                "UPDATE events SET championship_id = ? WHERE event_id = ?",
                (new_id, new_id),
            )
            await conn.commit()

        return new_id

    # ---------------------------------------------------------
    # 📖 READ
    # ---------------------------------------------------------
    async def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        conn = await self._conn()
        cur = await conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = await cur.fetchone()
        return self._dict_from_row(cur, row) if row else None

    async def list_events(
        self,
        guild_id: Optional[int] = None,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        after_date_utc: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve una lista de eventos filtrados opcionalmente por:
        - Servidor (`guild_id`)
        - Estado (`status`)
        - Tipo (`event_type`)
        - Fecha posterior (`after_date_utc`, formato ISO UTC)
        """
        conn = await self._conn()
        query = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []

        if guild_id:
            query += " AND guild_id = ?"
            params.append(guild_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if after_date_utc:
            query += " AND datetime(event_datetime_utc) >= datetime(?)"
            params.append(after_date_utc)

        query += " ORDER BY datetime(event_datetime_utc) ASC"
        cur = await conn.execute(query, params)
        rows = await cur.fetchall()
        return [self._dict_from_row(cur, r) for r in rows] if rows else []

    # ---------------------------------------------------------
    # ✏️ UPDATE
    # ---------------------------------------------------------
    async def update_event(self, event_id: int, fields: Dict[str, Any]) -> bool:
        """Actualiza uno o más campos del evento."""
        if not fields:
            return False

        fields["last_edited_date"] = datetime.utcnow().isoformat()
        sets = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [event_id]

        conn = await self._conn()
        cur = await conn.execute(f"UPDATE events SET {sets} WHERE event_id = ?", values)
        await conn.commit()
        return cur.rowcount > 0

    # ---------------------------------------------------------
    # 🕓 CAMBIOS DE ESTADO
    # ---------------------------------------------------------
    async def schedule_event(self, event_id: int, user_id: int, publish_dt: str):
        """Programa un evento para publicación futura."""
        await self.update_event(event_id, {
            "status": "scheduled",
            "is_published": 0,
            "publish_datetime_utc": publish_dt,
            "last_edited_by": user_id,
        })
        print(f"🕓 Evento {event_id} programado para {publish_dt}")

    async def publish_event(self, event_id: int, user_id: int):
        """Marca el evento como publicado y asigna la fecha actual."""
        now = datetime.utcnow().isoformat()
        await self.update_event(event_id, {
            "status": "active",
            "is_published": 1,
            "published_at": now,
            "last_edited_by": user_id,
        })

    async def archive_event(self, event_id: int, user_id: int):
        """Archiva el evento y define fecha de expiración a 30 días."""
        now = datetime.utcnow()
        expiry = now + timedelta(days=30)
        await self.update_event(event_id, {
            "status": "archived",
            "archived_at": now.isoformat(),
            "archive_expires_at": expiry.isoformat(),
            "last_edited_by": user_id,
        })

    # ---------------------------------------------------------
    # ❌ DELETE
    # ---------------------------------------------------------
    async def delete_event(self, event_id: int) -> bool:
        """Elimina un evento por ID."""
        conn = await self._conn()
        cur = await conn.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
        await conn.commit()
        return cur.rowcount > 0
