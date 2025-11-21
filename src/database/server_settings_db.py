"""
Archivo: server_settings_db.py
Ubicación: src/database/

Descripción:
Maneja la configuración específica de cada servidor (guild),
como prefijos personalizados o zona horaria base. Los datos 
se almacenan en la tabla `servers`, definida en `db.py`.

Este módulo usa la conexión centralizada del Database Singleton.
"""

from typing import Optional
from database.db import Database


class ServerSettingsDB:
    """CRUD para ajustes de servidor usando la tabla `servers`."""

    def __init__(self, db):
        self._db = db

    async def _conn(self):
        """Retorna la conexión centralizada."""
        return await self._db.get_connection()

    # ---------------------------------------------------------
    # 🔹 Prefix
    # ---------------------------------------------------------
    async def get_prefix(self, guild_id: int) -> Optional[str]:
        conn = await self._conn()
        cur = await conn.execute(
            "SELECT prefix FROM servers WHERE guild_id = ?",
            (guild_id,)
        )
        row = await cur.fetchone()
        await cur.close()
        return row[0] if row else None

    async def set_prefix(self, guild_id: int, prefix: str):
        conn = await self._conn()
        await conn.execute(
            """
            INSERT INTO servers (guild_id, prefix)
            VALUES (?, ?)
            ON CONFLICT(guild_id) 
            DO UPDATE SET prefix = excluded.prefix
            """,
            (guild_id, prefix)
        )
        await conn.commit()

    # ---------------------------------------------------------
    # 🔹 Timezone base del servidor
    # ---------------------------------------------------------
    async def get_timezone(self, guild_id: int) -> Optional[str]:
        conn = await self._conn()
        cur = await conn.execute(
            "SELECT timezone FROM servers WHERE guild_id = ?",
            (guild_id,)
        )
        row = await cur.fetchone()
        await cur.close()
        return row[0] if row else None

    async def set_timezone(self, guild_id: int, timezone: str):
        conn = await self._conn()
        await conn.execute(
            """
            INSERT INTO servers (guild_id, timezone)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET timezone = excluded.timezone
            """,
            (guild_id, timezone)
        )
        await conn.commit()
