"""
Archivo: db_init.py
Ubicación: src/database/

Descripción:
Este módulo inicializa la base de datos del Community Race Manager cargando el
esquema definido en `schema.sql`. Permite crear o reconstruir todas las tablas
necesarias (vehículos, circuitos, eventos, permisos, servidores, etc.) y se
utiliza tanto en la primera ejecución del bot como en entornos de desarrollo
para reinicializar la estructura.

Incluye:
- Lectura asíncrona del esquema SQL desde `schema.sql`.
- Ejecución automática de todas las sentencias CREATE TABLE / INDEX.
- Opción de reinicio completo (`full_reset=True`) que elimina el archivo
  `bot.db` antes de reconstruirlo.
- Control de errores y rollback en caso de fallo durante la inicialización.
"""

# ================================================
# DATABASE INITIALIZATION — Community Race Manager
# ================================================
import os
import aiosqlite
from database.db import Database


async def init_database(full_reset: bool = False):
    """
    Inicializa la base de datos completa cargando el esquema SQL desde schema.sql.
    - Si full_reset=True, elimina el archivo bot.db antes de crear las tablas.
    - Compatible con inicialización completa o incremental (según el esquema).
    """

    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "bot.db")
    schema_path = os.path.join(
        os.path.dirname(__file__), "schema.sql")

    if not os.path.exists(schema_path):
        raise FileNotFoundError(
            f"❌ No se encontró el archivo de esquema: {schema_path}")

    if full_reset and os.path.exists(db_path):
        os.remove(db_path)
        print("🧹 Base de datos anterior eliminada (modo reset activado).")

    db = await Database.get_instance()

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        async with await db.get_connection() as conn:
            await conn.executescript(schema_sql)
            await conn.commit()

        print("✅ Base de datos inicializada correctamente con el esquema completo.")
    except aiosqlite.Error as e:
        print(f"❌ Error durante la inicialización de la base de datos: {e}")
        await conn.rollback()
    except Exception as e:
        print(f"⚠️ Error inesperado: {e}")
