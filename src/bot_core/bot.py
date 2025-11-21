"""
Archivo: bot.py
Ubicación: src/bot_core/

Descripción:
Define la clase principal que encapsula el bot de Discord, la base de datos
y los eventos globales (on_ready, on_disconnect, etc.).
"""

from __future__ import annotations

import logging
from datetime import datetime

import discord
from discord.ext import commands

from src.database.db import Database
from src.bot_core.loader import load_all_cogs

logger = logging.getLogger("BotCore")


class BotApp:
    """
    Contenedor principal de la aplicación:
      - instancia de commands.Bot
      - acceso a Database
      - configuración básica
    """

    def __init__(self, config: dict, db: Database):
        self.config = config
        self.db = db

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.bot = commands.Bot(
            command_prefix=config.get("COMMAND_PREFIX", "!"),
            intents=intents,
            help_command=None,
        )

        # Exponer la DB en el bot para que los Cogs puedan acceder
        setattr(self.bot, "db", db)

        self._register_events()

    # ------------------------------------------------------------------
    # Eventos globales
    # ------------------------------------------------------------------
    def _register_events(self) -> None:
        @self.bot.event
        async def on_ready():
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"🕒 Bot conectado como {self.bot.user} (ID: {self.bot.user.id})")
            logger.info(f"🕒 Hora de inicio: {start_time}")

            # Cargar Cogs
            try:
                await load_all_cogs(self.bot)
                logger.info("🧩 Todos los Cogs han sido procesados.")
            except Exception as e:
                logger.error(f"❌ Error al cargar Cogs: {e}")

            # Sincronizar comandos de barra si es necesario
            try:
                current_cmds = [cmd.name for cmd in await self.bot.tree.fetch_commands()]
                if not current_cmds:
                    await self.bot.tree.sync()
                    logger.info(
                        "✅ Comandos de barra sincronizados con Discord.")
                else:
                    logger.info(
                        "🔁 Comandos de barra ya estaban sincronizados.")
            except Exception as e:
                logger.warning(f"⚠️ No se pudieron sincronizar comandos: {e}")

        @self.bot.event
        async def on_disconnect():
            logger.warning("⚠️ Desconexión detectada de Discord.")

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.exception(f"❌ Error en evento '{event}'")

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Inicia la conexión con Discord."""
        token = self.config.get("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN no definido en configuración")

        logger.info("🚀 Iniciando conexión a Discord...")
        await self.bot.start(token, reconnect=False)

    async def close(self) -> None:
        """Cierra el bot sin tocar la base de datos (la maneja shutdown)."""
        await self.bot.close()
        logger.info("✅ Cliente de Discord cerrado desde BotApp.")
