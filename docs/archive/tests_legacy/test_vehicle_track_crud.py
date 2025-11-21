import pytest
import asyncio
import aiosqlite
from database.db import Database


# --------------------------------------------------------
# FIXTURES
# --------------------------------------------------------
@pytest.fixture(scope="module")
def event_loop():
    """Permite ejecutar asyncio en pytest."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_temp_db(monkeypatch):
    """Crea una base temporal en memoria antes de cada test."""
    db = await aiosqlite.connect(":memory:")

    await db.executescript("""
    CREATE TABLE vehicle_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        created_by INTEGER
    );

    CREATE TABLE vehicle_list_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER,
        model_name TEXT
    );

    CREATE TABLE track_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT
    );

    CREATE TABLE track_list_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER,
        track_name TEXT
    );
    """)
    await db.commit()

    async def get_conn_override(self):
        return db

    # Sustituye el método del singleton para usar DB temporal
    monkeypatch.setattr(Database, "get_connection", get_conn_override)
    yield db
    await db.close()


# --------------------------------------------------------
# TEST VEHICLE LIST CRUD
# --------------------------------------------------------
@pytest.mark.asyncio
async def test_vehicle_list_crud(setup_temp_db):
    """Prueba la creación, actualización y eliminación de listas de vehículos."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    # Crear lista
    await conn.execute(
        "INSERT INTO vehicle_lists (name, description, created_by) VALUES (?, ?, ?)",
        ("GT3 Europe", "Lista de coches GT3", 1234)
    )
    list_id = (await conn.execute("SELECT id FROM vehicle_lists WHERE name = 'GT3 Europe'")).fetchone()
    await conn.commit()

    # Insertar coches
    cars = ["Ferrari 488 GT3", "Porsche 911 GT3 R",
            "Lamborghini Huracán GT3 Evo2"]
    for c in cars:
        await conn.execute("INSERT INTO vehicle_list_items (list_id, model_name) VALUES (?, ?)", (1, c))
    await conn.commit()

    # Validar inserción
    cur = await conn.execute("SELECT COUNT(*) FROM vehicle_list_items WHERE list_id = 1")
    count = (await cur.fetchone())[0]
    assert count == len(cars)

    # Actualizar lista
    await conn.execute("UPDATE vehicle_lists SET name = ? WHERE id = 1", ("GT3 2025",))
    await conn.commit()
    cur = await conn.execute("SELECT name FROM vehicle_lists WHERE id = 1")
    updated_name = (await cur.fetchone())[0]
    assert updated_name == "GT3 2025"

    # Eliminar lista
    await conn.execute("DELETE FROM vehicle_list_items WHERE list_id = 1")
    await conn.execute("DELETE FROM vehicle_lists WHERE id = 1")
    await conn.commit()
    cur = await conn.execute("SELECT COUNT(*) FROM vehicle_lists")
    assert (await cur.fetchone())[0] == 0


# --------------------------------------------------------
# TEST TRACK LIST CRUD (Create, Read, Update, Delete)
# --------------------------------------------------------
@pytest.mark.asyncio
async def test_track_list_crud(setup_temp_db):
    """Prueba la creación, actualización y eliminación de listas de circuitos."""
    db = await Database.get_instance()
    conn = await db.get_connection()

    # Crear lista
    await conn.execute("INSERT INTO track_lists (name, description) VALUES (?, ?)", ("Clásicos F1", "Circuitos icónicos"))
    await conn.commit()

    # Insertar circuitos
    tracks = ["Monza", "Spa-Francorchamps", "Silverstone"]
    for t in tracks:
        await conn.execute("INSERT INTO track_list_items (list_id, track_name) VALUES (?, ?)", (1, t))
    await conn.commit()

    # Validar inserción
    cur = await conn.execute("SELECT COUNT(*) FROM track_list_items WHERE list_id = 1")
    count = (await cur.fetchone())[0]
    assert count == len(tracks)

    # Actualizar lista
    await conn.execute("UPDATE track_lists SET name = ? WHERE id = 1", ("Históricos F1",))
    await conn.commit()
    cur = await conn.execute("SELECT name FROM track_lists WHERE id = 1")
    updated_name = (await cur.fetchone())[0]
    assert updated_name == "Históricos F1"

    # Eliminar lista
    await conn.execute("DELETE FROM track_list_items WHERE list_id = 1")
    await conn.execute("DELETE FROM track_lists WHERE id = 1")
    await conn.commit()
    cur = await conn.execute("SELECT COUNT(*) FROM track_lists")
    assert (await cur.fetchone())[0] == 0
