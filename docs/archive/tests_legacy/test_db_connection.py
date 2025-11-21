from database.db import Database
import sys
import os
import asyncio
import json

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


async def main():
    print("🔍 Iniciando prueba de conexión a la base de datos...\n")

    db = await Database.get_instance()
    await db.init_db()
    print("✅ Tablas principales inicializadas correctamente.\n")

    conn = await db.get_connection()
    async with conn.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
        tables = await cursor.fetchall()
        print("📋 Tablas encontradas en la base de datos:")
        for t in tables:
            print(f"   - {t[0]}")
    print()

    sample_event = {
        "guild_id": 123456789,
        "title": "Evento de Prueba",
        "description": "Carrera de prueba para verificar la DB",
        "track_id": None,                  # FK opcional
        "is_championship": 0,              # 0 = evento suelto
        "championship_id": None,           # sin campeonato asociado
        "is_published": 0,                 # 0 = borrador
        "max_drivers": 24,
        "broadcast_slots": 2,
        "timezone": "Europe/Madrid",
        "event_datetime_utc": "2025-11-01T18:00:00Z",
        "registration_open_utc": "2025-10-31T12:00:00Z",
        "registration_close_utc": "2025-11-01T12:00:00Z",
        "allow_custom_skins": 1,
        "rules_text": "Seguir las normas de comportamiento en pista",
        "rules_attachment_url": None,
        "publish_channel_id": 987654321,
        "participants_channel_id": 987654322,
        "created_by": 111111111111111111,
        "created_at": "2025-10-31T17:00:00Z",
        "status": "draft"
    }

    print("🧪 Insertando evento de prueba...")
    event_id = await db.events.insert_event(sample_event)
    if event_id != -1:
        print(f"✅ Evento insertado correctamente con ID: {event_id}")
    else:
        print("❌ Error al insertar el evento de prueba")

    print("\n🧩 Listado de eventos en la base de datos:")
    events = await db.events.list_events()
    for ev in events:
        print(f" - {ev['title']} ({ev['status']})")

    await conn.close()
    print("\n✅ Conexión cerrada correctamente.")


if __name__ == "__main__":
    asyncio.run(main())
