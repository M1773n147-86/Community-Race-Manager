"""
Archivo: commands.py
Ubicación: src/cogs/moderation_crm/

Descripción:
Gestiona los comandos slash de autorización interna del bot Community Race Manager.
Permite al propietario del servidor agregar o eliminar usuarios y roles con permisos 
para usar la aplicación. Por defecto, solo el propietario del servidor tiene acceso 
a los comandos del bot; mediante este módulo se amplía o restringe dicho acceso a 
miembros o roles específicos de la comunidad.
"""
import discord
from discord.ext import commands
from discord import app_commands


class ModerationCRMCommands(commands.Cog):
    """
    Cog principal del módulo moderation_crm.
    Gestiona los comandos slash de autorización interna del bot.
    Permite agregar o eliminar usuarios y roles con permisos de uso
    del Community Race Manager.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # Helpers internos
    # -------------------------
    async def _is_owner(self, interaction: discord.Interaction) -> bool:
        """Verifica si el usuario que ejecuta el comando es el propietario del servidor."""
        return interaction.user.id == interaction.guild.owner_id

    async def _authorize_entity(self, guild_id: int, entity_id: int, entity_type: str):
        """Registra un rol o usuario autorizado en la base de datos."""
        db = getattr(self.bot, "db", None)
        if db:
            await db.add_authorized_entity(guild_id, entity_id, entity_type)

    async def _remove_authorized_entity(self, guild_id: int, entity_id: int, entity_type: str):
        """Elimina un rol o usuario autorizado de la base de datos."""
        db = getattr(self.bot, "db", None)
        if db:
            await db.remove_authorized_entity(guild_id, entity_id, entity_type)

    # -------------------------
    # Comandos principales
    # -------------------------

    @app_commands.command(name="add_role", description="Autoriza un rol para usar la APP.")
    @app_commands.describe(role="Rol al que se le otorgará acceso a la APP.")
    async def add_role(self, interaction: discord.Interaction, role: discord.Role):
        """Agrega un rol a la lista de roles autorizados para usar la APP."""
        if not await self._is_owner(interaction):
            return await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)

        await self._authorize_entity(interaction.guild.id, role.id, "role")
        await interaction.response.send_message(f"✅ El rol {role.mention} ahora está autorizado para usar la APP.", ephemeral=True)

    @app_commands.command(name="add_user", description="Autoriza a un usuario para usar la APP.")
    @app_commands.describe(user="Usuario que podrá usar la APP.")
    async def add_user(self, interaction: discord.Interaction, user: discord.User):
        """Agrega un usuario a la lista de usuarios autorizados para usar la APP."""
        if not await self._is_owner(interaction):
            return await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)

        await self._authorize_entity(interaction.guild.id, user.id, "user")
        await interaction.response.send_message(f"✅ {user.mention} ahora está autorizado para usar la APP.", ephemeral=True)

    @app_commands.command(name="remove_role", description="Revoca la autorización de un rol.")
    @app_commands.describe(role="Rol al que se le revocará acceso.")
    async def remove_role(self, interaction: discord.Interaction, role: discord.Role):
        """Elimina un rol de la lista de roles autorizados."""
        if not await self._is_owner(interaction):
            return await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)

        await self._remove_authorized_entity(interaction.guild.id, role.id, "role")
        await interaction.response.send_message(f"🚫 El rol {role.mention} ya no tiene acceso a la APP.", ephemeral=True)

    @app_commands.command(name="remove_user", description="Revoca la autorización de un usuario.")
    @app_commands.describe(user="Usuario al que se le revocará el acceso.")
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        """Elimina un usuario de la lista de autorizados."""
        if not await self._is_owner(interaction):
            return await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)

        await self._remove_authorized_entity(interaction.guild.id, user.id, "user")
        await interaction.response.send_message(f"🚫 {user.mention} ya no tiene acceso a la APP.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Registra el Cog en el bot principal."""
    await bot.add_cog(ModerationCRMCommands(bot))
