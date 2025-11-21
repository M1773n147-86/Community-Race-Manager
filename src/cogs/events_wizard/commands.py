"""
Archivo: commands.py
Ubicación: src/cogs/events_wizard/

Descripción:
Define los comandos principales relacionados con creación y gestión de eventos.

Incluye:
1️⃣ /create_event → inicia el Events Wizard (flujo modular actual)
2️⃣ /list_events → consulta eventos (activos, borradores, archivados)
3️⃣ /delete_event → elimina un evento
4️⃣ /archive_event → archiva un evento
5️⃣ /restore_event → restaura un evento

Toda la edición avanzada y programación se gestiona ahora mediante:
- Scheduler Wizard
- EventWizardSession (sesiones en memoria)
"""

import discord
from discord.ext import commands
from discord import app_commands
from src.cogs.wizards_shared.handlers.event_creation_handler import EventCreationHandler


# ========================================================================
# 🌟 1 — CREACIÓN DE EVENTOS (Wizard moderno)
# ========================================================================
class EventCreationCog(commands.Cog):
    """Comando principal `/create_event`."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="create_event",
        description="Inicia el asistente interactivo para crear un nuevo evento."
    )
    async def create_event(self, interaction: discord.Interaction):
        """Punto de entrada al wizard de creación."""
        if not await self._check_permissions(interaction):
            return await interaction.response.send_message(
                "🚫 No tienes permisos para crear eventos.",
                ephemeral=True
            )

        handler = EventCreationHandler(self.bot)
        await handler.start_wizard(interaction)

    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        """El propietario del servidor o usuarios autorizados pueden crear eventos."""
        if interaction.user.id == interaction.guild.owner_id:
            return True

        db = getattr(self.bot, "db", None)
        if not db:
            return False

        return await db.is_authorized(interaction.guild.id, "events", interaction.user)


# ========================================================================
# 🌟 2 — GESTIÓN BÁSICA DE EVENTOS (CRUD)
# ========================================================================
class EventManagementCog(commands.Cog):
    """Comandos básicos para administrar eventos ya creados."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 /list_events — Listado sencillo por estado
    @app_commands.command(name="list_events", description="Muestra eventos por estado.")
    async def list_events(self, interaction: discord.Interaction, status: str):
        db = self.bot.db.events
        events = await db.list_events(interaction.guild_id, status=status)

        if not events:
            return await interaction.response.send_message(
                f"⚠️ No hay eventos con estado **{status}**.",
                ephemeral=True,
            )

        embed = discord.Embed(
            title=f"Eventos — {status.upper()}",
            color=discord.Color.blurple(),
        )

        for ev in events:
            embed.add_field(
                name=f"📝 {ev['title']}",
                value=f"ID: `{ev['event_id']}`\nCreado: {ev['created_at'][:16]}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 🔹 /delete_event
    @app_commands.command(name="delete_event", description="Elimina un evento.")
    async def delete_event(self, interaction: discord.Interaction, event_id: int):
        db = self.bot.db.events
        event = await db.get_event(event_id)

        if not event:
            return await interaction.response.send_message(
                "❌ No existe ningún evento con ese ID.",
                ephemeral=True
            )

        await db.delete_event(event_id)
        await interaction.response.send_message(
            f"🗑️ Evento **{event['title']}** eliminado.",
            ephemeral=True
        )

    # 🔹 /archive_event
    @app_commands.command(name="archive_event", description="Archiva un evento activo.")
    async def archive_event(self, interaction: discord.Interaction, event_id: int):
        db = self.bot.db.events
        event = await db.get_event(event_id)

        if not event:
            return await interaction.response.send_message("❌ Evento no encontrado.", ephemeral=True)

        await db.archive_event(event_id, interaction.user.id)
        await interaction.response.send_message(
            f"📦 Evento **{event['title']}** archivado.",
            ephemeral=True
        )

    # 🔹 /restore_event
    @app_commands.command(name="restore_event", description="Restaura un evento archivado.")
    async def restore_event(self, interaction: discord.Interaction, event_id: int):
        db = self.bot.db.events
        event = await db.get_event(event_id)

        if not event or event["status"] != "archived":
            return await interaction.response.send_message(
                "⚠️ Ese evento no está archivado.",
                ephemeral=True
            )

        await db.update_event(event_id, {
            "status": "active",
            "archived_at": None,
            "archive_expires_at": None
        })

        await interaction.response.send_message(
            f"✅ Evento **{event['title']}** restaurado.",
            ephemeral=True
        )


# ========================================================================
# 🔹 REGISTRO
# ========================================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(EventCreationCog(bot))
    await bot.add_cog(EventManagementCog(bot))
