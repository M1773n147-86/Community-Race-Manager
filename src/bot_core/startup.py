"""
Archivo: startup.py
Ubicación: src/bot_core/

Descripción:
Funciones de arranque de la aplicación:
  - carga configuración
  - arranca logging
  - prepara base de datos
  - crea instancia de BotApp
"""

from __future__ import annotations

import logging

from colorama import init as colorama_init, Fore, Style

from src.utils.config import load_config
from src.utils.logger import setup_logging
from src.database.db import Database
from src.bot_core.bot import BotApp

logger = logging.getLogger("Startup")


async def create_app() -> BotApp:
    """
    Crea e inicializa la instancia principal del bot:
      - logging
      - configuración
      - base de datos
      - BotApp
    """
    colorama_init(autoreset=True)

    # 1) Configuración
    config = load_config()
    log_level = config.get("LOG_LEVEL", "INFO")
    setup_logging(log_level)

    logger.info("🚀 Iniciando Community Race Manager (Startup)")
    print(f"{Fore.CYAN}🚀 Iniciando Community Race Manager...{Style.RESET_ALL}")

    # 2) Base de datos
    db = await Database.get_instance()
    logger.info("📦 Base de datos inicializada.")
    print(f"{Fore.GREEN}📦 Base de datos inicializada.{Style.RESET_ALL}")

    # 3) Crear instancia del bot
    app = BotApp(config=config, db=db)
    logger.info("🤖 Instancia de BotApp creada.")
    print(f"{Fore.GREEN}🤖 Instancia de BotApp creada.{Style.RESET_ALL}")

    return app
