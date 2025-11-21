from database.db import Database
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


async def main():
    db = await Database.get_instance()
    await db.init_db()

    # Crear un evento de prueba
    event = {
        "guild_id": 1,
        "title": "Evento con Participantes",
        "description": "Evento para probar inscripciones",
        "is_championship": 0,
        "created_by": 123456789,
        "created_at": "2025-10-31T17:00:00Z"
    }
    eid = await db.events.insert_event(event)
    print(f"\n🧩 Evento de prueba creado (ID {eid})")

    print("\n🧪 Registrando participante...")
    await db.events.add_participant(eid, user_id=999999, name="PilotoPrueba", car_model="Ferrari 488 GT3")
    participants = await db.events.list_participants(eid)
    print(f"✅ Participantes actuales: {len(participants)}")

    print("\n🗑️ Eliminando participante y evento...")
    await db.events.remove_participant(eid, user_id=999999)
    await db.events.delete_event(eid)
    print("✅ Limpieza completa realizada.")


if __name__ == "__main__":
    asyncio.run(main())
