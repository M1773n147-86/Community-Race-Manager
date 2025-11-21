"""
Archivo: track_list_view.py
Ubicación: src/cogs/wizards_general/views/

Descripción:
Define vistas y componentes de interfaz genéricos para la gestión 
de listas de elementos (en este caso, circuitos). 
Puede reutilizarse o extenderse en otros wizards (por ejemplo, vehículos o campeonatos)
para ofrecer funciones de creación, edición o eliminación de listas de recursos.

Nota: Este módulo solo contiene la lógica de interfaz. 
La manipulación de datos y persistencia en base de datos 
deberá implementarse en el módulo `tracks_wizard/handlers/`.
"""

import discord
from discord import ui, Interaction, ButtonStyle


class TrackListManagerView(ui.View):
    """Vista principal genérica para gestionar listas (tracks, vehículos, etc.)."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(CreateListButton())
        self.add_item(EditListButton())
        self.add_item(DeleteListButton())
        self.add_item(BackToWizardButton())


# --------------------------------------------------------
# Botones de acción base (interfaz genérica)
# --------------------------------------------------------

class CreateListButton(ui.Button):
    """Botón para crear una nueva lista genérica."""

    def __init__(self):
        super().__init__(label="🆕 Crear lista", style=ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🧱 Placeholder: abrir modal de creación de lista (implementación específica en tracks_wizard).",
            ephemeral=True
        )


class EditListButton(ui.Button):
    """Botón para editar una lista genérica."""

    def __init__(self):
        super().__init__(label="✏️ Editar lista", style=ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🧱 Placeholder: abrir interfaz de edición de lista (implementación específica en tracks_wizard).",
            ephemeral=True
        )


class DeleteListButton(ui.Button):
    """Botón para eliminar una lista genérica."""

    def __init__(self):
        super().__init__(label="🗑️ Eliminar lista", style=ButtonStyle.danger)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🧱 Placeholder: eliminar lista (implementación específica en tracks_wizard).",
            ephemeral=True
        )


class BackToWizardButton(ui.Button):
    """Permite volver al asistente del evento tras gestionar listas."""

    def __init__(self):
        super().__init__(label="↩️ Volver al asistente", style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🔄 Regresando al asistente principal...",
            ephemeral=True
        )
