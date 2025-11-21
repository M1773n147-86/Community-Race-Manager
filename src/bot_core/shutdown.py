"""
Archivo: shutdown.py
Ubicación: src/bot_core/

Descripción:
Funciones para realizar un cierre controlado del bot y de la base de datos.
"""

from __future__ import annotations

import logging
from datetime import datetime

from colorama import Fore, Style

from src.bot_core.bot import BotApp
from src.database.db import Database

logger = logging.getLogger("Shutdown")


async def graceful_shutdown(app: BotApp) -> None:
    """
    Cierra bot y base de datos de forma segura.
    """
    stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"🛑 Cierre solicitado a las {stop_time}.")
    print(f"{Fore.YELLOW}🛑 Cierre solicitado a las {stop_time}.{Style.RESET_ALL}")

    # Cerrar Discord
    try:
        await app.close()
        logger.info("🔒 Cliente Discord cerrado.")
    except Exception as e:
        logger.error(f"⚠️ Error al cerrar cliente Discord: {e}")

    # Cerrar DB
    try:
        db = await Database.get_instance()
        await db.safe_close()
    except Exception as e:
        logger.error(f"⚠️ Error al cerrar base de datos: {e}")
    else:
        logger.info("🔒 Base de datos cerrada correctamente.")
        print(f"{Fore.GREEN}🔒 Base de datos cerrada correctamente.{Style.RESET_ALL}")

    logger.info("✅ APP detenida con éxito. Hasta la próxima 👋")
    print(f"{Fore.MAGENTA}✅ APP detenida con éxito. Hasta la próxima 👋{Style.RESET_ALL}")
