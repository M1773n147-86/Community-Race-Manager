"""
Archivo: db.py
Ubicación: src/database/

Descripción:
Módulo central de gestión de base de datos del bot Community Race Manager.
Proporciona una interfaz asíncrona basada en SQLite mediante `aiosqlite`, 
implementando un patrón Singleton para mantener una única conexión activa.

Funciones principales:
- Inicialización y mantenimiento de tablas del sistema (eventos, circuitos, vehículos, participantes, etc.).
- Persistencia general de datos de la aplicación.
- Sistema de permisos internos (`authorized_entities`) que controla el acceso a los comandos 
  y módulos del bot según roles y usuarios autorizados.

Este módulo es utilizado por prácticamente todos los componentes del proyecto, 
sirviendo como capa de persistencia única y centralizada.
"""


import aiosqlite
import os
from typing import Optional


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "bot.db")

# Asegurarse de que la carpeta existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


class Database:
    _instance = None
    _conn: aiosqlite.Connection | None = None

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.events = None
        self.tracks = None

    @classmethod
    async def get_connection(cls) -> aiosqlite.Connection:
        """
        Mantiene una única conexión a SQLite por instancia del bot.
        """
        if cls._conn is None:
            cls._conn = await aiosqlite.connect(DB_PATH)
            await cls._conn.execute("PRAGMA foreign_keys = ON;")
        return cls._conn

    async def connect(self):
        """
        Establece una conexión activa con la base de datos SQLite.
        Incluye timestamp de apertura para diagnóstico y trazabilidad.
        """
        from datetime import datetime

        if hasattr(self, "_conn") and self._conn:
            print("ℹ️ [DB] Conexión ya activa. No se abrirá una nueva instancia.")
            return self._conn

        try:
            self._conn = await aiosqlite.connect(DB_PATH)
            await self._conn.execute("PRAGMA foreign_keys = ON;")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"🕒 [DB] Conexión establecida correctamente ({DB_PATH}) — {timestamp}")
            return self._conn

        except Exception as e:
            print(f"❌ [DB] Error al conectar con la base de datos: {e}")
            raise

    @classmethod
    async def get_instance(cls, db_path: str = DB_PATH):
        """
        Retorna la instancia Singleton del Database, creando conexión si no existe.
        """
        if cls._instance is None:
            cls._instance = cls(db_path)
            await cls._instance.init_db()

            # Inicializar submódulos
            try:
                from database.event_db import EventDB
                cls._instance.events = EventDB(cls._instance)
            except Exception as e:
                print(f"[DB WARNING] No se pudo cargar EventDB: {e}")
                cls._instance.events = None

            try:
                from database.track_db import TrackDB
                cls._instance.tracks = TrackDB(cls._instance)
                print("✅ [DB] Módulo TrackDB inicializado correctamente.")
            except Exception as e:
                print(f"[DB WARNING] No se pudo cargar TrackDB: {e}")
                cls._instance.tracks = None

            try:
                from database.server_settings_db import ServerSettingsDB
                cls._instance.server_settings = ServerSettingsDB(cls._instance)
                await cls._instance.server_settings.init_tables()
                print("✅ [DB] Módulo ServerSettingsDB inicializado correctamente.")
            except Exception as e:
                print(f"[DB WARNING] No se pudo cargar ServerSettingsDB: {e}")
                cls._instance.server_settings = None

        return cls._instance

    async def init_db(self):
        """
        Inicializa las tablas principales si no existen.
        """
        conn = await self.get_connection()

        # TABLA SERVERS – Configuración de cada servidor
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            guild_id            INTEGER PRIMARY KEY,
            language            TEXT DEFAULT 'en',
            event_creator_role  INTEGER
        );
        """)

        # TABLA EVENTOS – Datos principales del evento
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id                INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id                INTEGER NOT NULL,
            title                   TEXT NOT NULL,
            description             TEXT,
            -- Tipificado de evento para selección posterior en el scheduler
            -- standard | league | tournament | championship
            event_type              TEXT DEFAULT 'standard',

            -- Compat para estructuras legacy y campeonatos
            is_championship         INTEGER DEFAULT 0,
            championship_id         INTEGER,

            -- Publicación / estado
            is_published            INTEGER DEFAULT 0,
            status                  TEXT DEFAULT 'draft',          -- draft | scheduled | active | archived | closed
            timezone                TEXT,

            -- Fechas clave
            event_datetime_utc      TEXT,                          -- fecha/hora del evento
            publish_datetime_utc    TEXT,                          -- (opcional) si se programa publicación
            registration_open_utc   TEXT,                          -- NUEVO: apertura de inscripciones
            registration_close_utc  TEXT,                          -- (opcional) cierre de inscripciones

            -- Logística
            max_drivers             INTEGER,
            broadcast_slots         INTEGER DEFAULT 0,

            -- Reglas
            allow_custom_skins      INTEGER DEFAULT 0,
            rules_text              TEXT,
            rules_attachment_url    TEXT,

            -- Canales relacionados
            publish_channel_id      INTEGER,
            participants_channel_id INTEGER,

            -- Trazabilidad
            created_by              INTEGER NOT NULL,
            created_at              TEXT NOT NULL,
            last_edited_by          INTEGER,
            last_edited_date        TEXT,
            published_at            TEXT,
            archived_at             TEXT,
            archive_expires_at      TEXT,

            -- Relación básica con servers
            FOREIGN KEY (guild_id) REFERENCES servers(guild_id)
        );
        """)

        # Índices adicionales para rendimiento
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_archive_expires_at ON events(archive_expires_at);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_guild_id ON events(guild_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_title ON events(title);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_publish_dt ON events(publish_datetime_utc);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_event_dt ON events(event_datetime_utc);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_reg_open_dt ON events(registration_open_utc);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);")

        # TABLA PARTICIPANTES – Inscripciones al evento
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            user_id         INTEGER NOT NULL,
            event_id        INTEGER NOT NULL,
            steam_id        TEXT,
            name            TEXT,
            team_name       TEXT,
            car_model       TEXT,
            timezone        TEXT,
            has_custom_skin INTEGER DEFAULT 0,
            attempts        INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'pending',
            PRIMARY KEY (user_id, event_id),
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        );
        """)

        # TABLA TRACKS – Circuitos disponibles por servidor
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id          INTEGER NOT NULL,
            name              TEXT NOT NULL,
            layout            TEXT,
            pit_slots         INTEGER NOT NULL,
            broadcast_slots   INTEGER DEFAULT 0,
            details           TEXT,
            image_path        TEXT,
            created_at        TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # TABLA VEHICLE_LISTS – Listas de coches definidas por el usuario
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_lists (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            description     TEXT,
            created_by      INTEGER,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # TABLA VEHICLE_LIST_ITEMS – Vehículos asociados a cada lista
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_list_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id     INTEGER NOT NULL,
            model_name  TEXT NOT NULL,
            FOREIGN KEY (list_id) REFERENCES vehicle_lists(id)
        );
        """)

        await conn.commit()

        # ==============================================================
        # SISTEMA DE AUTORIZACIONES UNIFICADO (Usuarios, Roles y Módulos)
        # ==============================================================

    async def _ensure_authorized_table(self):
        """
        Crea la tabla de entidades autorizadas si no existe.
        Incluye control por módulo ('module_name'), usuario o rol.
        También aplica migración automática si la columna aún no existe.
        """
        conn = await self.get_connection()

        # Crear tabla si no existe
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS authorized_entities (
            guild_id     INTEGER NOT NULL,
            module_name  TEXT DEFAULT 'global',
            entity_id    INTEGER NOT NULL,
            entity_type  TEXT CHECK(entity_type IN ('user','role')) NOT NULL,
            UNIQUE(guild_id, module_name, entity_id, entity_type)
        );
        """)

        # 🔧 Migración automática para bases de datos antiguas (añade columna module_name si falta)
        try:
            cur = await conn.execute("PRAGMA table_info(authorized_entities);")
            columns = [row[1] for row in await cur.fetchall()]
            if "module_name" not in columns:
                await conn.execute("ALTER TABLE authorized_entities ADD COLUMN module_name TEXT DEFAULT 'global';")
                print(
                    "🛠️ [DB] Migración aplicada: columna 'module_name' añadida a authorized_entities.")
        except Exception as e:
            print(
                f"⚠️ [DB] Error durante la comprobación/migración de authorized_entities: {e}")

        await conn.commit()

    async def add_authorized_entity(
        self,
        guild_id: int,
        entity_id: int,
        entity_type: str,
        module_name: str = "global"
    ):
        """
        Registra una entidad (usuario o rol) como autorizada.
        Puede aplicarse globalmente o a un módulo específico.
        """
        await self._ensure_authorized_table()
        conn = await self.get_connection()
        await conn.execute("""
            INSERT OR IGNORE INTO authorized_entities (guild_id, module_name, entity_id, entity_type)
            VALUES (?, ?, ?, ?);
        """, (guild_id, module_name, entity_id, entity_type))
        await conn.commit()

    async def remove_authorized_entity(
        self,
        guild_id: int,
        entity_id: int,
        entity_type: str,
        module_name: str = "global"
    ):
        """
        Elimina una entidad (usuario o rol) de la lista de autorizaciones.
        Si el módulo no se especifica, elimina solo la autorización global.
        """
        await self._ensure_authorized_table()
        conn = await self.get_connection()
        await conn.execute("""
            DELETE FROM authorized_entities
            WHERE guild_id = ? AND module_name = ? AND entity_id = ? AND entity_type = ?;
        """, (guild_id, module_name, entity_id, entity_type))
        await conn.commit()

    async def is_authorized(self, guild_id: int, module: str, user) -> bool:
        """
        Verifica si un usuario o alguno de sus roles está autorizado
        para el módulo especificado o globalmente.

        Retorna True si:
        - El usuario es el propietario del servidor.
        - Está autorizado directamente para el módulo o de forma global.
        - Alguno de sus roles tiene permiso global o específico.
        """
        if not hasattr(user, "id") or not hasattr(user, "roles"):
            return False

        await self._ensure_authorized_table()
        conn = await self.get_connection()

        # --- Verificar usuario directamente ---
        async with conn.execute("""
            SELECT 1 FROM authorized_entities
            WHERE guild_id = ? 
              AND module_name IN (?, 'global')
              AND entity_id = ? 
              AND entity_type = 'user';
        """, (guild_id, module, user.id)) as cursor:
            if await cursor.fetchone():
                return True

        # --- Verificar roles ---
        role_ids = [r.id for r in getattr(user, "roles", [])]
        if not role_ids:
            return False

        placeholders = ",".join("?" * len(role_ids))
        query = f"""
            SELECT 1 FROM authorized_entities
            WHERE guild_id = ?
              AND module_name IN (?, 'global')
              AND entity_type = 'role'
              AND entity_id IN ({placeholders});
        """
        async with conn.execute(query, [guild_id, module, *role_ids]) as cursor:
            return bool(await cursor.fetchone())

    async def safe_close(self):
        """
        Cierra la conexión activa con la base de datos SQLite de forma segura.
        Incluye timestamp y gestión de errores detallada.
        """
        from datetime import datetime

        if hasattr(self, "_conn") and self._conn:
            try:
                await self._conn.close()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"🔒 [DB] Conexión cerrada correctamente — {timestamp}")
                self._conn = None
            except Exception as e:
                print(f"⚠️ [DB] Error al cerrar la base de datos: {e}")
        else:
            print(
                "ℹ️ [DB] No había conexión de base de datos activa al intentar cerrar.")

    async def purge_archived_events(self):
        """
        Elimina eventos archivados cuya fecha de caducidad haya expirado.
        Ejecutado bajo demanda al listar o iniciar un evento.
        """
        conn = await self.get_connection()
        try:
            await conn.execute("""
                DELETE FROM events
                WHERE status = 'archived'
                AND archive_expires_at IS NOT NULL
                AND datetime(archive_expires_at) <= datetime('now');
            """)
            await conn.commit()
            print("🧹 [DB] Eventos archivados expirados eliminados correctamente.")
        except Exception as e:
            print(f"⚠️ [DB] Error al purgar eventos archivados: {e}")
