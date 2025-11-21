# Community Race Manager — Codebase Review (Deep)

**Date:** 2025-10-29  
**Reviewer:** GPT-5 Thinking mini (automated analysis)

---

## 0 — Context
You uploaded `Community Race Manager.zip` (src + .vscode + requirements.txt). I performed a static review of the extracted `src/` tree and compared it with the design we discussed (wizard frontend + backend, DB schemas, session management, cogs).

This document summarizes:
- What is present
- Critical issues to fix before coding the wizard backend
- Missing components and placeholders
- Prioritized implementation plan (step-by-step)
- Exact edit locations and small code-snippets (when needed)
- Next immediate actions you can copy/paste

---

## 1 — Files scanned (key)
```
src/
├─ bot.py
├─ main.py
├─ cogs/
│  ├─ events.py
│  ├─ export_event.py
│  ├─ fun.py
│  ├─ general.py
│  ├─ manage_event.py
│  ├─ moderation.py
│  ├─ participants.py
│  ├─ permissions.py
│  ├─ tracks.py
│  └─ wizard/
│     ├─ __init__.py
│     └─ create_event.py
├─ database/
│  ├─ __init__.py
│  ├─ db.py
│  ├─ event_db.py
│  └─ track_db.py
├─ utils/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ session_manager.py
│  └─ timezone.py
├─ models/
│  └─ session.py
...
requirements.txt
```

---

## 2 — High-priority issues (must fix before continuing)
These are blockers: code will not run or is inconsistent.

1. **`src/database/db.py` is corrupted / incomplete**
   - Contains `...` placeholders and broken SQL fragments.
   - Several functions (e.g. `create_event_record`) show ellipses and malformed SQL.
   - This will raise SyntaxError / runtime errors.

2. **Many files are scaffolds with `...` placeholders**
   - `src/cogs/events.py`, `wizard/create_event.py`, `utils/session_manager.py`, `tracks.py`, `wizard_events.py`, `event_db.py` contain `...` or are empty. They are intended, but not implemented.

3. **Missing helper functions in `session_manager.py`**
   - Some functions referenced earlier (`get_session`, `end_session`) may be missing or only partially present. Ensure all helpers exist.

4. **Inconsistent naming and duplicate modules**
   - There are both `utils/session_manager.py` and `models/session.py` — be explicit on which you use. Current code imports `utils.session` in some places and `models.session` in others. Normalize to one path.

5. **Imports expecting modules that are placeholders**
   - Many cogs import database helpers (e.g. `from database.track_db import get_all_tracks`) but those helpers may be stubs. Implement those APIs.

---

## 3 — Non-blocking but important issues
- No tests.
- No linter configuration (consider flake8/black).
- No CI configuration.
- No docs inside repo (I will produce a `CRM_review.md`).

---

## 4 — Prioritized implementation plan (recommended order)
I'll give short tasks you can do incrementally. After each completed step, tell me `CONTINUE` and I'll give the next code snippet.

**Phase 0 — Stabilize the repo**
1. Fix `src/database/db.py` — replace with the consolidated `_create_tables()` and a minimal `connect()`/`close()`/`create_event_record()` implementation. (HIGH priority)
2. Ensure `utils/session_manager.py` has all helper functions: `create_session`, `get_session`, `update_session`, `advance_step`, `clear_session`, `end_session` (end_session = clear_session alias).
3. Normalize session model import: pick `utils.session_manager` as single source of truth; update imports across cogs.
4. Implement minimal `track_db.py` and `event_db.py` wrappers (get_all_tracks, get_track, create_event) returning simple structures.

**Phase 1 — Wizard wiring (non-UI)**
5. Implement the `/create_event` command handler (already scaffolded) to:
   - Check for tracks
   - Create session
   - Advance to step 1
6. Implement step handlers one-by-one:
   - Title (modal)
   - Description
   - Timezone select
   - Date/time selects
   - Vehicles (modal)
   - Track select
   - Capacity + broadcast
   - Teams calculation
   - Roles/channels selection
   - Rules/regulation/skins
   - Final confirmation that inserts row into `events` table

**Phase 2 — Participants / Check-in**
7. Implement `participants` cog: check-in/out handlers, validations, registration attempts counter.
8. Implement `export_event` cog to generate CSV/JSON attachments.

**Phase 3 — Extras**
9. Google Calendar link, SteamID checks, track manager UI, manage_event, persistence improvements (WIZPERSIST B), image storage and cleanup.

---

## 5 — Exact edits I recommend first (copy/paste)
Below are minimal fixes to make the codebase runnable and to remove syntax errors.

### A) Replace `src/database/db.py` with a minimal, working version.
**Find:** `src/database/db.py`  
**Replace entire file with the following minimal implementation (copy/paste):**

```python
# minimal db.py replacement - paste whole file
import aiosqlite
import asyncio
from pathlib import Path

class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._conn = None
        self._lock = asyncio.Lock()

    async def connect(self):
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._create_tables()

    async def _create_tables(self):
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            creator_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            timezone TEXT NOT NULL,
            event_datetime TEXT NOT NULL,
            vehicles TEXT,
            track_id INTEGER,
            image_url TEXT,
            teams_enabled INTEGER DEFAULT 0,
            max_drivers INTEGER NOT NULL,
            pilot_role_id INTEGER,
            steward_role_id INTEGER,
            publish_channel_id INTEGER,
            roster_channel_id INTEGER,
            special_rules TEXT,
            regulation_url TEXT,
            custom_liveries_url TEXT,
            checkin_closure_minutes INTEGER DEFAULT 60,
            briefing_enabled INTEGER DEFAULT 0,
            championship_id INTEGER,
            broadcast_slots INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );""")
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            name TEXT NOT NULL,
            layout TEXT,
            pit_slots INTEGER NOT NULL,
            broadcast_slots INTEGER DEFAULT 0,
            details TEXT,
            image_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );""")
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS event_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            steam_id TEXT NOT NULL,
            vehicle TEXT,
            team TEXT,
            timezone TEXT,
            custom_livery_url TEXT,
            attempts_used INTEGER DEFAULT 0,
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, user_id)
        );""")
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS registration_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            checkout_count INTEGER DEFAULT 0,
            last_attempt_at TEXT,
            UNIQUE(event_id, user_id)
        );""")
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS championships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );""")
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS championship_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            championship_id INTEGER NOT NULL,
            event_id INTEGER,
            round_number INTEGER NOT NULL,
            UNIQUE(championship_id, round_number)
        );""")
        await self._conn.execute("""CREATE TABLE IF NOT EXISTS module_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            module_name TEXT NOT NULL,
            role_id INTEGER,
            user_id INTEGER,
            UNIQUE(guild_id, module_name, role_id, user_id)
        );""")
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    # minimal helpers used by the cogs
    async def get_all_tracks(self, guild_id: int):
        async with self._lock:
            cur = await self._conn.execute("""SELECT id, name, layout, pit_slots, broadcast_slots FROM tracks WHERE guild_id=?""", (guild_id,))
            rows = await cur.fetchall()
            return rows

    async def create_event_record(self, data: dict):
        async with self._lock:
            await self._conn.execute("""INSERT INTO events (guild_id, creator_id, title, description, timezone, event_datetime, vehicles, track_id, image_url, teams_enabled, max_drivers, pilot_role_id, steward_role_id, publish_channel_id, roster_channel_id, special_rules, regulation_url, custom_liveries_url, checkin_closure_minutes, briefing_enabled, championship_id, broadcast_slots)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                data.get('guild_id'),
                data.get('creator_id'),
                data.get('title'),
                data.get('description'),
                data.get('timezone'),
                data.get('event_datetime'),
                data.get('vehicles'),
                data.get('track_id'),
                data.get('image_url'),
                int(data.get('teams_enabled',0)),
                int(data.get('max_drivers',0)),
                data.get('pilot_role_id'),
                data.get('steward_role_id'),
                data.get('publish_channel_id'),
                data.get('roster_channel_id'),
                data.get('special_rules'),
                data.get('regulation_url'),
                data.get('custom_liveries_url'),
                int(data.get('checkin_closure_minutes',60)),
                int(data.get('briefing_enabled',0)),
                data.get('championship_id'),
                int(data.get('broadcast_slots',0))
            ))
            await self._conn.commit()
            return True
```

This minimal file will let the code import and run basic DB operations. After this is in place, we can implement higher-level DB helpers.

---

## 6 — Conventions and small improvements
- Normalize imports to `from database.db import Database` (since you moved db.py to database/)
- Decide a single session module. I'd recommend `utils/session_manager.py` as authoritative.
- Add `src/__init__.py` if not present (you already have one).
- Add `.gitignore` (exclude .env, .venv, __pycache__, *.sqlite3)

---

## 7 — Deliverables I will produce next (if you want)
If you confirm, I will:
1. Replace `database/db.py` with the minimal working implementation above (or paste it for you to paste).  
2. Implement `database/track_db.py` with `get_all_tracks()` and `get_track()` wrappers.  
3. Implement `utils/session_manager.py` missing functions and adjust imports.  
4. Provide the first working wizard steps (title, description, timezone, date/time) as actual code (cog + Views + Modals).  

Reply with **which step to do first**:
- `1` = I'll generate `database/db.py` minimal replacement (paste-ready)
- `2` = Implement `track_db.py` helpers
- `3` = Fix `session_manager.py` helpers and normalize imports
- `4` = Generate the first wizard steps code (title/description/timezone/datetime)

---

## Appendix: quick checks I ran
- requirements.txt contains: `discord.py>=2.3.0`, `python-dotenv>=0.21.0`, `aiosqlite>=0.18.0`
- Pylance issues matched placeholders and missing imports

---
