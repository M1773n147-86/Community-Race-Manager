# src/tests/test_track_lists.py
import pytest
import asyncio
from database.db import Database

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def db():
    db_instance = await Database.get_instance()
    yield db_instance


async def test_create_track_list(db):
    async with await db.get_connection() as conn:
        await conn.execute(
            "INSERT INTO track_lists (name, description) VALUES (?, ?)",
            ("F1 Europeos", "Circuitos de la temporada europea de F1")
        )
        await conn.commit()

        cursor = await conn.execute("SELECT id, name FROM track_lists WHERE name = ?", ("F1 Europeos",))
        result = await cursor.fetchone()
        assert result is not None, "❌ No se insertó el registro en track_lists."


async def test_update_track_list(db):
    async with await db.get_connection() as conn:
        await conn.execute(
            "UPDATE track_lists SET description = ? WHERE name = ?",
            ("Actualización de descripción", "F1 Europeos")
        )
        await conn.commit()

        cursor = await conn.execute("SELECT description FROM track_lists WHERE name = ?", ("F1 Europeos",))
        desc = (await cursor.fetchone())[0]
        assert desc == "Actualización de descripción", "❌ No se actualizó correctamente la descripción."


async def test_delete_track_list(db):
    async with await db.get_connection() as conn:
        await conn.execute("DELETE FROM track_lists WHERE name = ?", ("F1 Europeos",))
        await conn.commit()

        cursor = await conn.execute("SELECT id FROM track_lists WHERE name = ?", ("F1 Europeos",))
        assert (await cursor.fetchone()) is None, "❌ No se eliminó correctamente el registro."
