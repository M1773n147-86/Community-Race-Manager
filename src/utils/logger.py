"""
Archivo: logger.py
Ubicación: src/

Descripción:
Sistema centralizado de logging para Community Race Manager.
Proporciona:
- Configuración única (evita duplicar handlers)
- Nivel configurable vía config.py (LOG_LEVEL)
- Formato uniforme con hora, módulo y nivel
- Logger obtenido por módulo mediante get_logger(__name__)
"""

import logging
import sys


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """
    Configura el logging global del proyecto.

    - Evita añadir múltiples handlers (muy común al reiniciar el bot)
    - Redirige logs al stdout para compatibilidad con Docker / Fly.io
    """

    root = logging.getLogger()

    # Evitar añadir handlers repetidos
    if root.handlers:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    root.setLevel(numeric_level)
    root.addHandler(handler)

    # Reducir el ruido del logger de discord.py
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)

    print(f"🟦 Logging inicializado (nivel={level.upper()})")


def get_logger(module_name: str) -> logging.Logger:
    """
    Devuelve un logger para un módulo específico.
    Uso recomendado:
        log = get_logger(__name__)
        log.info("Mensaje...")
    """
    return logging.getLogger(module_name)
