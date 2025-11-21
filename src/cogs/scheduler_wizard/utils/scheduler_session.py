"""
Archivo: scheduler_session.py
Ubicación: src/cogs/scheduler_wizard/utils/

Descripción:
Gestor de sesiones temporales del Scheduler Wizard.
Mantiene datos efímeros por usuario mientras el asistente
de programación está activo. Su estructura y API son
coherentes con EventWizardSession.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# --------------------------------------------------------
# 🔹 Estructura interna de una sesión
# --------------------------------------------------------
@dataclass
class _SchedulerSessionData:
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# --------------------------------------------------------
# 🔹 API pública — coherencia con EventWizardSession
# --------------------------------------------------------
class SchedulerWizardSession:
    """
    API estática para manejar sesiones del Scheduler Wizard.

    Métodos equivalentes a EventWizardSession:
      - start(user_id, data=None)
      - update(user_id, key, value)
      - get(user_id)
      - delete(user_id) / end(user_id)
      - exists(user_id)
      - bulk_update(user_id, payload)
    """

    _sessions: Dict[int, _SchedulerSessionData] = {}
    _lock = asyncio.Lock()

    # -------- Helpers internos --------

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    async def _touch(cls, user_id: int) -> None:
        """Actualiza updated_at en la sesión del usuario."""
        sess = cls._sessions.get(user_id)
        if sess:
            sess.updated_at = cls._now_iso()

    # -------- API coherente con EventWizardSession --------

    @classmethod
    async def start(cls, user_id: int, data: Optional[Dict[str, Any]] = None) -> None:
        """Crea o reinicia la sesión con datos opcionales iniciales."""
        async with cls._lock:
            cls._sessions[user_id] = _SchedulerSessionData(data or {})

    @classmethod
    async def update(cls, user_id: int, key: str, value: Any) -> None:
        """Actualiza un campo dentro de los datos de sesión."""
        async with cls._lock:
            if user_id not in cls._sessions:
                cls._sessions[user_id] = _SchedulerSessionData({})
            cls._sessions[user_id].data[key] = value
            await cls._touch(user_id)

    @classmethod
    async def bulk_update(cls, user_id: int, payload: Dict[str, Any]) -> None:
        """Actualiza múltiples datos de sesión en bloque."""
        async with cls._lock:
            if user_id not in cls._sessions:
                cls._sessions[user_id] = _SchedulerSessionData({})
            cls._sessions[user_id].data.update(payload or {})
            await cls._touch(user_id)

    @classmethod
    def exists(cls, user_id: int) -> bool:
        """Indica si existe una sesión activa para el usuario."""
        return user_id in cls._sessions

    @classmethod
    def get(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Devuelve solo los datos de la sesión."""
        sess = cls._sessions.get(user_id)
        return dict(sess.data) if sess else None

    @classmethod
    async def delete(cls, user_id: int) -> None:
        """Elimina por completo la sesión."""
        async with cls._lock:
            cls._sessions.pop(user_id, None)

    # Alias semántico
    end = delete

    @classmethod
    def to_dict(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Devuelve datos + metadatos completos."""
        sess = cls._sessions.get(user_id)
        if not sess:
            return None
        return {
            "data": dict(sess.data),
            "created_at": sess.created_at,
            "updated_at": sess.updated_at,
        }
