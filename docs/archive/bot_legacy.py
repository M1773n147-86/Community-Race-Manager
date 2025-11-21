"""Clase principal del bot, carga cogs y gestiona ciclo de vida."""
import yaml
import logging.config
import signal
import asyncio
import sys
import os
from datetime import datetime
from colorama import init as colorama_init, Fore, Style
from dotenv import load_dotenv
import discord
from discord.ext import commands
from src.database.db import Database
from src.utils.config import load_config
import logging
from logging.handlers import TimedRotatingFileHandler

# --------------------------------------------------------
# RUTA RAÍZ DEL PROYECTO
# --------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
    sys.path.append(os.path.dirname(ROOT_DIR))

# --------------------------------------------------------
# CONFIGURACIÓN DE LOGGING — usando PROD_logging_config.yaml
# --------------------------------------------------------

CONFIG_PATH = os.path.join(ROOT_DIR, "config", "PROD_logging_config.yaml")

# Crear carpeta de logs si no existe
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)
    PROD_logger = logging.getLogger("PROD_Logger")
    PROD_logger.info(
        "📂 Logging de producción inicializado desde archivo YAML.")
except Exception as e:
    # Si falla la carga YAML, usar configuración de respaldo
    print(
        f"⚠️ No se pudo cargar PROD_logging_config.yaml ({e}), aplicando configuración por defecto.")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(
                LOG_DIR, "runtime_fallback.log"), encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    PROD_logger = logging.getLogger("PROD_Logger")
    PROD_logger.warning(
        "⚠️ Usando configuración de log por defecto (fallback).")


# --------------------------------------------------------
# CLASE PRINCIPAL DEL BOT
# --------------------------------------------------------
class CommunityRaceManager:
    def __init__(self, config: dict):
        """Inicializa el bot y la conexión con la base de datos."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.config = config
        self.bot = commands.Bot(
            command_prefix=config.get("COMMAND_PREFIX", "!"),
            intents=intents,
            help_command=None
        )
        self.db = Database(config.get("DATABASE_PATH", "./data/bot.db"))
        self._register_events()

    # --------------------------------------------------------
    # EVENTOS PRINCIPALES
    # --------------------------------------------------------
    def _register_events(self):
        @self.bot.event
        async def on_ready():
            """Evento disparado al iniciar el bot correctamente."""
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            PROD_logger.info(f"🕒 Bot iniciado a las {start_time}")
            print(f"{Fore.CYAN}🕒 Bot iniciado: {start_time}{Style.RESET_ALL}")
            PROD_logger.info(
                f"✅ Bot conectado como {self.bot.user} (ID: {self.bot.user.id})")

            try:
                await self.db.connect()
                PROD_logger.info("📦 Conexión con base de datos inicializada.")
                print(
                    f"{Fore.GREEN}📦 Conexión con base de datos inicializada.{Style.RESET_ALL}")

                await self._load_cogs()
                PROD_logger.info("🧩 Cogs cargados correctamente (on_ready).")
                print(
                    f"{Fore.GREEN}🧩 Cogs cargados correctamente (on_ready).{Style.RESET_ALL}")

                # Evitar sincronizaciones redundantes
                synced = False
                try:
                    current_cmds = [cmd.name for cmd in await self.bot.tree.fetch_commands()]
                    if not current_cmds or len(current_cmds) < 8:
                        await self.bot.tree.sync()
                        synced = True
                except Exception as sync_error:
                    PROD_logger.warning(
                        f"⚠️ No se pudieron sincronizar comandos: {sync_error}")
                    print(
                        f"{Fore.YELLOW}⚠️ No se pudieron sincronizar comandos: {sync_error}{Style.RESET_ALL}")

                if synced:
                    PROD_logger.info("✅ Comandos sincronizados con Discord.")
                    print(
                        f"{Fore.GREEN}✅ Comandos sincronizados con Discord.{Style.RESET_ALL}")
                else:
                    PROD_logger.info("🔁 Comandos ya estaban sincronizados.")
                    print(
                        f"{Fore.BLUE}🔁 Comandos ya estaban sincronizados.{Style.RESET_ALL}")

                PROD_logger.info("🚀 APP desplegada con éxito.")
                print(f"{Fore.MAGENTA}🚀 APP desplegada con éxito.{Style.RESET_ALL}")

            except Exception as e:
                import traceback
                PROD_logger.error(f"❌ Error en on_ready: {e}")
                print(f"{Fore.RED}❌ Error en on_ready: {e}{Style.RESET_ALL}")
                traceback.print_exc()

        @self.bot.event
        async def on_disconnect():
            msg = f"⚠️ Desconexión detectada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            PROD_logger.warning(msg)
            print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            PROD_logger.error(f"❌ Error en evento {event}")
            print(f"{Fore.RED}❌ Error en evento {event}{Style.RESET_ALL}")

    # --------------------------------------------------------
    # CARGA DE COGS
    # --------------------------------------------------------
    async def _load_cogs(self):
        """Carga los módulos (cogs) del bot de forma asíncrona."""
        cogs = (
            "cogs.general",
            "cogs.moderation",
            "cogs.fun",
            "cogs.permissions",
            "cogs.wizard.create_event",
            "cogs.wizard.event_wizard",
            "cogs.wizard.manage_events",
        )

        for cog in cogs:
            try:
                await self.bot.load_extension(cog)
                PROD_logger.info(f"🧩 Cargado cog: {cog}")
                print(f"{Fore.CYAN}🧩 Cargado cog: {cog}{Style.RESET_ALL}")
            except Exception as e:
                PROD_logger.warning(f"⚠️ Error cargando {cog}: {e}")
                print(f"{Fore.YELLOW}⚠️ Error cargando {cog}: {e}{Style.RESET_ALL}")

    # --------------------------------------------------------
    # ARRANQUE PRINCIPAL
    # --------------------------------------------------------
    async def start_bot(self):
        """Inicia el bot con control de cierre limpio."""
        token = self.config.get("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN no definido en configuración")

        PROD_logger.info("🔍 Intentando conectar a Discord...")
        print(f"{Fore.CYAN}🔍 Intentando conectar a Discord...{Style.RESET_ALL}")
        print(f"TOKEN detectado: {token[:10]}...")

        try:
            await self.bot.start(token, reconnect=False)
        except discord.ConnectionClosed:
            PROD_logger.warning(
                "⚠️ Conexión de Discord cerrada inesperadamente.")
            print(
                f"{Fore.YELLOW}⚠️ Conexión de Discord cerrada inesperadamente.{Style.RESET_ALL}")
        except asyncio.CancelledError:
            PROD_logger.warning("🧩 Ejecución cancelada manualmente.")
            print(f"{Fore.YELLOW}🧩 Ejecución cancelada manualmente.{Style.RESET_ALL}")
        finally:
            await self.db.safe_close()
            await self.bot.close()
            PROD_logger.info("✅ Cliente Discord cerrado correctamente.")
            print(
                f"{Fore.GREEN}✅ Cliente Discord cerrado correctamente.{Style.RESET_ALL}")


# --------------------------------------------------------
# FUNCIÓN DE CIERRE SEGURO
# --------------------------------------------------------
async def graceful_shutdown(bot_instance):
    """Cierra el bot y la base de datos de forma segura."""
    stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    PROD_logger.info(f"🛑 Cierre solicitado a las {stop_time}.")

    if getattr(bot_instance, "_shutting_down", False):
        return
    bot_instance._shutting_down = True

    try:
        await bot_instance.db.safe_close()
        await bot_instance.bot.close()
        PROD_logger.info(
            "🔒 Base de datos y cliente Discord cerrados correctamente.")
        PROD_logger.info("✅ APP detenida con éxito. Hasta la próxima! 👋")
        print(
            f"{Fore.GREEN}🔒 Base de datos y cliente Discord cerrados correctamente.{Style.RESET_ALL}")
        print(
            f"{Fore.MAGENTA}✅ APP detenida con éxito. Hasta la próxima! 👋{Style.RESET_ALL}")
    except Exception as e:
        PROD_logger.error(f"⚠️ Error durante el cierre: {e}")
        print(f"{Fore.RED}⚠️ Error durante el cierre: {e}{Style.RESET_ALL}")


# --------------------------------------------------------
# BLOQUE PRINCIPAL DE EJECUCIÓN
# --------------------------------------------------------
if __name__ == "__main__":
    async def main():
        start_time = datetime.now()
        PROD_logger.info("🚀 Iniciando Community Race Manager...")
        print(f"{Fore.CYAN}🚀 Iniciando Community Race Manager...{Style.RESET_ALL}")
        print(f"🕒 Inicio del bot: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        config = load_config()
        manager = CommunityRaceManager(config)
        loop = asyncio.get_event_loop()

        if hasattr(signal, "SIGTERM"):
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(
                        sig, lambda s=sig: asyncio.create_task(graceful_shutdown(manager)))
                except NotImplementedError:
                    pass

        try:
            await manager.start_bot()
        except (KeyboardInterrupt, asyncio.CancelledError):
            await graceful_shutdown(manager)
        finally:
            end_time = datetime.now()
            PROD_logger.info(
                f"🏁 Bot detenido a las: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            PROD_logger.info(
                f"⏱️ Tiempo total de ejecución: {end_time - start_time}")
            print(
                f"{Fore.MAGENTA}🏁 Bot detenido a las: {end_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            print(f"⏱️ Tiempo total de ejecución: {end_time - start_time}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        PROD_logger.warning("🧩 Interrupción manual detectada.")
        print(f"{Fore.YELLOW}🧩 Interrupción manual detectada.{Style.RESET_ALL}")
