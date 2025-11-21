"""
Archivo: permissions_legacy.py
Ubicación: src/archive/

Descripción:
Versión previa del sistema de permisos por módulo del Community Race Manager.
Este archivo se conserva únicamente como referencia para futuras implementaciones
del control de autorizaciones granulares (por módulo). 
No forma parte del código activo del bot.
"""


from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

# añade aquí tus módulos futuros
MODULES = ["events", "reminders", "inscriptions"]


class Permissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ----------------------
    # Helper para comprobar permisos
    # ----------------------
    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == interaction.guild.owner_id

    # ----------------------
    # Assign role
    # ----------------------
    @app_commands.command(name="assign_role", description="Asignar permisos a un rol en un módulo")
    @app_commands.describe(
        module="Selecciona el módulo",
        role="Rol a autorizar"
    )
    @app_commands.choices(
        module=[app_commands.Choice(name=m, value=m) for m in MODULES]
    )
    async def assign_role(self, interaction: discord.Interaction, module: str, role: discord.Role):
        if not await self._check_owner(interaction):
            await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)
            return
        await self.bot.db.assign_role(interaction.guild.id, module, role.id)
        await interaction.response.send_message(f"Rol {role.mention} autorizado para el módulo `{module}`.", ephemeral=True)

    # ----------------------
    # Remove role
    # ----------------------
    @app_commands.command(name="remove_role", description="Quitar permisos a un rol en un módulo")
    @app_commands.describe(
        module="Selecciona el módulo",
        role="Rol a revocar"
    )
    @app_commands.choices(
        module=[app_commands.Choice(name=m, value=m) for m in MODULES]
    )
    async def remove_role(self, interaction: discord.Interaction, module: str, role: discord.Role):
        if not await self._check_owner(interaction):
            await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)
            return
        await self.bot.db.remove_role(interaction.guild.id, module, role.id)
        await interaction.response.send_message(f"Rol {role.mention} revocado para el módulo `{module}`.", ephemeral=True)

    # ----------------------
    # Assign user
    # ----------------------
    @app_commands.command(name="assign_user", description="Asignar permisos a un usuario en un módulo")
    @app_commands.describe(
        module="Selecciona el módulo",
        user="Usuario a autorizar"
    )
    @app_commands.choices(
        module=[app_commands.Choice(name=m, value=m) for m in MODULES]
    )
    async def assign_user(self, interaction: discord.Interaction, module: str, user: discord.Member):
        if not await self._check_owner(interaction):
            await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)
            return
        await self.bot.db.assign_user(interaction.guild.id, module, user.id)
        await interaction.response.send_message(f"Usuario {user.mention} autorizado para el módulo `{module}`.", ephemeral=True)

    # ----------------------
    # Remove user
    # ----------------------
    @app_commands.command(name="remove_user", description="Quitar permisos a un usuario en un módulo")
    @app_commands.describe(
        module="Selecciona el módulo",
        user="Usuario a revocar"
    )
    @app_commands.choices(
        module=[app_commands.Choice(name=m, value=m) for m in MODULES]
    )
    async def remove_user(self, interaction: discord.Interaction, module: str, user: discord.Member):
        if not await self._check_owner(interaction):
            await interaction.response.send_message("Solo el propietario del servidor puede usar este comando.", ephemeral=True)
            return
        await self.bot.db.remove_user(interaction.guild.id, module, user.id)
        await interaction.response.send_message(f"Usuario {user.mention} revocado para el módulo `{module}`.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Permissions(bot))
