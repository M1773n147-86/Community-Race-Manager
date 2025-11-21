from database.db import Database
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


async def main():
    db = await Database.get_instance()
    await db.init_db()

    print("\n🧪 [TRACK_DB TEST] Insertando circuito...")
    track_id = await db.tracks.add_track(1, "Spa-Francorchamps", "GP", 30, 5, "Circuito belga emblemático", None)
    print(f"✅ Circuito insertado con ID {track_id}")

    print("\n📋 Listado de circuitos:")
    tracks = await db.tracks.list_tracks()
    for t in tracks:
        print(f"  - {t['id']} | {t['name']} ({t['layout']})")

    print("\n🗑️ Eliminando circuito...")
    await db.tracks.delete_track(track_id)
    print("✅ Circuito eliminado correctamente.")

    print("\n✅ Prueba de TRACK_DB completada.")


if __name__ == "__main__":
    asyncio.run(main())
