"""
Archivo: config.py
Ubicación: src/utils/

Descripción:
Carga la configuración global del bot desde el archivo .env y las variables
de entorno del sistema. Devuelve un diccionario simple con los parámetros
más importantes para la inicialización del bot.

Incluye validación del token de Discord y asegura rutas absolutas para
el archivo de base de datos, evitando errores de ejecución según la
ubicación del script principal.
"""

import os
from dotenv import load_dotenv


def load_config() -> dict:
    """Carga variables de entorno y devuelve un diccionario de configuración."""
    load_dotenv()

    # Determinar ruta base del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    config = {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
        "COMMAND_PREFIX": os.getenv("COMMAND_PREFIX", "!"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "DATABASE_PATH": os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "bot.db")),
        "ENV": os.getenv("ENV", "dev"),  # dev / prod / test
    }

    # Validación obligatoria
    if not config["DISCORD_TOKEN"]:
        raise ValueError(
            "❌ No se encontró DISCORD_TOKEN en el entorno o archivo .env.")

    return config
