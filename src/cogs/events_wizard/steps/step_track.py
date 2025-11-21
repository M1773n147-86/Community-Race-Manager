# ========================================================
# Archivo: step_track.py
# Ubicación: src/cogs/events_wizard/steps/
# ========================================================

"""
Paso 3 del Event Wizard — Selección del circuito.

El usuario puede:
- Seleccionar un circuito desde listas guardadas (tracks_wizard)
- O registrar un circuito manualmente (nombre, variante, descripción)

El circuito seleccionado se almacena en EventWizardSession.
"""

import discord
from discord import ui, Interaction, SelectOption

from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView
from src.cogs.tracks_wizard import handlers as track_handlers


# --------------------------------------------------------
# 🔹 MODAL — Circuito manual
# --------------------------------------------------------
class TrackManualModal(ui.Modal, title="🏁 Registrar circuito manual"):
    track_name = ui.TextInput(
        label="Nombre del circuito",
        placeholder="Ej. Spa-Francorchamps",
        required=True,
    )
    track_variant = ui.TextInput(
        label="Variante (opcional)",
        placeholder="Ej. GP, National",
        required=False,
    )
    track_description = ui.TextInput(
        label="Descripción breve (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Ej. Circuito rápido con rectas largas.",
        required=False,
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        EventWizardSession.update(
            self.user_id, "track_name", self.track_name.value.strip())
        EventWizardSession.update(
            self.user_id, "track_variant", self.track_variant.value.strip() or "N/A")
        EventWizardSession.update(self.user_id, "track_description",
                                  self.track_description.value.strip() or "Sin descripción.")
        EventWizardSession.update(self.user_id, "track_list_id", None)

        await interaction.response.send_message(
            f"{event_step_header(3, 'Selección de circuito')}\n"
            f"✅ Circuito **{self.track_name.value}** registrado correctamente.",
            ephemeral=True
        )

        # Avanzar inmediatamente al siguiente paso
        from src.cogs.events_wizard.steps.step_vehicles import show_vehicles_step
        await show_vehicles_step(interaction)


# --------------------------------------------------------
# 🔹 SELECT — Selección de lista de circuitos
# --------------------------------------------------------
class TrackListSelect(ui.Select):
    def __init__(self, parent_view, lists):
        options = [
            SelectOption(label=lst["name"], value=str(lst["id"]))
            for lst in lists
        ]
        super().__init__(
            placeholder="📂 Selecciona una lista de circuitos",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.view_ref = parent_view

    async def callback(self, interaction: Interaction):
        list_id = int(self.values[0])
        list_name = next(
            o.label for o in self.options if o.value == str(list_id))

        EventWizardSession.update(
            interaction.user.id, "track_list_id", list_id)
        EventWizardSession.update(
            interaction.user.id, "track_list_name", list_name)
        EventWizardSession.update(interaction.user.id, "track_name", None)
        EventWizardSession.update(interaction.user.id, "track_variant", None)

        tracks = await track_handlers.get_tracks_in_list(list_id)
        if not tracks:
            await interaction.response.send_message("⚠️ Esta lista no tiene circuitos.", ephemeral=True)
            return

        # Sustituir contenido de la vista
        self.view_ref.clear_items()
        self.view_ref.add_item(TrackIndividualSelect(self.view_ref, tracks))
        self.view_ref.add_item(ConfirmTrackButton())

        await interaction.response.edit_message(
            content=f"🏁 Lista **{list_name}** cargada. Selecciona circuitos o confirma.",
            view=self.view_ref,
        )


# --------------------------------------------------------
# 🔹 SELECT — Circuitos individuales
# --------------------------------------------------------
class TrackIndividualSelect(ui.Select):
    def __init__(self, parent_view, tracks):
        options = [SelectOption(label=t, value=t) for t in tracks[:25]]
        super().__init__(
            placeholder="🏁 Selecciona circuitos individuales (opcional)",
            options=options,
            min_values=1,
            max_values=len(options),
        )
        self.view_ref = parent_view

    async def callback(self, interaction: Interaction):
        EventWizardSession.update(
            interaction.user.id, "track_selected_items", self.values)
        await interaction.response.send_message(
            f"✅ Seleccionados: {', '.join(self.values)}",
            ephemeral=True
        )


# --------------------------------------------------------
# 🔹 BOTÓN — Confirmar selección
# --------------------------------------------------------
class ConfirmTrackButton(ui.Button):
    def __init__(self):
        super().__init__(label="✅ Confirmar selección", style=discord.ButtonStyle.success)

    async def callback(self, interaction: Interaction):
        data = EventWizardSession.get(interaction.user.id) or {}
        list_name = data.get("track_list_name", "N/A")

        await interaction.response.send_message(
            f"{event_step_header(3, 'Selección de circuito')}\n"
            f"✅ Selección confirmada — Lista **{list_name}** asociada al evento.",
            ephemeral=True
        )

        from src.cogs.events_wizard.steps.step_vehicles import show_vehicles_step
        await show_vehicles_step(interaction)


# --------------------------------------------------------
# 🔹 BOTÓN — Registro manual de circuito
# --------------------------------------------------------
class ManualTrackButton(ui.Button):
    def __init__(self, user_id):
        super().__init__(label="✍️ Circuito manual", style=discord.ButtonStyle.secondary)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(TrackManualModal(self.user_id))


# --------------------------------------------------------
# 🔹 VISTA PRINCIPAL DEL PASO
# --------------------------------------------------------
class StepTrackView(ui.View):
    def __init__(self, user_id, lists, text_filled: bool):
        super().__init__(timeout=300)

        if lists:
            select = TrackListSelect(self, lists)
            select.disabled = text_filled
            self.add_item(select)
        else:
            self.add_item(
                ui.Button(label="No hay listas disponibles", disabled=True))

        self.add_item(ManualTrackButton(user_id))


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL DEL PASO
# --------------------------------------------------------
async def show_track_step(interaction: Interaction):
    user_id = interaction.user.id
    guild_id = interaction.guild.id if interaction.guild else None

    try:
        lists = await track_handlers.get_track_lists(guild_id)
    except Exception:
        lists = []

    data = EventWizardSession.get(user_id) or {}
    text_filled = bool(data.get("track_name"))

    view = StepTrackView(user_id, lists, text_filled)

    await interaction.followup.send(
        f"{event_step_header(3, 'Selección de circuito')}\n"
        "Puedes escribir el circuito manualmente o seleccionar desde una lista guardada.",
        view=view,
        ephemeral=True
    )

    # Navegación estándar
    nav = WizardNavigationView(user_id, current_step=3)
    await interaction.followup.send(
        "🧭 Usa los botones de navegación para avanzar o retroceder.",
        view=nav,
        ephemeral=True
    )
