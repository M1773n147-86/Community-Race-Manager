"""
Archivo: track_list_manager_legacy.py
Ubicación: src/archive/

Descripción:
Versión previa del gestor de listas de circuitos. 
Incluye lógica funcional completa (UI + DB) anterior a la migración modular.
El código aquí almacenado servirá de referencia para la futura 
implementación del módulo `tracks_wizard` y su integración con la base de datos.
"""


import discord
from discord import ui, Interaction, ButtonStyle

# --------------------------------------------------------
# MANAGER — Listas de circuitos
# --------------------------------------------------------
# Este módulo gestiona la creación, edición y eliminación de
# listas de circuitos para el asistente de eventos.


# --------------------------------------------------------
# VISTA PRINCIPAL DEL GESTOR
# --------------------------------------------------------
class TrackListManagerView(ui.View):
    """Vista principal del gestor de listas de circuitos."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(CreateTrackListButton())
        self.add_item(EditTrackListButton())
        self.add_item(DeleteTrackListButton())
        self.add_item(BackToWizardButton())


# --------------------------------------------------------
# BLOQUE: Crear lista
# --------------------------------------------------------
class CreateTrackListButton(ui.Button):
    """Botón para crear una nueva lista de circuitos."""

    def __init__(self):
        super().__init__(label="🆕 Crear lista", style=ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        modal = TrackListCreateModal()
        await interaction.response.send_modal(modal)


class TrackListCreateModal(ui.Modal, title="🆕 Crear lista de circuitos"):
    """Permite crear una lista con nombre, descripción y circuitos."""

    list_name = ui.TextInput(
        label="Nombre de la lista",
        placeholder="Ejemplo: Circuitos Europeos",
        required=True,
        max_length=100
    )

    list_description = ui.TextInput(
        label="Descripción (opcional)",
        placeholder="Ejemplo: Circuitos para torneos GT3 europeos.",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=300
    )

    list_tracks = ui.TextInput(
        label="Circuitos (separados por comas)",
        placeholder="Ejemplo: Monza, Spa-Francorchamps, Imola, Nürburgring",
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: Interaction):
        from database.db import Database
        db = await Database.get_instance()

        async with await db.get_connection() as conn:
            await conn.execute(
                "INSERT INTO track_lists (name, description) VALUES (?, ?)",
                (self.list_name.value.strip(), self.list_description.value.strip())
            )
            await conn.commit()

            # Insertar circuitos si el campo no está vacío
            tracks_text = self.list_tracks.value.strip()
            track_count = 0
            if tracks_text:
                cursor = await conn.execute(
                    "SELECT id FROM track_lists WHERE name = ?",
                    (self.list_name.value.strip(),)
                )
                list_id = (await cursor.fetchone())[0]
                tracks = [t.strip()
                          for t in tracks_text.split(",") if t.strip()]
                for t in tracks:
                    await conn.execute(
                        "INSERT INTO track_list_items (list_id, track_name) VALUES (?, ?)",
                        (list_id, t)
                    )
                    track_count += 1
                await conn.commit()

        await interaction.response.send_message(
            f"✅ Lista **{self.list_name.value}** creada correctamente con {track_count} circuitos.",
            ephemeral=True
        )


# --------------------------------------------------------
# BLOQUE: Editar lista
# --------------------------------------------------------
class EditTrackListButton(ui.Button):
    """Botón para editar una lista existente."""

    def __init__(self):
        super().__init__(label="✏️ Editar lista", style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        from database.db import Database
        db = await Database.get_instance()

        async with await db.get_connection() as conn:
            cursor = await conn.execute("SELECT id, name FROM track_lists")
            lists = await cursor.fetchall()

        if not lists:
            await interaction.response.send_message(
                "⚠️ No hay listas de circuitos para editar.",
                ephemeral=True
            )
            return

        view = TrackListSelectForEditView(lists)
        await interaction.response.send_message(
            "✏️ Selecciona la lista de circuitos que deseas editar:",
            view=view,
            ephemeral=True
        )


class TrackListSelectForEditView(ui.View):
    def __init__(self, lists):
        super().__init__(timeout=120)
        self.add_item(TrackListEditSelect(lists))


class TrackListEditSelect(ui.Select):
    def __init__(self, lists):
        options = [discord.SelectOption(
            label=name, value=str(list_id)) for list_id, name in lists]
        super().__init__(
            placeholder="Selecciona una lista para editar",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):
        list_id = int(self.values[0])
        modal = TrackListEditModal(list_id)
        await interaction.response.send_modal(modal)


class TrackListEditModal(ui.Modal, title="✏️ Editar lista de circuitos"):
    """Permite modificar el nombre, descripción y circuitos de una lista."""

    list_name = ui.TextInput(
        label="Nuevo nombre de la lista",
        placeholder="Ejemplo: Circuitos europeos actualizados",
        required=True
    )

    list_description = ui.TextInput(
        label="Descripción (opcional)",
        style=discord.TextStyle.paragraph,
        required=False
    )

    list_tracks = ui.TextInput(
        label="Circuitos (separados por comas)",
        style=discord.TextStyle.paragraph,
        required=False
    )

    def __init__(self, list_id: int):
        super().__init__()
        self.list_id = list_id

    async def on_submit(self, interaction: Interaction):
        from database.db import Database
        db = await Database.get_instance()

        async with await db.get_connection() as conn:
            await conn.execute(
                "UPDATE track_lists SET name = ?, description = ? WHERE id = ?",
                (self.list_name.value.strip(),
                 self.list_description.value.strip(), self.list_id)
            )
            await conn.execute("DELETE FROM track_list_items WHERE list_id = ?", (self.list_id,))

            tracks = [t.strip()
                      for t in self.list_tracks.value.split(",") if t.strip()]
            for t in tracks:
                await conn.execute(
                    "INSERT INTO track_list_items (list_id, track_name) VALUES (?, ?)",
                    (self.list_id, t)
                )

            await conn.commit()

        await interaction.response.send_message(
            f"✅ Lista **{self.list_name.value}** actualizada correctamente con {len(tracks)} circuitos.",
            ephemeral=True
        )


# --------------------------------------------------------
# BLOQUE: Eliminar lista
# --------------------------------------------------------
class DeleteTrackListButton(ui.Button):
    """Botón para eliminar una lista de circuitos."""

    def __init__(self):
        super().__init__(label="🗑️ Eliminar lista", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        from database.db import Database
        db = await Database.get_instance()

        async with await db.get_connection() as conn:
            cursor = await conn.execute("SELECT id, name FROM track_lists")
            lists = await cursor.fetchall()

        if not lists:
            await interaction.response.send_message(
                "⚠️ No hay listas disponibles para eliminar.",
                ephemeral=True
            )
            return

        view = TrackListDeleteSelectView(lists)
        await interaction.response.send_message(
            "🗑️ Selecciona la lista de circuitos que deseas eliminar:",
            view=view,
            ephemeral=True
        )


class TrackListDeleteSelectView(ui.View):
    def __init__(self, lists):
        super().__init__(timeout=120)
        self.add_item(TrackListDeleteSelect(lists))


class TrackListDeleteSelect(ui.Select):
    def __init__(self, lists):
        options = [discord.SelectOption(
            label=name, value=str(list_id)) for list_id, name in lists]
        super().__init__(
            placeholder="Selecciona una lista para eliminar",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):
        list_id = int(self.values[0])
        list_name = next(
            (opt.label for opt in self.options if opt.value == str(list_id)), "Desconocido")
        view = TrackListDeleteConfirmView(list_id, list_name)
        await interaction.response.send_message(
            f"⚠️ ¿Seguro que deseas eliminar la lista **{list_name}**?\nEsta acción no se puede deshacer.",
            view=view,
            ephemeral=True
        )


class TrackListDeleteConfirmView(ui.View):
    def __init__(self, list_id: int, list_name: str):
        super().__init__(timeout=60)
        self.add_item(ConfirmDeleteTrackListButton(list_id, list_name))
        self.add_item(CancelDeleteTrackListButton())


class ConfirmDeleteTrackListButton(ui.Button):
    def __init__(self, list_id: int, list_name: str):
        super().__init__(label="✅ Sí, eliminar", style=ButtonStyle.danger)
        self.list_id = list_id
        self.list_name = list_name

    async def callback(self, interaction: Interaction):
        from database.db import Database
        db = await Database.get_instance()

        async with await db.get_connection() as conn:
            await conn.execute("DELETE FROM track_list_items WHERE list_id = ?", (self.list_id,))
            await conn.execute("DELETE FROM track_lists WHERE id = ?", (self.list_id,))
            await conn.commit()

        await interaction.response.edit_message(
            content=f"🗑️ Lista **{self.list_name}** eliminada correctamente.",
            view=None
        )


class CancelDeleteTrackListButton(ui.Button):
    def __init__(self):
        super().__init__(label="↩️ Cancelar", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(
            content="❎ Eliminación cancelada.",
            view=None
        )


# --------------------------------------------------------
# BLOQUE: Volver al asistente
# --------------------------------------------------------
class BackToWizardButton(ui.Button):
    """Permite volver al asistente del evento tras gestionar listas de circuitos."""

    def __init__(self):
        super().__init__(label="↩️ Volver al asistente", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        try:
            from cogs.wizard.steps.step_track import show_track_step
            await interaction.response.send_message(
                "🔄 Regresando al asistente de creación de evento...",
                ephemeral=True
            )
            await show_track_step(interaction)

        except Exception as e:
            print(f"[ERROR] Fallo al volver al asistente: {e}")
            await interaction.response.send_message(
                "⚠️ Ocurrió un error al intentar volver al asistente.",
                ephemeral=True
            )


# --------------------------------------------------------
# FUNCIÓN PRINCIPAL
# --------------------------------------------------------
async def show_track_list_manager(interaction: Interaction):
    """Lanza el gestor de listas de circuitos."""
    view = TrackListManagerView(interaction.user.id)
    await interaction.response.send_message(
        "⚙️ Gestor de listas de circuitos.",
        view=view,
        ephemeral=True
    )
