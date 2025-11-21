"""
Archivo: main.py
Ubicación: src/

Descripción:
Punto de entrada principal de Community Race Manager.
Orquesta:
  - creación de la app (startup)
  - registro de manejadores de señal
  - arranque del bot
  - cierre controlado (shutdown)
"""

import asyncio
import signal
from datetime import datetime

from colorama import Fore, Style

from src.bot_core.startup import create_app
from src.bot_core.shutdown import graceful_shutdown


async def main():
    start_time = datetime.now()
    print(f"{Fore.CYAN}🚀 Lanzando Community Race Manager...{Style.RESET_ALL}")
    print(f"🕒 Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    app = await create_app()

    loop = asyncio.get_running_loop()

    # Manejadores de señal (CTRL+C / SIGTERM)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(graceful_shutdown(app)),
            )
        except NotImplementedError:
            # En Windows o entornos restringidos puede no estar soportado
            pass

    try:
        await app.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await graceful_shutdown(app)
    finally:
        end_time = datetime.now()
        print(
            f"{Fore.MAGENTA}🏁 Bot detenido a las: "
            f"{end_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}"
        )
        print(f"⏱️ Tiempo total de ejecución: {end_time - start_time}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Ya gestionado en graceful_shutdown, pero por si acaso:
        print(f"{Fore.YELLOW}🧩 Interrupción manual detectada.{Style.RESET_ALL}")
