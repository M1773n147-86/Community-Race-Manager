-- ===========================================================
-- Archivo: schema.sql
-- Ubicación: src/database/
--
-- Descripción:
-- Define la estructura principal de la base de datos del
-- Community Race Manager. Contiene las sentencias SQL
-- necesarias para crear todas las tablas e índices base
-- del sistema, incluyendo la gestión de listas de vehículos
-- y circuitos.
--
-- Este esquema puede ser ejecutado automáticamente desde
-- `db_init.py` o aplicado manualmente mediante herramientas
-- SQLite. Compatible con SQLite 3.x.
--
-- Incluye:
--   • vehicle_lists y vehicle_list_items
--   • track_lists y track_list_items
--
-- Cada tabla mantiene referencias con clave foránea para
-- garantizar la integridad y eliminación en cascada.
-- ===========================================================


-- ============================================
-- COMMUNITY RACE MANAGER — DATABASE SCHEMA
-- Versión revisada y actualizada (2025)
-- ============================================

PRAGMA foreign_keys = ON;

-- ============================================
-- TABLE: EVENTS
-- ============================================
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT DEFAULT 'standard',
    status TEXT DEFAULT 'draft',
    track_name TEXT,
    track_variant TEXT,
    track_description TEXT,
    vehicle_list_id INTEGER,
    vehicle_text TEXT,
    event_datetime_utc TEXT,
    publish_datetime_utc TEXT,
    timezone TEXT DEFAULT 'UTC',
    rules_text TEXT,
    rules_attachment_url TEXT,
    rules_discord_channel INTEGER,
    has_briefing INTEGER DEFAULT 0,
    briefing_offset_minutes INTEGER,
    briefing_channel_id INTEGER,
    briefing_type TEXT,
    allow_custom_skins INTEGER DEFAULT 0,
    skins_url TEXT,
    skins_filename TEXT,
    practice_time INTEGER DEFAULT 0,
    qualy_time INTEGER DEFAULT 0,
    race_time INTEGER DEFAULT 0,
    assists TEXT,
    weather TEXT,
    fuel_rate REAL DEFAULT 100,
    tire_wear_rate REAL DEFAULT 100,
    damage_multiplier REAL DEFAULT 100,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_edited_by INTEGER,
    last_edited_date TEXT,
    published_at TEXT,
    archived_at TEXT,
    archive_expires_at TEXT,
    FOREIGN KEY (vehicle_list_id) REFERENCES vehicle_lists(id)
);

CREATE INDEX IF NOT EXISTS idx_events_guild_status ON events (guild_id, status);
CREATE INDEX IF NOT EXISTS idx_events_title_ci ON events (title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_events_publish_at ON events (publish_datetime_utc);


-- ============================================
-- TABLE: AUTHORIZED ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS authorized_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    module TEXT DEFAULT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (guild_id, entity_id, entity_type, module)
);


-- ============================================
-- TABLE: SERVER SETTINGS
-- ============================================
CREATE TABLE IF NOT EXISTS server_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL UNIQUE,
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'es-ES',
    default_channel_id INTEGER,
    default_role_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- TABLE: VEHICLE LISTS
-- ============================================
CREATE TABLE IF NOT EXISTS vehicle_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicle_lists_name ON vehicle_lists (name);

CREATE TABLE IF NOT EXISTS vehicle_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    FOREIGN KEY (list_id) REFERENCES vehicle_lists (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vehicle_list_items_list_id ON vehicle_list_items (list_id);


-- ============================================
-- TABLE: TRACK LISTS
-- ============================================
CREATE TABLE IF NOT EXISTS track_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_track_lists_name ON track_lists (name);

CREATE TABLE IF NOT EXISTS track_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    track_name TEXT NOT NULL,
    FOREIGN KEY (list_id) REFERENCES track_lists (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_track_list_items_list_id ON track_list_items (list_id);
