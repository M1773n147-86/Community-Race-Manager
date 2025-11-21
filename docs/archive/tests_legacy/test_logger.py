"""Test rápido del sistema de logging con rotación diaria automática"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# ---------------------------------------------------------
# RUTAS BASE DEL PROYECTO
# ---------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "runtime.log")

# ---------------------------------------------------------
# CONFIGURACIÓN DE LOGGING CON ROTACIÓN DIARIA
# ---------------------------------------------------------
# Crea un nuevo log cada día a medianoche y mantiene 14 días de logs
rotating_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when="midnight",          # rotación diaria a medianoche
    interval=1,               # cada 1 día
    backupCount=14,           # conserva los últimos 14 días
    encoding="utf-8",
    utc=False                 # usa hora local
)

# Estilo del mensaje (igual que en el bot)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
rotating_handler.setFormatter(formatter)

# Registrar handler y salida en consola
logger = logging.getLogger("CRM-Test")
logger.setLevel(logging.INFO)
logger.addHandler(rotating_handler)
logger.addHandler(logging.StreamHandler())

# ---------------------------------------------------------
# PRUEBA DE ESCRITURA
# ---------------------------------------------------------
logger.info("🚀 [TEST] Inicio de prueba de logging con rotación diaria.")
logger.warning("⚠️ [TEST] Este es un aviso de prueba.")
logger.error("❌ [TEST] Simulación de error crítico.")
logger.info(f"🕒 [TEST] Timestamp de ejecución: {datetime.now()}")

print("\n✅ Test de logging completado con rotación diaria.")
print(f"📂 Revisa el archivo de logs en: {LOG_FILE}")
print("🧹 Los logs se rotan cada medianoche y se conservan 14 días.")
