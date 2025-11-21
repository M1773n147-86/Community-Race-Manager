"""
Archivo: step_rules.py
Ubicación: src/cogs/events_wizard/steps/

Descripción general:
Este módulo implementa el paso 5 del asistente de creación de eventos (Event Wizard).
Su objetivo es recopilar toda la información normativa y de configuración complementaria
para un evento, incluyendo:

1. Normas básicas (texto libre, hasta 5 puntos breves de 250 caracteres cada uno)
2. Reglamento (enlace HTTPS externo o canal interno de Discord, elección exclusiva)
3. Briefing pre-carrera (configuración opcional de tiempo antes del evento, canal y tipo)
4. Skins personalizadas (habilitación opcional, enlace y nombre de archivo)

Cada submódulo actualiza la sesión activa del usuario mediante EventWizardSession.
La información se usa posteriormente en el resumen final (step_finalize) y en
la publicación del evento.

No implementa persistencia directa en la base de datos, dado que se trata de
configuraciones efímeras vinculadas a la sesión de creación del evento.
"""

import discord
from discord import ui, Interaction, SelectOption
from src.cogs.events_wizard.utils.wizard_session import EventWizardSession
from src.cogs.events_wizard.utils.helpers import event_step_header
from src.cogs.wizards_shared.views.navigation_view import WizardNavigationView


# --------------------------------------------------------
# 🔹 VISTA PRINCIPAL DEL PASO DE REGLAS / BRIEFING / SKINS
# --------------------------------------------------------
class StepRulesView(ui.View):
    """Vista principal del paso 5 — Reglas, reglamento, briefing y skins."""

    def __init__(self, user_id: int):
        super().__init__(timeout=600)
        self.user_id = user_id

        self.add_item(AddRulesButton())
        self.add_item(AddRegulationButton())
        self.add_item(AddBriefingButton())
        self.add_item(AddSkinsButton())
        self.add_item(WizardNavigationView(user_id, current_step=5))


# --------------------------------------------------------
# 📜 BOTÓN — AÑADIR REGLAS BÁSICAS
# --------------------------------------------------------
class AddRulesButton(ui.Button):
    """Abre modal para escribir normas básicas (hasta 5)."""

    def __init__(self):
        super().__init__(label="📜 Añadir reglas básicas", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(RulesModal(interaction.user.id))


class RulesModal(ui.Modal, title="📜 Normas del evento"):
    """Modal con hasta 5 reglas (250 caracteres cada una)."""

    rule_1 = ui.TextInput(label="Norma 1", max_length=250, required=False)
    rule_2 = ui.TextInput(label="Norma 2", max_length=250, required=False)
    rule_3 = ui.TextInput(label="Norma 3", max_length=250, required=False)
    rule_4 = ui.TextInput(label="Norma 4", max_length=250, required=False)
    rule_5 = ui.TextInput(label="Norma 5", max_length=250, required=False)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        rules = [r.value.strip() for r in [self.rule_1, self.rule_2,
                                           self.rule_3, self.rule_4, self.rule_5] if r.value.strip()]
        formatted = "\n".join([f"• {r}" for r in rules])
        EventWizardSession.update(self.user_id, "rules_text", formatted)
        await interaction.response.send_message("✅ Reglas guardadas correctamente.", ephemeral=True)


# --------------------------------------------------------
# 📘 BOTÓN — AÑADIR REGLAMENTO (ENLACE O CANAL)
# --------------------------------------------------------
class AddRegulationButton(ui.Button):
    """Permite seleccionar entre reglamento externo o canal interno."""

    def __init__(self):
        super().__init__(label="📘 Añadir reglamento", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "📘 Selecciona la fuente del reglamento:",
            view=RegulationSelectView(interaction.user.id),
            ephemeral=True
        )


class RegulationSelectView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.add_item(RegulationTypeSelect(self))


class RegulationTypeSelect(ui.Select):
    def __init__(self, parent):
        options = [
            SelectOption(label="🌐 Enlace externo (HTTPS)", value="external"),
            SelectOption(label="💬 Canal de Discord", value="discord"),
        ]
        super().__init__(placeholder="Selecciona el tipo de reglamento", options=options)
        self.parent = parent

    async def callback(self, interaction: Interaction):
        if self.values[0] == "external":
            await interaction.response.send_modal(RegulationExternalModal(self.parent.user_id))
        else:
            await interaction.response.send_message(
                "📘 Selecciona el canal de Discord que contiene el reglamento:",
                view=RegulationChannelSelect(self.parent.user_id),
                ephemeral=True,
            )


class RegulationExternalModal(ui.Modal, title="🌐 Enlace al reglamento (HTTPS)"):
    regulation_url = ui.TextInput(
        label="URL del reglamento",
        placeholder="https://tusitio.com/reglamento.pdf",
        required=True,
        max_length=200,
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        url = self.regulation_url.value.strip()
        if not url.startswith("https://"):
            await interaction.response.send_message("⚠️ Solo se permiten enlaces HTTPS.", ephemeral=True)
            return
        EventWizardSession.update(self.user_id, "rules_attachment_url", url)
        EventWizardSession.update(self.user_id, "rules_discord_channel", None)
        await interaction.response.send_message(f"✅ Enlace guardado correctamente: {url}", ephemeral=True)


class RegulationChannelSelect(ui.View):
    """Vista con selector de canales de Discord válidos."""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(ChannelSelectDropdown(self.user_id))


class ChannelSelectDropdown(ui.Select):
    """Desplegable para seleccionar un canal de texto o voz."""

    def __init__(self, user_id: int):
        super().__init__(placeholder="Selecciona un canal de texto o voz",
                         min_values=1, max_values=1, options=[])
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        if not self.options:
            self.options.extend([
                SelectOption(label=ch.name, value=str(ch.id))
                for ch in interaction.guild.channels
                if ch.type in (discord.ChannelType.text, discord.ChannelType.voice)
            ])
        channel = interaction.guild.get_channel(int(self.values[0]))
        EventWizardSession.update(
            self.user_id, "rules_discord_channel", channel.id)
        EventWizardSession.update(self.user_id, "rules_attachment_url", None)
        await interaction.response.send_message(f"✅ Canal seleccionado: {channel.mention}", ephemeral=True)


# --------------------------------------------------------
# 📋 BRIEFING PRE-CARRERA
# --------------------------------------------------------
class AddBriefingButton(ui.Button):
    """Configura si habrá briefing pre-carrera."""

    def __init__(self):
        super().__init__(label="📋 Configurar briefing pre-carrera",
                         style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "📋 ¿Deseas programar un briefing pre-carrera?",
            view=BriefingSelectView(interaction.user.id),
            ephemeral=True,
        )


class BriefingSelectView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.add_item(BriefingSelect(self.user_id))


class BriefingSelect(ui.Select):
    def __init__(self, user_id: int):
        options = [
            SelectOption(label="✅ Sí, programar briefing", value="yes"),
            SelectOption(label="❌ No, sin briefing", value="no")
        ]
        super().__init__(placeholder="Selecciona una opción", options=options)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        if self.values[0] == "yes":
            await interaction.response.send_message(
                "🕒 Configura el briefing pre-carrera:",
                view=BriefingConfigView(self.user_id),
                ephemeral=True
            )
        else:
            EventWizardSession.update(self.user_id, "has_briefing", False)
            EventWizardSession.update(
                self.user_id,
                "briefing_notice",
                "✅ No está estipulada una sesión de briefing previa al evento. "
                "Se ruega por favor que los participantes estén presentes al menos 15 minutos antes de iniciar el evento."
            )
            await interaction.response.send_message(
                "✅ No está estipulada una sesión de briefing previa al evento. "
                "Se ruega por favor que los participantes estén presentes al menos 15 minutos antes de iniciar el evento.",
                ephemeral=True
            )


class BriefingConfigView(ui.View):
    """Configura canal, tipo y tiempo de anticipación."""

    def __init__(self, user_id: int):
        super().__init__(timeout=240)
        self.user_id = user_id
        self.add_item(BriefingOffsetSelect(user_id))
        self.add_item(BriefingTypeSelect(user_id))
        self.add_item(BriefingChannelSelect(user_id))


class BriefingOffsetSelect(ui.Select):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [SelectOption(label=f"{m} min antes", value=str(
            m)) for m in range(15, 135, 15)]
        super().__init__(placeholder="Selecciona el tiempo antes del evento", options=options)

    async def callback(self, interaction: Interaction):
        offset = int(self.values[0])
        EventWizardSession.update(self.user_id, "has_briefing", True)
        EventWizardSession.update(
            self.user_id, "briefing_offset_minutes", offset)
        await interaction.response.send_message(f"✅ El briefing se realizará {offset} minutos antes del evento.", ephemeral=True)


class BriefingTypeSelect(ui.Select):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            SelectOption(label="Informativo", value="Informativo"),
            SelectOption(label="Obligatorio", value="Obligatorio"),
        ]
        super().__init__(placeholder="Selecciona el tipo de briefing", options=options)

    async def callback(self, interaction: Interaction):
        EventWizardSession.update(
            self.user_id, "briefing_type", self.values[0])
        await interaction.response.send_message(f"✅ Tipo de briefing: {self.values[0]}", ephemeral=True)


class BriefingChannelSelect(ui.Select):
    """Selector de canal donde se realizará el briefing."""

    def __init__(self, user_id: int):
        super().__init__(placeholder="Selecciona canal de briefing",
                         options=[], min_values=1, max_values=1)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        if not self.options:
            self.options.extend([
                SelectOption(label=ch.name, value=str(ch.id))
                for ch in interaction.guild.channels
                if ch.type in (discord.ChannelType.text, discord.ChannelType.voice)
            ])
        channel = interaction.guild.get_channel(int(self.values[0]))
        EventWizardSession.update(
            self.user_id, "briefing_channel_id", channel.id)
        await interaction.response.send_message(f"✅ Canal de briefing seleccionado: {channel.mention}", ephemeral=True)


# --------------------------------------------------------
# 🎨 SKINS PERSONALIZADAS
# --------------------------------------------------------
class AddSkinsButton(ui.Button):
    """Permite habilitar o deshabilitar skins personalizadas."""

    def __init__(self):
        super().__init__(label="🎨 Configurar skins personalizadas",
                         style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            "🎨 ¿Permitir skins personalizadas?",
            view=SkinsSelectView(interaction.user.id),
            ephemeral=True
        )


class SkinsSelectView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.add_item(SkinsSelect(self.user_id))


class SkinsSelect(ui.Select):
    def __init__(self, user_id: int):
        options = [
            SelectOption(label="✅ Sí, permitir skins", value="yes"),
            SelectOption(label="❌ No, no permitir", value="no")
        ]
        super().__init__(placeholder="Selecciona una opción", options=options)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        if self.values[0] == "yes":
            EventWizardSession.update(self.user_id, "allow_custom_skins", True)
            await interaction.response.send_modal(SkinsModal(self.user_id))
        else:
            EventWizardSession.update(
                self.user_id, "allow_custom_skins", False)
            await interaction.response.send_message("✅ Skins personalizadas deshabilitadas.", ephemeral=True)


class SkinsModal(ui.Modal, title="🎨 Información de skins personalizadas"):
    skins_url = ui.TextInput(
        label="Enlace de descarga (opcional)",
        placeholder="https://drive.google.com/...",
        required=False
    )
    skins_filename = ui.TextInput(
        label="Nombre del archivo (opcional)",
        placeholder="Ej. skins_GT3_pack.zip",
        required=False
    )

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        EventWizardSession.update(
            self.user_id, "skins_url", self.skins_url.value.strip())
        EventWizardSession.update(
            self.user_id, "skins_filename", self.skins_filename.value.strip())
        await interaction.response.send_message("✅ Información de skins guardada correctamente.", ephemeral=True)


# --------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL DEL PASO
# --------------------------------------------------------
async def show_rules_step(interaction: Interaction):
    """Lanza el paso 5 — Reglas, reglamento, briefing y skins."""
    view = StepRulesView(interaction.user.id)
    await interaction.followup.send(
        f"{event_step_header(5, 'Normas, reglamento y configuraciones especiales')}\n"
        "Configura las normas, reglamento, briefing y skins personalizadas del evento.",
        view=view,
        ephemeral=True
    )
