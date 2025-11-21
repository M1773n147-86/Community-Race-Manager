"""
Archivo: track_db.py
Ubicación: src/database/

Descripción:
Implementa la capa de acceso a datos (CRUD) para la tabla `tracks`, 
utilizada por el módulo `tracks_wizard` y el `events_wizard` al seleccionar circuitos.

Funciones principales:
- add_track(data): inserta un nuevo circuito.
- get_track(track_id): devuelve los datos de un circuito por ID.
- list_tracks(guild_id): lista circuitos por servidor o globalmente.
- update_track(track_id, fields): actualiza campos específicos.
- delete_track(track_id): elimina un circuito.
- get_or_create_track(name, layout, guild_id): busca o crea uno nuevo automáticamente.

Campos gestionados:
    id, guild_id, name, layout, pit_slots, broadcast_slots,
    details, image_path, created_at
"""

import aiosqlite
from datetime import datetime
from typing import Any, Dict, List, Optional
from database.db import Database


class TrackDB:
    """Capa de persistencia para la tabla `tracks`."""

    def __init__(self, db: Database):
        self.db = db

    # ---------------------------------------------------------
    # 🧩 Helper interno
    # ---------------------------------------------------------
    async def _conn(self) -> aiosqlite.Connection:
        return await self.db.get_connection()

    @staticmethod
    def _dict_from_row(cursor, row) -> Dict[str, Any]:
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    # ---------------------------------------------------------
    # 🟢 CREATE
    # ---------------------------------------------------------
    async def add_track(self, data: Dict[str, Any]) -> int:
        """
        Inserta un nuevo circuito en la base de datos.
        Requiere: guild_id, name, pit_slots.
        """
        required = ("guild_id", "name", "pit_slots")
        for key in required:
            if key not in data:
                raise ValueError(f"Falta campo obligatorio: {key}")

        data.setdefault("broadcast_slots", 0)
        data.setdefault("created_at", datetime.utcnow().isoformat())

        # Evitar duplicados (por nombre y layout dentro del mismo guild)
        conn = await self._conn()
        cur = await conn.execute("""
            SELECT id FROM tracks
            WHERE LOWER(name) = LOWER(?) AND IFNULL(layout,'') = IFNULL(?, '')
              AND guild_id = ?;
        """, (data["name"], data.get("layout", ""), data["guild_id"]))
        existing = await cur.fetchone()
        if existing:
            raise ValueError(
                "Ya existe un circuito con este nombre y diseño en este servidor.")

        cols = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        query = f"INSERT INTO tracks ({cols}) VALUES ({placeholders})"

        await conn.execute(query, data)
        await conn.commit()

        cur = await conn.execute("SELECT last_insert_rowid()")
        new_id = (await cur.fetchone())[0]
        print(f"🏁 Circuito creado: {data.get('name')} (ID={new_id})")
        return new_id

    # ---------------------------------------------------------
    # 📖 READ
    # ---------------------------------------------------------
    async def get_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        conn = await self._conn()
        cur = await conn.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
        row = await cur.fetchone()
        return self._dict_from_row(cur, row) if row else None

    async def list_tracks(self, guild_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Devuelve todos los circuitos registrados (opcionalmente filtrados por servidor)."""
        conn = await self._conn()
        query = "SELECT * FROM tracks"
        params: list[Any] = []
        if guild_id:
            query += " WHERE guild_id = ?"
            params.append(guild_id)
        query += " ORDER BY name ASC"

        cur = await conn.execute(query, params)
        rows = await cur.fetchall()
        return [self._dict_from_row(cur, r) for r in rows] if rows else []

    # ---------------------------------------------------------
    # ✏️ UPDATE
    # ---------------------------------------------------------
    async def update_track(self, track_id: int, fields: Dict[str, Any]) -> bool:
        if not fields:
            return False

        sets = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [track_id]

        conn = await self._conn()
        cur = await conn.execute(f"UPDATE tracks SET {sets} WHERE id = ?", values)
        await conn.commit()
        return cur.rowcount > 0

    # ---------------------------------------------------------
    # ❌ DELETE
    # ---------------------------------------------------------
    async def delete_track(self, track_id: int) -> bool:
        conn = await self._conn()
        cur = await conn.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
        await conn.commit()
        return cur.rowcount > 0

    # ---------------------------------------------------------
    # 🔍 GET OR CREATE
    # ---------------------------------------------------------
    async def get_or_create_track(self, guild_id: int, name: str, layout: str = "", **extra) -> int:
        """
        Devuelve el ID del circuito si existe; de lo contrario lo crea.
        """
        conn = await self._conn()
        cur = await conn.execute("""
            SELECT id FROM tracks
            WHERE LOWER(name) = LOWER(?) AND IFNULL(layout,'') = IFNULL(?, '')
              AND guild_id = ?;
        """, (name, layout, guild_id))
        row = await cur.fetchone()
        if row:
            return row[0]

        data = {
            "guild_id": guild_id,
            "name": name,
            "layout": layout,
            "pit_slots": extra.get("pit_slots", 24),
            "broadcast_slots": extra.get("broadcast_slots", 0),
            "details": extra.get("details", None),
            "image_path": extra.get("image_path", None),
            "created_at": datetime.utcnow().isoformat(),
        }
        return await self.add_track(data)
