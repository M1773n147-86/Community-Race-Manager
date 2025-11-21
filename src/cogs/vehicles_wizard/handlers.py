"""
Archivo: handlers.py
Ubicación: src/cogs/vehicles_wizard/

Descripción:
Gestiona las operaciones CRUD (crear, leer, actualizar, eliminar) 
para las listas de vehículos del sistema Community Race Manager.

Funciones principales:
- create_list(name, description, created_by)
- add_vehicle(list_id, model_name)
- get_vehicle_lists(guild_id)
- get_vehicles_in_list(list_id)
- delete_list(list_id)
"""

from database.db import Database
from datetime import datetime


# ==========================================================
# 🚗 VEHICLE LISTS HANDLER
# ==========================================================
async def create_list(name: str, description: str, created_by: int):
    """Crea una nueva lista de vehículos."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    await conn.execute("""
        INSERT INTO vehicle_lists (name, description, created_by, created_at)
        VALUES (?, ?, ?, ?)
    """, (name.strip(), description.strip() if description else None, created_by, datetime.utcnow().isoformat()))
    await conn.commit()

    print(f"[DB] Nueva lista de vehículos creada: {name}")


async def add_vehicle(list_id: int, model_name: str):
    """Agrega un vehículo a una lista existente."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    await conn.execute("""
        INSERT INTO vehicle_list_items (list_id, model_name)
        VALUES (?, ?)
    """, (list_id, model_name.strip()))
    await conn.commit()

    print(f"[DB] Vehículo '{model_name}' agregado a la lista ID {list_id}")


async def get_vehicle_lists(guild_id: int = None):
    """Obtiene todas las listas de vehículos (por servidor o globales)."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    query = "SELECT id, name, description, created_by, created_at FROM vehicle_lists"
    params = []
    if guild_id:
        query += " WHERE created_by = ?"
        params.append(guild_id)

    cur = await conn.execute(query, params)
    rows = await cur.fetchall()
    return [{"id": r[0], "name": r[1], "description": r[2], "created_by": r[3], "created_at": r[4]} for r in rows]


async def get_vehicles_in_list(list_id: int):
    """Devuelve los modelos de coche asociados a una lista."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    cur = await conn.execute("""
        SELECT model_name FROM vehicle_list_items WHERE list_id = ?
    """, (list_id,))
    rows = await cur.fetchall()
    return [r[0] for r in rows]


async def delete_list(list_id: int):
    """Elimina una lista de vehículos y sus elementos asociados."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    await conn.execute("DELETE FROM vehicle_lists WHERE id = ?", (list_id,))
    await conn.commit()
    print(f"[DB] Lista de vehículos eliminada: ID {list_id}")
