# src/tests/test_track_list_items.py
import pytest
from database.db import Database

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def db():
    db_instance = await Database.get_instance()
    yield db_instance


async def test_insert_track_list_and_items(db):
    async with await db.get_connection() as conn:
        # Crear lista base
        await conn.execute(
            "INSERT INTO track_lists (name, description) VALUES (?, ?)",
            ("Endurance 2025", "Circuitos de resistencia para 2025")
        )
        await conn.commit()

        # Obtener ID de la lista
        cursor = await conn.execute("SELECT id FROM track_lists WHERE name = ?", ("Endurance 2025",))
        list_id = (await cursor.fetchone())[0]

        # Insertar circuitos asociados
        tracks = ["Spa-Francorchamps", "Le Mans", "Nürburgring"]
        for t in tracks:
            await conn.execute(
                "INSERT INTO track_list_items (list_id, track_name) VALUES (?, ?)",
                (list_id, t)
            )
        await conn.commit()

        # Validar asociación
        cursor = await conn.execute("SELECT track_name FROM track_list_items WHERE list_id = ?", (list_id,))
        results = [r[0] for r in await cursor.fetchall()]
        assert len(results) == len(
            tracks), "❌ No se insertaron todos los circuitos esperados."
        assert set(results) == set(
            tracks), "❌ Los nombres de circuitos no coinciden."


async def test_cleanup_track_list_items(db):
    async with await db.get_connection() as conn:
        await conn.execute("DELETE FROM track_list_items")
        await conn.execute("DELETE FROM track_lists WHERE name = ?", ("Endurance 2025",))
        await conn.commit()

        # Verificar limpieza
        cursor = await conn.execute("SELECT COUNT(*) FROM track_list_items")
        count_items = (await cursor.fetchone())[0]
        assert count_items == 0, "❌ Los track_list_items no se limpiaron correctamente."
