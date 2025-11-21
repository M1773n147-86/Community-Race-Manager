from database.db import Database
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


async def main():
    db = await Database.get_instance()
    await db.init_db()

    print("\n🧪 [EVENT_DB TEST] Insertando evento...")
    sample = {
        "guild_id": 1,
        "title": "Evento Test CRUD",
        "description": "Evento creado para prueba de CRUD",
        "is_championship": 0,
        "created_by": 123456789,
        "created_at": "2025-10-31T17:00:00Z"
    }

    eid = await db.events.insert_event(sample)
    print(f"✅ Insertado con ID: {eid}")

    print("\n📋 Eventos en la base de datos:")
    events = await db.events.list_events()
    for e in events:
        print(f"  - {e['event_id']} | {e['title']}")

    print("\n✏️ Actualizando evento...")
    await db.events.update_event(eid, {"title": "Evento Actualizado"})
    updated = await db.events.get_event(eid)
    print(f"✅ Nuevo título: {updated['title']}")

    print("\n🗑️ Eliminando evento...")
    await db.events.delete_event(eid)
    final = await db.events.list_events()
    print(f"📉 Total eventos después de eliminar: {len(final)}")

    print("\n✅ Prueba de EVENT_DB completada.")


if __name__ == "__main__":
    asyncio.run(main())
