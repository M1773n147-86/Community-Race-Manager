🧩 To-Do — Tareas Pendientes de Integrar

Proyecto: Community Race Manager
Ubicación: /docs/To_Do.md
Propósito:
Este archivo recopila funcionalidades y mejoras planificadas que aún no se han implementado.
Cada punto incluye una breve descripción y un ejemplo ilustrativo de cómo podría integrarse.

-----------------------------------------------------

🧱 FASE 1 — Consolidación estructural y migraciones
Objetivo:

Reestructurar el proyecto para lograr una arquitectura modular, escalable y reutilizable.
Esta fase incluye la migración de módulos legacy, la separación de responsabilidades y la creación de wizards dedicados.

1️⃣ Control de permisos por módulo

Descripción:
Extender el sistema de autorizaciones internas (authorized_entities) para permitir que los permisos
se apliquen a módulos específicos (por ejemplo: events, reminders, inscriptions),
en lugar de autorizar globalmente el acceso al bot.

Implementación futura (concepto):

await conn.execute("""
ALTER TABLE authorized_entities
ADD COLUMN module TEXT DEFAULT NULL;
""")

2️⃣ Sistema de Ticketing (soporte de comunidad)

Descripción:
Implementar un sistema de tickets gestionado desde Discord, que permita a los usuarios crear solicitudes
de soporte o inscripciones manuales.
Cada ticket generará un canal temporal con permisos restringidos y etiquetas automáticas.

3️⃣ Registro de logs detallados de comandos

Descripción:
Agregar un sistema centralizado de registro de ejecución de comandos (quién, cuándo, comando usado, éxito/error).
Servirá para auditoría, depuración y análisis de uso.

4️⃣ Integración con Dashboard Web (futuro)

Descripción:
Sincronizar los datos del bot con un dashboard gestionado vía API REST (FastAPI).
Permitirá editar eventos, usuarios y autorizaciones desde una interfaz gráfica web.

5️⃣ Localización multilenguaje (i18n)

Descripción:
Extraer todos los textos visibles al usuario a archivos de localización (/data/localization/<lang>.json)
y agregar un gestor de idioma por servidor.

6️⃣ Sistema de gestión de circuitos (Tracks Wizard)

Descripción:
Implementar el módulo tracks_wizard encargado de crear, listar, editar y eliminar circuitos.
Servirá como fuente de datos para el events_wizard.

7️⃣ Módulo de administración de eventos (Events Admin)

Descripción:
Reubicar y ampliar las funciones del antiguo manage_events.py en un módulo
dedicado (events_admin/commands.py), complementando el events_wizard.

8️⃣ Migración del gestor de listas de circuitos a tracks_wizard

Descripción:
Migrar la lógica específica de gestión de listas de circuitos desde la versión legacy
a un módulo dedicado tracks_wizard (handlers, views, modals), sincronizando el esquema de BD.

9️⃣ Migración del gestor de listas de vehículos a vehicles_wizard

Descripción:
Migrar la lógica específica de gestión de listas de vehículos desde la versión legacy
a un módulo dedicado vehicles_wizard (handlers, views, modals).

1️⃣0️⃣ Scheduler Wizard (programación de eventos)

Descripción: módulo independiente reutilizable que permita programar publicación (scheduled_publish_utc), apertura de inscripciones (registration_open_utc) y recordatorios automáticos.

API prevista:

show_scheduler_for_current_session(interaction) — inicia la UI cuando venimos desde step_finalize.

Slash: /schedule_saved_event — abrir scheduler para un evento guardado.

Persistencia:

Guardar status='scheduled', scheduled_publish_utc, registration_open_utc.

Ejecución:

Tarea periódica (background loop) que publique al llegar la hora.

Ejemplo conceptual:

# scheduler_wizard/views.py
async def show_scheduler_for_current_session(interaction):
    # 1) pedir fecha/hora publicación (modal)
    # 2) pedir apertura inscripciones (opcional)
    # 3) pedir recordatorios (checkbox/select)
    # 4) persistir y marcar status='scheduled'
    await interaction.response.send_message("🗓️ Evento programado.", ephemeral=True)

1️⃣1️⃣ — “Actualización de esquema y unificación post-Scheduler”

Descripción:
Tras la implementación del scheduler_wizard, actualizar el esquema de base de datos para reflejar la nueva lógica de programación, gestión de estados y trazabilidad de eventos.
Incluir la creación del índice compuesto (guild_id, LOWER(title)) para asegurar unicidad de nombres de eventos dentro de cada comunidad, y revisar la coherencia de las tablas y dependencias con la nueva arquitectura modular.

Implementación futura (concepto):

-- Asegurar unicidad de nombres de eventos dentro del mismo servidor
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_guild_title
ON events (guild_id, LOWER(title));

-- Nuevos estados contemplados en el flujo de Scheduler:
-- 'draft' | 'scheduled' | 'active' | 'completed' | 'archived'

Notas:
Esta fase incluirá la revisión y unificación de todos los módulos legacy que aún no se hayan migrado al nuevo formato modular.
Se consolidará la gestión de created_by, created_at, last_edited_by, last_edited_date en todas las operaciones CRUD.
El proceso de actualización del esquema será atómico para garantizar compatibilidad hacia atrás con los datos existentes.

1️⃣2️⃣

Implementar helper reutilizable para encabezados de pasos (compose_step_header)

Descripción:
Centralizar el formato de encabezados de pasos en un helper común dentro de
src/cogs/wizards_shared/helpers.py (o utils/helpers.py si se decide globalizar).
El objetivo es unificar el estilo visual de todos los wizards y reducir redundancias
en los mensajes followup.send.

Implementación futura (concepto):

# wizards_shared/helpers.py
from src.utils.wizard_constants import wizard_step_header

def compose_step_header(step_number: int, title: str) -> str:
    """Genera un encabezado estandarizado para cada paso del wizard."""
    return f"{wizard_step_header(step_number)}\n**{title}**"

Ejemplo de uso:

from src.cogs.wizards_shared.helpers import compose_step_header

await interaction.followup.send(
    f"{compose_step_header(2, 'Configuración de horario')}\n"
    "Selecciona la fecha y hora del evento.",
    view=StepScheduleView(interaction.user.id),
    ephemeral=True
)


Notas:
Requiere actualizar los módulos events_wizard, scheduler_wizard, tracks_wizard y vehicles_wizard para usar el helper en lugar del formato manual.
Mantiene el estándar visual uniforme entre asistentes.
Compatible con wizard_step_header() dinámico actual.

-----------------------------------------------------

⚙️ FASE 2 — Validación funcional del Events Wizard
Objetivo:

Comprobar la coherencia funcional del events_wizard tras la reestructuración.
Se revisará paso a paso el flujo de creación de eventos, garantizando consistencia en sesiones, navegación y persistencia.

2.1 Validar paso step_schedule.py

Descripción:
Verificar formato UTC y sincronización con la sesión:

EventWizardSession.update(user_id, "event_datetime_utc", utc_dt.isoformat())

2.2 Validar paso step_track.py

Descripción:
Confirmar la coherencia entre selección manual y listas de circuitos.
Validar integración con track_handlers:

tracks = await track_handlers.get_tracks_in_list(list_id)

2.3 Validar paso step_vehicles.py

Descripción:
Comprobar consistencia de datos (vehicle_list_id, vehicle_selected_models)
y compatibilidad con vehicle_handlers.

2.4 Validar paso step_settings.py

Descripción:
Asegurar el guardado correcto de parámetros técnicos (tiempos, clima, daños).
Validar la conversión segura de tipos (safe_int, safe_float).

2.5 Validar paso step_rules.py

Descripción:
Verificar coherencia de submódulos: reglas, reglamento, briefing y skins.
Confirmar exclusividad de reglamento (enlace HTTPS o canal Discord).
Validar persistencia temporal en sesión.

2.6 Validar paso step_finalize.py

Descripción:
Comprobar consolidación de datos y sincronización con la tabla events.
Validar trazabilidad (created_by, last_edited_by, published_at).

2.7 Validar navigation_view.py

Descripción:
Asegurar sincronía del mapa STEP_MAP con los pasos activos (1–6).
Verificar disponibilidad condicional de botones (anterior, siguiente, cancelar).

✅ Resultado esperado:
El events_wizard debe operar de forma íntegra, sin dependencias legacy y con un flujo estable entre pasos,
dejando lista la base para la FASE 3: Integración del Wizard Handler Universal.

-----------------------------------------------------

🧠 FASE 3 — Integración del Wizard Handler Universal
Objetivo general:

Centralizar la lógica de control y flujo de todos los asistentes (wizards) del proyecto —eventos, circuitos y vehículos— en un módulo unificado y reutilizable, eliminando duplicación de código y garantizando consistencia en la navegación, validación y persistencia de datos.

3.1 Crear módulo wizard_handler_universal.py

Ubicación sugerida:
src/cogs/wizards_general/handlers/wizard_handler_universal.py

Descripción:
Implementar una clase base WizardHandler que sirva como plantilla para todos los asistentes.
Esta clase gestionará:

Sesión activa (EventWizardSession o sus variantes).

Registro de pasos (STEP_MAP dinámico).

Transiciones controladas entre pasos (next_step(), previous_step()).

Validación previa a avanzar (validate_step()).

Finalización segura (end_session()).

Ejemplo de estructura base:

class WizardHandler:
    def __init__(self, bot, session_class, step_map: dict):
        self.bot = bot
        self.session_class = session_class
        self.step_map = step_map

    async def start_wizard(self, interaction):
        """Inicia el flujo del wizard."""
        user_id = interaction.user.id
        self.session_class.start(user_id)
        await self.load_step(interaction, 1)

    async def load_step(self, interaction, step_number):
        """Carga dinámicamente el módulo correspondiente."""
        module_name = self.step_map.get(step_number)
        if not module_name:
            await interaction.response.send_message(
                f"⚠️ Paso {step_number} no definido.", ephemeral=True)
            return
        module_path = f"src.cogs.events_wizard.steps.{module_name}"
        module = __import__(module_path, fromlist=["show_step"])
        await getattr(module, "show_step")(interaction)

3.2 Implementar herencia por tipo de wizard

Descripción:
Crear clases derivadas del WizardHandler adaptadas a cada wizard específico:

EventCreationHandler → src/cogs/events_wizard/handlers/event_creation_handler.py

TrackCreationHandler → src/cogs/tracks_wizard/handlers/track_creation_handler.py

VehicleCreationHandler → src/cogs/vehicles_wizard/handlers/vehicle_creation_handler.py

Cada una definirá su propio STEP_MAP y validaciones personalizadas.

Ejemplo:

from src.cogs.wizards_general.handlers.wizard_handler_universal import WizardHandler
from src.utils.wizard_session import EventWizardSession

class EventCreationHandler(WizardHandler):
    def __init__(self, bot):
        step_map = {
            1: "step_schedule",
            2: "step_track",
            3: "step_vehicles",
            4: "step_settings",
            5: "step_rules",
            6: "step_finalize"
        }
        super().__init__(bot, EventWizardSession, step_map)

3.3 Agregar validaciones por paso (validate_step)

Descripción:
Cada paso debe validar la integridad de los datos antes de permitir avanzar.
Ejemplo: no se puede pasar de “vehículos” a “configuración” si no se ha seleccionado ningún vehículo.

Ejemplo de método:

async def validate_step(self, user_id: int, step_number: int) -> tuple[bool, str]:
    """Valida los datos requeridos del paso actual antes de avanzar."""
    data = self.session_class.get(user_id)
    if step_number == 3 and not data.get("vehicle_list_id") and not data.get("vehicle_text"):
        return False, "Debes seleccionar o escribir al menos un vehículo."
    return True, ""

3.4 Integrar control centralizado de errores

Descripción:
Agregar manejo seguro de excepciones en las funciones críticas (load_step, next_step, end_session).
Todos los errores deben ser reportados al usuario de forma controlada y al terminal mediante logs.

Ejemplo:

try:
    await self.load_step(interaction, next_step)
except Exception as e:
    print(f"[WIZARD ERROR] {e}")
    await interaction.followup.send(f"❌ Error interno al avanzar al paso {next_step}.", ephemeral=True)

3.5 Unificar navegación con navigation_view.py

Descripción:
Refactorizar WizardNavigationView para interactuar directamente con el WizardHandlerUniversal,
en lugar de importar pasos estáticos.

Ejemplo conceptual:

await handler.load_step(interaction, step_number)


El handler determinará el flujo de pasos y gestionará las sesiones globales.

3.6 Preparar hooks de persistencia

Descripción:
Agregar al handler funciones genéricas para manejar la persistencia de datos de wizard:

save_draft()

publish()

archive()
Cada wizard podrá sobrescribirlas según sus necesidades (por ejemplo, events_wizard con Database.events).

✅ Resultado esperado

Una infraestructura unificada capaz de gestionar múltiples asistentes (events, tracks, vehicles)
de manera homogénea, reduciendo la redundancia y facilitando el mantenimiento y escalabilidad.

-----------------------------------------------------

🧪 FASE 4 — Validación y Testing integral del sistema de Wizards
Objetivo general:

Verificar la estabilidad, coherencia y trazabilidad del nuevo sistema de asistentes (Wizards)
tras la integración del Wizard Handler Universal, garantizando compatibilidad entre módulos
y persistencia correcta de datos en la base de datos.

4.1 Testing unificado de WizardHandlerUniversal

Descripción:
Probar el flujo de creación completo de eventos, circuitos y vehículos usando el nuevo handler unificado.
Cada flujo debe:

Crear sesión correctamente.

Validar cada paso antes de avanzar.

Cerrar sesión sin errores al finalizar o cancelar.

Ejemplo de prueba manual:

# En Discord:
/create_event
➡️ Completar pasos 1–6
✅ Confirmar que cada avance muestra el encabezado correcto y mantiene el estado

4.2 Validación de sesión y estado (EventWizardSession)

Descripción:
Verificar que los datos temporales se guardan y eliminan correctamente.
Probar condiciones límite:

Usuario abre dos wizards simultáneamente → debe bloquear el segundo.

Cancelar wizard debe limpiar la sesión activa.

Reanudar wizard conserva los datos previos.

4.3 Integración con la base de datos (Database / EventDB)

Descripción:
Comprobar que los eventos, circuitos y vehículos creados desde el wizard se insertan correctamente.
Revisar las columnas de trazabilidad:

created_by, created_at

last_edited_by, last_edited_date

status, archived_at, published_at

Ejemplo de consulta de verificación:

SELECT event_id, title, status, created_by, created_at FROM events;

4.4 Testing de navegación (WizardNavigationView)

Descripción:
Verificar que los botones dinámicos (⬅️ Anterior, ➡️ Siguiente, 💾 Guardar, ❌ Cancelar)
funcionan correctamente según el paso:

El primero oculta el botón “Anterior”.

El último muestra “Guardar” o “Publicar”.

“Cancelar” elimina sesión sin errores.

4.5 Testing cruzado entre wizards

Descripción:
Comprobar interoperabilidad entre wizards:

tracks_wizard → events_wizard (selección de circuito).

vehicles_wizard → events_wizard (selección de vehículos).

Verificar que los datos referenciados (IDs, nombres) se actualizan dinámicamente.

Ejemplo:
Crear una lista de circuitos desde tracks_wizard y verificar que aparece como opción en /create_event.

4.6 Validación de persistencia y recuperación

Descripción:
Probar las funciones de carga y edición:

/load_saved_event recupera datos completos.

/edit_event actualiza sin duplicar entradas.

/delete_event elimina registros y limpia dependencias.

4.7 Testing de errores y manejo de excepciones

Descripción:
Simular errores comunes (por ejemplo, eliminar canal usado por un evento).
Verificar que los mensajes de error son legibles, consistentes y no interrumpen el flujo del bot.

4.8 Validación final de UX (experiencia de usuario)

Descripción:
Revisar la interfaz completa desde Discord:

Mensajes claros, coherentes y traducibles.

Estados efímeros correctamente aplicados.

Reutilización de estilos y emojis para coherencia visual.

✅ Resultado esperado:
Todos los asistentes (events_wizard, tracks_wizard, vehicles_wizard) operan correctamente bajo el WizardHandlerUniversal,
manteniendo sesiones independientes, navegación coherente y persistencia estable.
El sistema queda listo para la FASE 5 — Integración con el Dashboard Web.

-----------------------------------------------------

🌐 FASE 5 — Integración con Dashboard Web y API REST
Objetivo general:

Conectar el ecosistema de wizards de Discord con una interfaz web (dashboard)
gestionada por una API REST (FastAPI), permitiendo administración, visualización
y sincronización bidireccional de datos de eventos, usuarios, circuitos y vehículos.

5.1 Diseño e implementación de la API REST (FastAPI)

Descripción:
Crear un backend en src/api/ basado en FastAPI, responsable de servir y recibir datos entre Discord y el Dashboard Web.
El backend será responsable de:

Servir datos del bot (eventos, usuarios, configuraciones).

Recibir actualizaciones desde el Dashboard Web.

Gestionar autenticación y permisos de API (token o OAuth2).

Estructura propuesta:

src/api/
 ├── main.py               # punto de entrada FastAPI
 ├── routes/
 │    ├── events.py        # endpoints CRUD de eventos
 │    ├── tracks.py        # endpoints CRUD de circuitos
 │    ├── vehicles.py      # endpoints CRUD de vehículos
 │    └── auth.py          # autenticación básica / tokens
 ├── models/
 │    └── schemas.py       # Pydantic models
 └── utils/
      └── db_bridge.py     # puente con Database (aiosqlite)


Ejemplo de endpoint:

from fastapi import APIRouter
from database.db import Database

router = APIRouter(prefix="/events")

@router.get("/")
async def get_events():
    db = await Database.get_instance()
    events = await db.events.list_events()
    return {"events": events}

5.2 Autenticación y seguridad

Descripción:
Implementar un sistema de autenticación básica para el dashboard y la API.
Opciones recomendadas:

Token API secreto para sincronización del bot.

OAuth2 Discord para acceso de usuarios web (administradores y propietarios de servidores).

Ejemplo conceptual:

@app.middleware("http")
async def verify_api_key(request, call_next):
    token = request.headers.get("X-API-Key")
    if token != os.getenv("CRM_API_KEY"):
        return JSONResponse(status_code=403, content={"error": "Unauthorized"})
    return await call_next(request)

5.3 Sincronización bidireccional Bot ↔ API

Descripción:
Garantizar coherencia entre los datos del bot y el dashboard:

Cuando se crea o edita un evento desde Discord, se actualiza la API.

Cuando se edita o borra un evento desde la API, se notifica al bot.

Implementación sugerida (webhook + tareas asíncronas):

# FastAPI → Discord (actualización externa)
@app.post("/webhook/event_updated")
async def notify_bot(payload: dict):
    # enviar notificación al bot (ej. canal logs o admin)
    await bot.notify_admin(f"Evento '{payload['title']}' actualizado desde el dashboard.")

5.4 Dashboard Web (Frontend)

Descripción:
Crear un dashboard visual alojado en GitHub Pages o Vercel,
construido en React + TailwindCSS para visualizar y editar datos sincronizados.

Características previstas:

Listado y búsqueda de eventos, circuitos y vehículos.

Edición en línea de campos clave.

Sincronización automática con la API REST.

Sistema de login mediante OAuth2 de Discord.

Ejemplo de estructura frontend:

dashboard/
 ├── src/
 │    ├── components/
 │    │    ├── EventCard.tsx
 │    │    ├── TrackTable.tsx
 │    │    └── VehicleList.tsx
 │    ├── pages/
 │    │    ├── index.tsx
 │    │    ├── events.tsx
 │    │    └── admin.tsx
 │    ├── api/
 │    │    └── client.ts (fetch con Axios)
 │    └── utils/
 │         └── auth.ts (gestión de tokens)

5.5 Integración de estados del evento en el Dashboard

Descripción:
Mostrar visualmente los estados (draft, active, archived) y permitir acciones contextuales:

Editar / Publicar / Archivar / Eliminar

Fechas y usuarios de creación/modificación visibles en el panel.

Ejemplo:

<EventCard
  title="GT3 Endurance - Monza"
  status="active"
  created_by="JohnDoe"
  created_at="2025-11-07 18:30 UTC"
  onEdit={() => openEditor(event_id)}
/>

5.6 Comunicación segura entre Dashboard y Bot

Descripción:
Usar webhooks autenticados o API keys cifradas para comunicar ambos entornos.
Evitar llamadas directas al bot desde el frontend.

Esquema recomendado:

Dashboard  →  FastAPI (verifica token)  →  Base de datos compartida
                                       ↘  Discord Bot (solo notificación)

5.7 Pruebas de sincronización

Descripción:
Probar flujos de sincronización real:

Crear un evento desde Discord → visualizarlo en Dashboard.

Editar un evento desde el Dashboard → reflejar cambio en el bot.

Archivar o eliminar evento → actualizar estados automáticamente.

✅ Resultado esperado

Backend FastAPI operativo y conectado con la misma base de datos que el bot.

Dashboard visual accesible y sincronizado con los datos del bot.

Comunicación bidireccional segura entre Discord ↔ API ↔ Web.

Base para la FASE 6 — Escalabilidad y despliegue en producción (Fly.io + CI/CD).

-----------------------------------------------------

🚀 FASE 6 — Despliegue y CI/CD en Fly.io + GitHub Actions
Objetivo general:

Implementar un flujo de despliegue continuo (CI/CD) que permita mantener el bot, la API REST y el Dashboard Web actualizados automáticamente tras cada cambio en el repositorio, garantizando estabilidad, monitorización y disponibilidad 24/7 en producción.

6.1 Preparar el entorno de despliegue

Descripción:
Configurar el entorno de hosting principal en Fly.io para alojar tanto el bot de Discord como el backend FastAPI.
El dashboard (frontend) se alojará en GitHub Pages o Vercel.

Estructura sugerida del entorno:

fly.toml                  # Configuración principal de despliegue
src/
 ├── bot/                 # Código principal del bot
 ├── api/                 # API REST (FastAPI)
 └── database/            # Base de datos SQLite o futura PostgreSQL


Comando básico de inicialización:

flyctl launch --name crm-bot --region fra --no-deploy

6.2 Separación de servicios (multi-app deployment)

Descripción:
Configurar dos aplicaciones Fly.io independientes pero conectadas:

crm-bot → servicio principal del bot de Discord

crm-api → backend FastAPI
Ambas compartirán un volumen persistente para la base de datos (montado como /data).

Ejemplo de configuración parcial (fly.toml):

[env]
  DB_PATH = "/data/bot.db"
  BOT_TOKEN = "your_discord_token"
  CRM_API_KEY = "secure_api_key"

[mounts]
  source = "crm_data"
  destination = "/data"

6.3 Configuración de CI/CD con GitHub Actions

Descripción:
Crear un flujo automatizado que despliegue los cambios en Fly.io tras cada commit en la rama main.
El proceso incluirá:

Instalación de dependencias.

Ejecución de pruebas automatizadas.

Construcción de la imagen Docker.

Despliegue directo a Fly.io.

Archivo: .github/workflows/deploy.yml

name: Deploy to Fly.io
on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -q || echo "Skipping tests in MVP phase"

      - name: Deploy to Fly.io
        uses: superfly/flyctl-actions@1.5
        with:
          args: "deploy --remote-only"
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

6.4 Gestión de base de datos y persistencia

Descripción:
Configurar almacenamiento persistente (volumen crm_data) compartido entre crm-bot y crm-api.
Para futuras versiones, planificar migración de SQLite → PostgreSQL.

Comandos de gestión Fly.io:

flyctl volumes create crm_data --size 1 --region fra
flyctl volumes list


Plan futuro (PostgreSQL):

flyctl postgres create --name crm-db --region fra
flyctl postgres attach --app crm-bot crm-db

6.5 Monitorización y mantenimiento

Descripción:
Agregar monitorización básica para detectar fallos o caídas del bot/API.
Fly.io reinicia automáticamente las instancias, pero se recomienda incluir alertas adicionales.

Opciones recomendadas:

Fly.io Metrics Dashboard

UptimeRobot / BetterStack (para pings HTTP y latencia)

Logs centralizados en Discord vía canal #crm-logs

Ejemplo de webhook de logs:

async def log_to_discord(message: str):
    webhook_url = os.getenv("DISCORD_LOG_WEBHOOK")
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json={"content": message})

6.6 Despliegue del Dashboard Web

Descripción:
Publicar el frontend en GitHub Pages o Vercel con CI/CD automatizado.
El build debe ejecutarse automáticamente con cada push a la rama main.

Ejemplo (.github/workflows/deploy_dashboard.yml):

name: Deploy Dashboard
on:
  push:
    branches:
      - main
    paths:
      - 'dashboard/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Install dependencies
        run: npm ci
        working-directory: ./dashboard

      - name: Build project
        run: npm run build
        working-directory: ./dashboard

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dashboard/dist

6.7 Testing de despliegue

Descripción:
Validar el correcto funcionamiento de los tres servicios desplegados:

crm-bot responde a comandos /create_event.

crm-api devuelve datos en https://crm-api.fly.dev/events.

dashboard muestra datos sincronizados.

✅ Resultado esperado

Sistema completamente desplegado y funcional en Fly.io (bot + API).

Dashboard web sincronizado y actualizado automáticamente.

Flujos CI/CD activos en GitHub Actions.

Entorno de producción estable, persistente y auto-recuperable ante fallos.