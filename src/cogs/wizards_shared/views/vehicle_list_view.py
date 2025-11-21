"""
Archivo: vehicle_list_view.py
Ubicación: src/cogs/wizards_general/views/

Descripción:
Define vistas y componentes de interfaz genéricos para la gestión 
de listas de vehículos (u otros elementos configurables) en los wizards.
Esta versión solo incluye la capa visual; la lógica y persistencia 
se implementarán en el módulo `vehicles_wizard`.
"""

import discord
from discord import ui, Interaction, ButtonStyle


class VehicleListManagerView(ui.View):
    """Vista genérica para gestionar listas de vehículos (interfaz base)."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(CreateListButton())
        self.add_item(EditListButton())
        self.add_item(DeleteListButton())
        self.add_item(ExportListsButton(disabled=True))
        self.add_item(ImportListsButton(disabled=True))
        self.add_item(BackToWizardButton())


class CreateListButton(ui.Button):
    def __init__(self):
        super().__init__(label="🆕 Crear lista", style=ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🧱 Placeholder: abrir modal de creación de lista (implementación específica en vehicles_wizard).",
            ephemeral=True
        )


class EditListButton(ui.Button):
    def __init__(self):
        super().__init__(label="✏️ Editar lista", style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🧱 Placeholder: abrir interfaz de edición de lista (implementación específica en vehicles_wizard).",
            ephemeral=True
        )


class DeleteListButton(ui.Button):
    def __init__(self):
        super().__init__(label="🗑️ Eliminar lista", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🧱 Placeholder: eliminar lista (implementación específica en vehicles_wizard).",
            ephemeral=True
        )


class ExportListsButton(ui.Button):
    def __init__(self, disabled=False):
        super().__init__(label="⬇️ Exportar listas (próx.)",
                         style=ButtonStyle.secondary, disabled=disabled)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("🧰 Exportación aún no implementada.", ephemeral=True)


class ImportListsButton(ui.Button):
    def __init__(self, disabled=False):
        super().__init__(label="⬆️ Importar listas (próx.)",
                         style=ButtonStyle.secondary, disabled=disabled)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("🧰 Importación aún no implementada.", ephemeral=True)


class BackToWizardButton(ui.Button):
    """Permite volver al asistente del evento tras gestionar listas."""

    def __init__(self):
        super().__init__(label="↩️ Volver al asistente", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🔄 Regresando al asistente principal...",
            ephemeral=True
        )
