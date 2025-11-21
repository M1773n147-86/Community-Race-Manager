"""
Archivo: handlers.py
Ubicación: src/cogs/tracks_wizard/

Descripción:
Módulo central de gestión de listas de circuitos (CRUD + consultas).
Provee operaciones asíncronas para leer, crear, actualizar y eliminar
listas de circuitos y sus ítems asociados. Compatible con la estructura
de base de datos definida en `database/db.py`.
"""

from src.database.db import Database
from typing import List, Dict, Optional
from datetime import datetime

# ────────────────────────────────────────────────────────────────────────
# LECTURAS
# ────────────────────────────────────────────────────────────────────────


async def get_track_lists(guild_id: Optional[int] = None) -> List[Dict]:
    """
    Obtiene todas las listas de circuitos registradas para un servidor.
    Si guild_id es None, devuelve todas las listas globales (modo compatibilidad).
    """
    db = await Database.get_instance()
    conn = await db.get_connection()

    if guild_id:
        cursor = await conn.execute(
            "SELECT id, name, description FROM track_lists WHERE guild_id = ? ORDER BY name ASC",
            (guild_id,)
        )
    else:
        cursor = await conn.execute(
            "SELECT id, name, description FROM track_lists ORDER BY name ASC"
        )

    rows = await cursor.fetchall()
    await cursor.close()

    return [{"id": r[0], "name": r[1], "description": r[2] or ""} for r in rows]


async def get_tracks_in_list(list_id: int) -> List[str]:
    """
    Obtiene todos los circuitos (track_name) pertenecientes a una lista específica.
    """
    db = await Database.get_instance()
    conn = await db.get_connection()

    cursor = await conn.execute(
        "SELECT track_name FROM track_list_items WHERE list_id = ? ORDER BY id ASC",
        (list_id,)
    )
    rows = await cursor.fetchall()
    await cursor.close()

    return [r[0] for r in rows]


# ────────────────────────────────────────────────────────────────────────
# CREACIÓN / ACTUALIZACIÓN / ELIMINACIÓN
# ────────────────────────────────────────────────────────────────────────

async def create_track_list(guild_id: int, name: str, description: str, created_by: int, items: Optional[List[str]] = None) -> int:
    """
    Crea una nueva lista de circuitos y opcionalmente añade ítems asociados.
    Retorna el ID de la nueva lista.
    """
    db = await Database.get_instance()
    conn = await db.get_connection()

    await conn.execute(
        "INSERT INTO track_lists (guild_id, name, description, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (guild_id, name, description, created_by, datetime.utcnow().isoformat())
    )
    cursor = await conn.execute("SELECT last_insert_rowid()")
    list_id = (await cursor.fetchone())[0]
    await cursor.close()

    if items:
        for t in items:
            await conn.execute(
                "INSERT INTO track_list_items (list_id, track_name) VALUES (?, ?)",
                (list_id, t.strip())
            )

    await conn.commit()
    return list_id


async def update_track_list(list_id: int, name: str, description: str, items: Optional[List[str]] = None):
    """
    Actualiza una lista existente y reemplaza sus ítems si se proporcionan.
    """
    db = await Database.get_instance()
    conn = await db.get_connection()

    await conn.execute(
        "UPDATE track_lists SET name = ?, description = ? WHERE id = ?",
        (name, description, list_id)
    )

    if items is not None:
        await conn.execute("DELETE FROM track_list_items WHERE list_id = ?", (list_id,))
        for t in items:
            await conn.execute(
                "INSERT INTO track_list_items (list_id, track_name) VALUES (?, ?)",
                (list_id, t.strip())
            )

    await conn.commit()


async def delete_track_list(list_id: int):
    """
    Elimina una lista de circuitos y todos sus ítems asociados.
    """
    db = await Database.get_instance()
    conn = await db.get_connection()

    await conn.execute("DELETE FROM track_list_items WHERE list_id = ?", (list_id,))
    await conn.execute("DELETE FROM track_lists WHERE id = ?", (list_id,))
    await conn.commit()
