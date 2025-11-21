"""
Archivo: wizard_session.py
Ubicación: src/utils/

Descripción:
Gestor de sesiones temporales para el Events Wizard.
Mantiene datos efímeros por usuario mientras completan el asistente
de creación de eventos.

Su API es coherente con SchedulerWizardSession, con métodos:
  - start(user_id, data=None)
  - update(user_id, key, value)
  - bulk_update(user_id, payload)
  - get(user_id)
  - next_step(user_id)
  - exists(user_id)
  - delete(user_id) / end(user_id)
  - to_dict(user_id)

Esta sesión se mantiene in-memory y se destruye cuando el wizard finaliza.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# --------------------------------------------------------
# 🔹 Estructura interna
# --------------------------------------------------------
@dataclass
class _EventWizardSessionData:
    data: Dict[str, Any] = field(default_factory=dict)
    step: int = 1
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# --------------------------------------------------------
# 🔹 API principal del Events Wizard
# --------------------------------------------------------
class EventWizardSession:
    """
    Sistema estático de manejo de sesiones del Events Wizard.
    Coherente con SchedulerWizardSession, pero con soporte adicional para `step`.
    """

    _sessions: Dict[int, _EventWizardSessionData] = {}
    _lock = asyncio.Lock()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    async def _touch(cls, user_id: int) -> None:
        """Actualiza updated_at."""
        sess = cls._sessions.get(user_id)
        if sess:
            sess.updated_at = cls._now_iso()

    # ---------- API pública ----------

    @classmethod
    async def start(cls, user_id: int, initial: Optional[Dict[str, Any]] = None) -> None:
        """Crea o reinicia una sesión del wizard."""
        async with cls._lock:
            cls._sessions[user_id] = _EventWizardSessionData(
                data=initial or {},
                step=initial.get("step", 1) if initial else 1
            )

    @classmethod
    def exists(cls, user_id: int) -> bool:
        return user_id in cls._sessions

    @classmethod
    def get(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Devuelve solo los datos almacenados del wizard."""
        sess = cls._sessions.get(user_id)
        return dict(sess.data) if sess else None

    @classmethod
    async def update(cls, user_id: int, key: str, value: Any) -> None:
        """Actualiza un valor dentro de la sesión."""
        async with cls._lock:
            sess = cls._sessions.get(user_id)
            if not sess:
                sess = _EventWizardSessionData()
                cls._sessions[user_id] = sess
            sess.data[key] = value
            await cls._touch(user_id)

    @classmethod
    async def bulk_update(cls, user_id: int, payload: Dict[str, Any]) -> None:
        """Actualiza múltiples valores simultáneamente."""
        async with cls._lock:
            sess = cls._sessions.get(user_id)
            if not sess:
                sess = _EventWizardSessionData()
                cls._sessions[user_id] = sess
            sess.data.update(payload or {})
            await cls._touch(user_id)

    @classmethod
    async def next_step(cls, user_id: int) -> None:
        """Incrementa el número de paso del wizard."""
        async with cls._lock:
            sess = cls._sessions.get(user_id)
            if sess:
                sess.step += 1
                await cls._touch(user_id)

    @classmethod
    async def delete(cls, user_id: int) -> None:
        """Elimina por completo la sesión."""
        async with cls._lock:
            cls._sessions.pop(user_id, None)

    # alias semántico
    end = delete

    @classmethod
    def to_dict(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Devuelve la sesión con metadatos completos."""
        sess = cls._sessions.get(user_id)
        if not sess:
            return None
        return {
            "data": dict(sess.data),
            "step": sess.step,
            "created_at": sess.created_at,
            "updated_at": sess.updated_at,
        }
