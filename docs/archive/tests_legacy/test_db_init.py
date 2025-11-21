# ================================================
# TEST — Database Initialization Integrity Check
# ================================================
import pytest
import asyncio
import aiosqlite
import os

from database.db_init import init_database
from database.db import Database


@pytest.mark.asyncio
async def test_database_initialization(tmp_path):
    """
    Verifica que la base de datos se inicializa correctamente
    y contiene las tablas esperadas después de ejecutar init_database().
    """
    # Crear base de datos temporal
    db_path = tmp_path / "test_bot.db"
    os.environ["DB_PATH"] = str(db_path)

    # Forzar inicialización
    await init_database()

    # Conexión directa a SQLite
    db = await Database.get_instance()
    async with await db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = [row[0] for row in await cursor.fetchall()]

    expected_tables = {
        "vehicle_lists",
        "vehicle_list_items",
        "track_lists",
        "track_list_items"
    }

    missing = expected_tables - set(tables)
    assert not missing, f"Faltan tablas tras inicialización: {missing}"

    print("✅ Todas las tablas esperadas están presentes en la base de datos.")


@pytest.mark.asyncio
async def test_foreign_key_integrity():
    """
    Verifica que las claves foráneas estén activas y configuradas correctamente.
    """
    db = await Database.get_instance()
    async with await db.get_connection() as conn:
        # Foreign keys activas
        cursor = await conn.execute("PRAGMA foreign_keys;")
        result = await cursor.fetchone()
        assert result[0] == 1, "Las claves foráneas no están activadas en la conexión."

        # Validar referencias (ON DELETE CASCADE)
        cursor = await conn.execute("PRAGMA foreign_key_list('track_list_items');")
        fk_info = [row for row in await cursor.fetchall()]
        assert any(
            "track_lists" in row for row in fk_info), "Fallo: no se encontró referencia a track_lists"

    print("✅ Integridad referencial confirmada (foreign keys activas).")
