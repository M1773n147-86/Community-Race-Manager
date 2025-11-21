"""
Archivo: vehicle_list_manager_legacy.py
Ubicación: src/archive/

Descripción:
Versión completa del gestor de listas de vehículos con integración a base de datos.
Se conserva como referencia para la futura migración al módulo `vehicles_wizard`
(handlers, views, modals) y la expansión del sistema de importación/exportación.
"""


import discord
from discord import ui, Interaction, ButtonStyle, SelectOption
from database.db import Database

# --------------------------------------------------------
# MANAGER — Listas de vehículos
# --------------------------------------------------------
# Este módulo gestiona la creación, edición y eliminación de
# listas de vehículos (coches) usadas en el asistente de eventos.


# --------------------------------------------------------
# VISTA PRINCIPAL DEL GESTOR
# --------------------------------------------------------
class VehicleListManagerView(ui.View):
    """Vista principal del gestor de listas de vehículos."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(CreateVehicleListButton())
        self.add_item(EditVehicleListButton())
        self.add_item(DeleteVehicleListButton())
        self.add_item(ExportVehicleListsButton(disabled=True))
        self.add_item(ImportVehicleListsButton(disabled=True))
        self.add_item(BackToWizardButton())


# --------------------------------------------------------
# BLOQUE: Crear lista
# --------------------------------------------------------
class CreateVehicleListButton(ui.Button):
    """Botón para crear una nueva lista de vehículos."""

    def __init__(self):
        super().__init__(label="🆕 Crear lista", style=ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        modal = VehicleListCreateModal()
        await interaction.response.send_modal(modal)


class VehicleListCreateModal(ui.Modal, title="🆕 Crear lista de coches"):
    """Permite crear una lista con nombre, descripción y vehículos."""

    list_name = ui.TextInput(
        label="Nombre de la lista",
        placeholder="Ejemplo: GT3 2025",
        required=True,
        max_length=100
    )

    list_description = ui.TextInput(
        label="Descripción (opcional)",
        placeholder="Ejemplo: Lista de vehículos GT3 moderna.",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=300
    )

    list_vehicles = ui.TextInput(
        label="Coches (separados por comas)",
        placeholder="Ferrari 488 GT3, Porsche 911 GT3 R, Mercedes AMG GT3",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: Interaction):
        from database.db import Database
        db = await Database.get_instance()

        vehicles = [v.strip()
                    for v in self.list_vehicles.value.split(",") if v.strip()]
        async with await db.get_connection() as conn:
            await conn.execute(
                "INSERT INTO vehicle_lists (name, description, created_by) VALUES (?, ?, ?)",
                (self.list_name.value.strip(),
                 self.list_description.value.strip(), interaction.user.id)
            )
            cursor = await conn.execute("SELECT id FROM vehicle_lists WHERE name = ?", (self.list_name.value.strip(),))
            list_id = (await cursor.fetchone())[0]

            for v in vehicles:
                await conn.execute(
                    "INSERT INTO vehicle_list_items (list_id, model_name) VALUES (?, ?)",
                    (list_id, v)
                )
            await conn.commit()

        await interaction.response.send_message(
            f"✅ Lista **{self.list_name.value}** creada correctamente con {len(vehicles)} vehículos.",
            ephemeral=True
        )


# --------------------------------------------------------
# BLOQUE: Editar lista
# --------------------------------------------------------
class EditVehicleListButton(ui.Button):
    """Botón para editar una lista existente."""

    def __init__(self):
        super().__init__(label="✏️ Editar lista", style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        db = await Database.get_instance()
        async with await db.get_connection() as conn:
            cursor = await conn.execute("SELECT id, name FROM vehicle_lists ORDER BY name ASC")
            lists = await cursor.fetchall()

        if not lists:
            await interaction.response.send_message("⚠️ No hay listas disponibles para editar.", ephemeral=True)
            return

        view = VehicleListSelectForEditView(lists)
        await interaction.response.send_message(
            "✏️ Selecciona la lista de vehículos que deseas editar:",
            view=view,
            ephemeral=True
        )


class VehicleListSelectForEditView(ui.View):
    def __init__(self, lists):
        super().__init__(timeout=120)
        self.add_item(VehicleListEditSelect(lists))


class VehicleListEditSelect(ui.Select):
    def __init__(self, lists):
        options = [discord.SelectOption(
            label=name, value=str(list_id)) for list_id, name in lists]
        super().__init__(placeholder="Selecciona una lista para editar",
                         options=options, min_values=1, max_values=1)

    async def callback(self, interaction: Interaction):
        list_id = int(self.values[0])
        db = await Database.get_instance()
        async with await db.get_connection() as conn:
            cur = await conn.execute("SELECT name, description FROM vehicle_lists WHERE id=?", (list_id,))
            row = await cur.fetchone()
            if not row:
                await interaction.response.send_message("⚠️ Lista no encontrada.", ephemeral=True)
                return
            name, desc = row
            cur = await conn.execute("SELECT model_name FROM vehicle_list_items WHERE list_id=?", (list_id,))
            vehicles = ", ".join([r[0] for r in await cur.fetchall()])

        modal = VehicleListEditModal(list_id, name, desc or "", vehicles)
        await interaction.response.send_modal(modal)


class VehicleListEditModal(ui.Modal, title="✏️ Editar lista de coches"):
    """Permite modificar una lista de vehículos existente."""

    def __init__(self, list_id: int, name: str, description: str, vehicles_csv: str):
        super().__init__()
        self.list_id = list_id
        self.list_name = ui.TextInput(
            label="Nombre", default=name, required=True)
        self.list_description = ui.TextInput(
            label="Descripción", default=description, style=discord.TextStyle.paragraph, required=False)
        self.list_vehicles = ui.TextInput(label="Coches (separados por comas)",
                                          default=vehicles_csv, style=discord.TextStyle.paragraph, required=False)
        self.add_item(self.list_name)
        self.add_item(self.list_description)
        self.add_item(self.list_vehicles)

    async def on_submit(self, interaction: Interaction):
        vehicles = [v.strip() for v in self.list_vehicles.value.split(
            ",") if v.strip()] if self.list_vehicles.value else []
        db = await Database.get_instance()
        async with await db.get_connection() as conn:
            await conn.execute("UPDATE vehicle_lists SET name=?, description=? WHERE id=?", (self.list_name.value, self.list_description.value, self.list_id))
            await conn.execute("DELETE FROM vehicle_list_items WHERE list_id=?", (self.list_id,))
            for v in vehicles:
                await conn.execute("INSERT INTO vehicle_list_items (list_id, model_name) VALUES (?, ?)", (self.list_id, v))
            await conn.commit()

        await interaction.response.send_message(
            f"✅ Lista **{self.list_name.value}** actualizada correctamente con {len(vehicles)} vehículos.",
            ephemeral=True
        )


# --------------------------------------------------------
# BLOQUE: Eliminar lista
# --------------------------------------------------------
class DeleteVehicleListButton(ui.Button):
    """Botón para eliminar una lista de vehículos."""

    def __init__(self):
        super().__init__(label="🗑️ Eliminar lista", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        db = await Database.get_instance()
        async with await db.get_connection() as conn:
            cursor = await conn.execute("SELECT id, name FROM vehicle_lists ORDER BY name ASC")
            lists = await cursor.fetchall()

        if not lists:
            await interaction.response.send_message("⚠️ No hay listas disponibles para eliminar.", ephemeral=True)
            return

        view = VehicleListDeleteSelectView(lists)
        await interaction.response.send_message(
            "🗑️ Selecciona la lista de vehículos que deseas eliminar:",
            view=view,
            ephemeral=True
        )


class VehicleListDeleteSelectView(ui.View):
    def __init__(self, lists):
        super().__init__(timeout=120)
        self.add_item(VehicleListDeleteSelect(lists))


class VehicleListDeleteSelect(ui.Select):
    def __init__(self, lists):
        options = [discord.SelectOption(
            label=name, value=str(list_id)) for list_id, name in lists]
        super().__init__(placeholder="Selecciona una lista para eliminar",
                         options=options, min_values=1, max_values=1)

    async def callback(self, interaction: Interaction):
        list_id = int(self.values[0])
        list_name = next(
            (opt.label for opt in self.options if opt.value == str(list_id)), "Desconocido")
        view = VehicleListDeleteConfirmView(list_id, list_name)
        await interaction.response.send_message(
            f"⚠️ ¿Seguro que deseas eliminar la lista **{list_name}**?\nEsta acción no se puede deshacer.",
            view=view,
            ephemeral=True
        )


class VehicleListDeleteConfirmView(ui.View):
    def __init__(self, list_id: int, list_name: str):
        super().__init__(timeout=60)
        self.add_item(ConfirmDeleteVehicleListButton(list_id, list_name))
        self.add_item(CancelDeleteVehicleListButton())


class ConfirmDeleteVehicleListButton(ui.Button):
    def __init__(self, list_id: int, list_name: str):
        super().__init__(label="✅ Sí, eliminar", style=ButtonStyle.danger)
        self.list_id = list_id
        self.list_name = list_name

    async def callback(self, interaction: Interaction):
        db = await Database.get_instance()
        async with await db.get_connection() as conn:
            await conn.execute("DELETE FROM vehicle_list_items WHERE list_id=?", (self.list_id,))
            await conn.execute("DELETE FROM vehicle_lists WHERE id=?", (self.list_id,))
            await conn.commit()

        await interaction.response.edit_message(
            content=f"🗑️ Lista **{self.list_name}** eliminada correctamente.",
            view=None
        )


class CancelDeleteVehicleListButton(ui.Button):
    def __init__(self):
        super().__init__(label="↩️ Cancelar", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(
            content="❎ Eliminación cancelada.",
            view=None
        )


# --------------------------------------------------------
# BLOQUE: Exportar / Importar (stub)
# --------------------------------------------------------
class ExportVehicleListsButton(ui.Button):
    """Botón para exportar listas (aún no implementado)."""

    def __init__(self, disabled: bool = False):
        super().__init__(label="⬇️ Exportar listas (próx.)",
                         style=ButtonStyle.secondary, disabled=disabled)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("🧰 Exportación aún no implementada.", ephemeral=True)


class ImportVehicleListsButton(ui.Button):
    """Botón para importar listas (aún no implementado)."""

    def __init__(self, disabled: bool = False):
        super().__init__(label="⬆️ Importar listas (próx.)",
                         style=ButtonStyle.secondary, disabled=disabled)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("🧰 Importación aún no implementada.", ephemeral=True)


# --------------------------------------------------------
# BLOQUE: Volver al asistente
# --------------------------------------------------------
class BackToWizardButton(ui.Button):
    """Permite volver al asistente de creación de evento."""

    def __init__(self):
        super().__init__(label="↩️ Volver al asistente", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        try:
            from cogs.wizard.steps.step_vehicles import show_vehicles_step
            await interaction.response.send_message("🔄 Regresando al asistente de creación de evento...", ephemeral=True)
            await show_vehicles_step(interaction)
        except Exception as e:
            print(f"[ERROR] Fallo al volver al asistente: {e}")
            await interaction.response.send_message("⚠️ Error al intentar volver al asistente.", ephemeral=True)


# --------------------------------------------------------
# FUNCIÓN PRINCIPAL
# --------------------------------------------------------
async def show_vehicle_list_manager(interaction: Interaction):
    """Lanza el gestor de listas de vehículos."""
    view = VehicleListManagerView(interaction.user.id)
    await interaction.response.send_message(
        "⚙️ Gestor de listas de vehículos.",
        view=view,
        ephemeral=True
    )
