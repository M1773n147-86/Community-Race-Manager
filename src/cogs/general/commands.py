"""
Archivo: commands.py
Ubicación: src/cogs/general/

Descripción:
Contiene comandos slash de propósito general para el bot Community Race Manager.
Incluye comandos informativos y de diagnóstico, como `/ping`, `/status` o `/say`,
utilizados para verificar la disponibilidad y funcionamiento general del bot.
"""
import discord
from discord.ext import commands
from discord import app_commands
import platform
import datetime


class GeneralCommands(commands.Cog):
    """
    Cog que agrupa comandos slash de propósito general.
    Incluye herramientas de diagnóstico, comprobación de estado
    y utilidades ligeras de interacción.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ----------------------
    # Comando: /ping
    # ----------------------
    @app_commands.command(name="ping", description="Comprueba la latencia del bot.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latencia: `{latency} ms`", ephemeral=True)

    # ----------------------
    # Comando: /say
    # ----------------------
    @app_commands.command(name="say", description="Hace que el bot repita un mensaje.")
    @app_commands.describe(message="El mensaje que el bot debe repetir.")
    async def say(self, interaction: discord.Interaction, message: str):
        """Repite un mensaje enviado por el usuario."""
        await interaction.response.send_message(message)

    # ----------------------
    # Comando: /status
    # ----------------------
    @app_commands.command(name="status", description="Muestra el estado general del bot.")
    async def status(self, interaction: discord.Interaction):
        """Devuelve información básica sobre el bot y su entorno."""
        bot_version = getattr(self.bot, "version", "1.0.0")
        py_version = platform.python_version()
        uptime = datetime.datetime.utcnow(
        ) - datetime.datetime.fromtimestamp(self.bot.start_time)
        uptime_str = str(uptime).split(".")[0]  # hh:mm:ss

        embed = discord.Embed(
            title="🧠 Estado del Bot",
            color=discord.Color.blurple(),
            description="Resumen del estado actual del bot y su entorno de ejecución."
        )
        embed.add_field(name="Versión", value=bot_version)
        embed.add_field(name="Python", value=py_version)
        embed.add_field(name="Uptime", value=uptime_str)
        embed.set_footer(text="Community Race Manager")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Registra el Cog en el bot principal."""
    # Guardamos la hora de inicio si no existe (para cálculo del uptime)
    if not hasattr(bot, "start_time"):
        bot.start_time = datetime.datetime.utcnow()
    await bot.add_cog(GeneralCommands(bot))
