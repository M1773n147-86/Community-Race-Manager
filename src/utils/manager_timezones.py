"""
Archivo: manager_timezones.py
Ubicación: src/utils/

Descripción:
Contiene las utilidades centrales de gestión de zonas horarias utilizadas por
los wizards de Community Race Manager. Define las regiones disponibles, sus
zonas horarias asociadas y helpers para conversión y validación de fechas.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --------------------------------------------------------
# 🌍 REGIONES PRINCIPALES (en español)
# --------------------------------------------------------
REGIONS = {
    "Europa": "🌍 Europa",
    "América del Norte": "🌎 América del Norte",
    "América del Sur": "🌎 América del Sur",
    "Asia": "🌏 Asia",
    "Oceanía": "🌊 Oceanía",
    "África": "🌍 África",
    "Medio Oriente": "🕌 Medio Oriente",
    "Pacífico": "🏝️ Pacífico",
}

# --------------------------------------------------------
# 🕒 ZONAS HORARIAS SIMPLIFICADAS POR REGIÓN
# --------------------------------------------------------
ZONES_BY_REGION = {
    "Europa": [
        ("UTC−01:00", "Azores", "Atlantic/Azores"),
        ("UTC±00:00", "Londres, Lisboa", "Europe/London"),
        ("UTC+01:00", "Bruselas, Copenhague, Madrid, París", "Europe/Madrid"),
        ("UTC+02:00", "Atenas, Bucarest, Helsinki", "Europe/Helsinki"),
        ("UTC+03:00", "Moscú, Estambul, Minsk", "Europe/Moscow"),
    ],
    "América del Norte": [
        ("UTC−08:00", "Los Ángeles, Vancouver", "America/Los_Angeles"),
        ("UTC−07:00", "Denver, Calgary", "America/Denver"),
        ("UTC−06:00", "Chicago, Ciudad de México", "America/Mexico_City"),
        ("UTC−05:00", "Nueva York, Toronto, Bogotá", "America/New_York"),
        ("UTC−04:00", "Santo Domingo, Caracas", "America/Caracas"),
    ],
    "América del Sur": [
        ("UTC−05:00", "Lima, Quito", "America/Lima"),
        ("UTC−04:00", "La Paz, Caracas", "America/La_Paz"),
        ("UTC−03:00", "Buenos Aires, Montevideo, São Paulo", "America/Sao_Paulo"),
    ],
    "Asia": [
        ("UTC+05:30", "Nueva Delhi, Colombo", "Asia/Kolkata"),
        ("UTC+07:00", "Bangkok, Yakarta", "Asia/Bangkok"),
        ("UTC+08:00", "Beijing, Singapur, Manila", "Asia/Singapore"),
        ("UTC+09:00", "Seúl, Tokio", "Asia/Tokyo"),
        ("UTC+10:00", "Vladivostok, Yakutsk", "Asia/Vladivostok"),
    ],
    "Oceanía": [
        ("UTC+10:00", "Sídney, Melbourne", "Australia/Sydney"),
        ("UTC+12:00", "Auckland, Suva", "Pacific/Auckland"),
    ],
    "África": [
        ("UTC±00:00", "Dakar, Casablanca", "Africa/Casablanca"),
        ("UTC+01:00", "Argel, Túnez, Lagos", "Africa/Algiers"),
        ("UTC+02:00", "El Cairo, Johannesburgo", "Africa/Johannesburg"),
    ],
    "Medio Oriente": [
        ("UTC+02:00", "Jerusalén, Gaza", "Asia/Jerusalem"),
        ("UTC+03:00", "Riad, Bagdad, Kuwait", "Asia/Riyadh"),
        ("UTC+04:00", "Dubái, Abu Dabi, Muscat", "Asia/Dubai"),
    ],
    "Pacífico": [
        ("UTC−10:00", "Honolulu, Papeete", "Pacific/Honolulu"),
        ("UTC+10:00", "Guam, Port Moresby", "Pacific/Guam"),
        ("UTC+12:00", "Islas Marshall, Fiji", "Pacific/Fiji"),
    ],
}

# --------------------------------------------------------
# ⚙️ FUNCIONES DE UTILIDAD
# --------------------------------------------------------


def list_regions() -> list[str]:
    """Devuelve la lista de nombres de regiones disponibles."""
    return list(REGIONS.keys())


def list_timezones_by_region(region: str) -> list[tuple[str, str, str]]:
    """Devuelve las zonas horarias de una región concreta."""
    return ZONES_BY_REGION.get(region, [])


def convert_to_utc(dt_str: str, tz_name: str) -> str:
    """
    Convierte una fecha/hora local (AAAA-MM-DD HH:MM) a UTC (ISO8601).
    """
    try:
        local_zone = ZoneInfo(tz_name)
        local_dt = datetime.strptime(
            dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_zone)
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
        return utc_dt.isoformat()
    except Exception as e:
        raise ValueError(f"❌ Error al convertir fecha: {e}")


def validate_future_datetime(utc_iso: str, min_offset_minutes: int = 0) -> bool:
    """
    Valida que una fecha UTC sea futura respecto a la actual.
    """
    now_utc = datetime.now(ZoneInfo("UTC"))
    try:
        dt = datetime.fromisoformat(utc_iso)
    except Exception:
        return False
    return dt > (now_utc + timedelta(minutes=min_offset_minutes))


# --------------------------------------------------------
# 📦 EXPORTS
# --------------------------------------------------------
__all__ = [
    "REGIONS",
    "ZONES_BY_REGION",
    "list_regions",
    "list_timezones_by_region",
    "convert_to_utc",
    "validate_future_datetime",
]
