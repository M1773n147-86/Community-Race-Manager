"""
Archivo: loader.py
Ubicación: src/bot_core/

Descripción:
Funciones auxiliares para cargar los Cogs del bot de forma centralizada.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("Loader")

# Lista centralizada de módulos de Cogs
COG_MODULES: tuple[str, ...] = (
    # General
    "src.cogs.general.commands",
    "src.cogs.moderation_crm.commands",

    # Wizards compartidos (vistas y handlers comunes)
    "src.cogs.wizards_shared.handlers.event_creation_handler",   # si es extension-ready
    # (si no es un Cog, puedes omitirlo aquí)

    # Events Wizard
    "src.cogs.events_wizard.commands",

    # Tracks / Vehicles
    # si en algún momento lo conviertes en Cog
    "src.cogs.tracks_wizard.handlers",
    "src.cogs.vehicles_wizard.handlers",    # idem

    # Scheduler Wizard
    "src.cogs.scheduler_wizard.commands",
)


async def load_all_cogs(bot: commands.Bot) -> None:
    """
    Carga todos los Cogs definidos en COG_MODULES.
    Loguea éxito o fallo por cada uno.
    """
    for module in COG_MODULES:
        try:
            await bot.load_extension(module)
            logger.info(f"✓ Cog cargado: {module}")
        except Exception as e:
            logger.error(f"✗ Error cargando {module}: {e}")
