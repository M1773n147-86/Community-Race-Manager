import asyncio
from database.db import Database


async def main():
    print("🧪 [VEHICLE_LISTS TEST] Iniciando prueba de gestión de listas de coches...\n")

    db = await Database.get_instance()
    await db.init_db()

    async with await db.get_connection() as conn:
        # --- 1️⃣ Crear lista de prueba ---
        print("➕ Creando lista de prueba...")
        cursor = await conn.execute(
            "INSERT INTO vehicle_lists (name, description, created_by) VALUES (?, ?, ?)",
            ("GT3 Europe 2025", "Lista de coches GT3 para eventos europeos", 123456789)
        )
        list_id = cursor.lastrowid

        # --- 2️⃣ Agregar coches a la lista ---
        cars = ["Ferrari 488 GT3", "Porsche 911 GT3 R", "BMW M4 GT3"]
        for car in cars:
            await conn.execute(
                "INSERT INTO vehicle_list_items (list_id, model_name) VALUES (?, ?)",
                (list_id, car)
            )
        await conn.commit()
        print(f"✅ Lista creada con {len(cars)} coches.")

        # --- 3️⃣ Consultar las listas ---
        cursor = await conn.execute("SELECT id, name, description FROM vehicle_lists")
        lists = await cursor.fetchall()
        print("\n📋 Listas registradas:")
        for lst in lists:
            print(f"   ID={lst[0]} | Nombre={lst[1]} | Descripción={lst[2]}")

        # --- 4️⃣ Consultar coches asociados ---
        cursor = await conn.execute("SELECT model_name FROM vehicle_list_items WHERE list_id=?", (list_id,))
        cars_in_list = [r[0] for r in await cursor.fetchall()]
        print("\n🚗 Coches en la lista creada:")
        for c in cars_in_list:
            print(f"   - {c}")

        # --- 5️⃣ Eliminar lista (limpieza) ---
        await conn.execute("DELETE FROM vehicle_list_items WHERE list_id=?", (list_id,))
        await conn.execute("DELETE FROM vehicle_lists WHERE id=?", (list_id,))
        await conn.commit()
        print("\n🧹 Datos de prueba eliminados correctamente.")

    print("\n✅ [VEHICLE_LISTS TEST] Prueba completada sin errores.")


if __name__ == "__main__":
    asyncio.run(main())
