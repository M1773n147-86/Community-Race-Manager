"""
Archivo: step_vehicles.py
Ubicación: src/cogs/events_wizard/steps/

Descripción:
Define el paso 3 del asistente de creación de eventos — selección de vehículos.
Permite seleccionar una lista de vehículos existente (desde vehicles_wizard)
o introducir modelos manualmente. No gestiona ni crea listas; solo consume los datos ya existentes.
"""

import discord
from discord import ui, Interaction, SelectOption
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView
from src.cogs.vehicles_wizard import handlers as vehicle_handlers


# --------------------------------------------------------
# MODAL — ENTRADA MANUAL DE VEHÍCULOS
# --------------------------------------------------------
class VehicleTextModal(ui.Modal, title="🚗 Añadir coches manualmente"):
    """Permite al usuario escribir modelos de coches manualmente."""

    vehicle_text = ui.TextInput(
        label="Introduce marca y modelo de coche(s)",
        placeholder="Ej: Ferrari 488 GT3, Porsche 911 GT3 R, BMW M4 GT3",
        style=discord.TextStyle.paragraph,
        required=False
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        """Guarda la lista de vehículos escrita manualmente."""
        text = self.vehicle_text.value.strip()
        EventWizardSession.update(self.user_id, "vehicle_text", text)
        EventWizardSession.update(self.user_id, "vehicle_list_id", None)
        EventWizardSession.update(
            self.user_id, "vehicle_selected_models", None)

        await interaction.response.send_message(
            "✅ Vehículos registrados manualmente.",
            ephemeral=True
        )

        from src.cogs.events_wizard.steps.step_vehicles import show_vehicles_step
        await show_vehicles_step(interaction)


# --------------------------------------------------------
# SELECTOR DE LISTAS DE VEHÍCULOS
# --------------------------------------------------------
class VehicleListSelect(ui.Select):
    """Selector de listas de vehículos registradas."""

    def __init__(self, parent_view, lists, disabled=False):
        options = [SelectOption(
            label=lst["name"], value=str(lst["id"])) for lst in lists]
        super().__init__(
            placeholder="📂 Selecciona una lista de coches",
            options=options,
            min_values=1,
            max_values=1,
            disabled=disabled
        )
        self.view_ref = parent_view

    async def callback(self, interaction: Interaction):
        """Gestiona la selección de una lista de vehículos."""
        list_id = int(self.values[0])
        list_name = next(
            o.label for o in self.options if o.value == str(list_id))

        EventWizardSession.update(
            interaction.user.id, "vehicle_list_id", list_id)
        EventWizardSession.update(
            interaction.user.id, "vehicle_list_name", list_name)
        EventWizardSession.update(interaction.user.id, "vehicle_text", "")

        await interaction.response.send_message(
            f"✅ Lista seleccionada: **{list_name}**",
            ephemeral=True
        )

        cars = await vehicle_handlers.get_vehicles_in_list(list_id)

        if not cars:
            await interaction.followup.send(
                "⚠️ Esta lista no tiene coches registrados.",
                ephemeral=True
            )
            return

        self.view_ref.clear_items()
        self.view_ref.add_item(VehicleIndividualSelect(self.view_ref, cars))
        self.view_ref.add_item(ConfirmVehicleButton(self.view_ref))

        await interaction.followup.send(
            "🚘 Puedes seleccionar coches individuales o confirmar todos los de la lista:",
            view=self.view_ref,
            ephemeral=True
        )


# --------------------------------------------------------
# SELECTOR DE COCHES INDIVIDUALES
# --------------------------------------------------------
class VehicleIndividualSelect(ui.Select):
    """Permite seleccionar coches individuales dentro de una lista."""

    def __init__(self, parent_view, cars):
        options = [SelectOption(label=c, value=c) for c in cars[:25]]
        super().__init__(
            placeholder="🚘 Selecciona coches individuales (opcional)",
            options=options,
            min_values=1,
            max_values=len(options)
        )
        self.view_ref = parent_view

    async def callback(self, interaction: Interaction):
        """Guarda los coches seleccionados manualmente."""
        EventWizardSession.update(
            interaction.user.id, "vehicle_selected_models", self.values)
        await interaction.response.send_message(
            f"✅ Coches seleccionados: {', '.join(self.values)}",
            ephemeral=True
        )


# --------------------------------------------------------
# BOTÓN DE CONFIRMACIÓN
# --------------------------------------------------------
class ConfirmVehicleButton(ui.Button):
    """Confirma la selección de vehículos y avanza al siguiente paso."""

    def __init__(self, parent_view):
        super().__init__(label="✅ Confirmar selección", style=discord.ButtonStyle.success)
        self.view_ref = parent_view

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        data = EventWizardSession.get(user_id)
        list_name = data.get("vehicle_list_name", "entrada manual")

        await interaction.response.send_message(
            f"{event_step_header(3, 'Selección de vehículos')}\n"
            f"✅ Selección confirmada — Fuente: **{list_name}**",
            ephemeral=True
        )

        view_nav = WizardNavigationView(user_id, current_step=3)
        await interaction.followup.send(
            "🧭 Control del asistente — puedes volver o avanzar según sea necesario.",
            view=view_nav,
            ephemeral=True
        )

        from src.cogs.events_wizard.steps.step_settings import show_settings_step
        await show_settings_step(interaction)


# --------------------------------------------------------
# BOTÓN DE ENTRADA MANUAL
# --------------------------------------------------------
class ManualVehicleButton(ui.Button):
    """Abre el modal de entrada manual de vehículos."""

    def __init__(self, user_id: int):
        super().__init__(label="✍️ Escribir coches manualmente",
                         style=discord.ButtonStyle.secondary)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        modal = VehicleTextModal(self.user_id)
        await interaction.response.send_modal(modal)


# --------------------------------------------------------
# VISTA PRINCIPAL
# --------------------------------------------------------
class StepVehiclesView(ui.View):
    """Vista principal del paso 3 del asistente (selección de vehículos)."""

    def __init__(self, user_id: int, lists, text_filled: bool):
        super().__init__(timeout=300)
        self.user_id = user_id

        if lists:
            selector = VehicleListSelect(self, lists)
            selector.disabled = text_filled
            self.add_item(selector)
        else:
            self.add_item(
                ui.Button(
                    label="No hay listas disponibles",
                    style=discord.ButtonStyle.secondary,
                    disabled=True
                )
            )

        self.add_item(ManualVehicleButton(user_id))


# --------------------------------------------------------
# FUNCIÓN PRINCIPAL DEL PASO
# --------------------------------------------------------
async def show_vehicles_step(interaction: Interaction):
    """Lanza el paso 3 del asistente — selección de vehículos."""
    user_id = interaction.user.id
    guild_id = interaction.guild.id if interaction.guild else None

    print(
        f"[STEP 3] Iniciando selección de vehículos para {interaction.user.name}")

    try:
        lists = await vehicle_handlers.get_vehicle_lists(guild_id)
    except Exception as e:
        print(
            f"[DB ERROR] No se pudieron obtener las listas de vehículos: {e}")
        lists = []

    data = EventWizardSession.get(user_id) or {}
    text_filled = bool(data.get("vehicle_text"))

    view = StepVehiclesView(user_id, lists, text_filled)

    await interaction.followup.send(
        f"{event_step_header(3, 'Selección de vehículos')}\n"
        "Puedes **escribir los coches manualmente** o **seleccionarlos desde una lista existente**.\n\n"
        "➡️ Si escribes coches manualmente, el selector de lista quedará deshabilitado.",
        view=view,
        ephemeral=True
    )

    view_nav = WizardNavigationView(user_id, current_step=3)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para avanzar o retroceder en el asistente.",
        view=view_nav,
        ephemeral=True
    )
