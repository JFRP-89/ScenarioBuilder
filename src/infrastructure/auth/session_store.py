"""Server-side session store — in-memory + file-backed implementation.

Each session holds:
- ``session_id``: cryptographically random token (32 bytes hex = 256 bits)
- ``actor_id``: authenticated username
- ``created_at``: session creation timestamp
- ``last_seen_at``: updated on every request (idle timeout)
- ``reauth_at``: timestamp of last re-authentication (for sensitive ops)
- ``csrf_token``: per-session CSRF token

Expiration policy:
- **Idle timeout**: ``SESSION_IDLE_MINUTES`` (default 15) since ``last_seen_at``.
- **Max lifetime**: ``SESSION_MAX_HOURS`` (default 12) since ``created_at``.

Persistence:
- Sessions are saved to a JSON file after every mutation so they survive
  server restarts.  The file path defaults to ``.sessions.json`` in the
  project root and can be overridden via ``SESSION_STORE_PATH``.

Thread-safe via ``threading.Lock``.
"""

from __future__ import annotations

import json
import os
import pathlib
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import TypedDict

# ── Configuration (overridable via env) ──────────────────────────────────────
SESSION_IDLE_MINUTES = int(os.environ.get("SESSION_IDLE_MINUTES", "15"))
SESSION_MAX_HOURS = int(os.environ.get("SESSION_MAX_HOURS", "12"))
REAUTH_WINDOW_MINUTES = int(os.environ.get("REAUTH_WINDOW_MINUTES", "10"))

_SESSION_ID_BYTES = 32  # 256-bit random

_DEFAULT_STORE_PATH = str(
    pathlib.Path(__file__).resolve().parent.parent.parent.parent / ".sessions.json"
)
_STORE_PATH = os.environ.get("SESSION_STORE_PATH", _DEFAULT_STORE_PATH)


# ── Types ────────────────────────────────────────────────────────────────────
class SessionRecord(TypedDict):
    session_id: str
    actor_id: str
    created_at: datetime
    last_seen_at: datetime
    reauth_at: datetime | None
    csrf_token: str


# ── In-memory store ──────────────────────────────────────────────────────────
_lock = threading.Lock()
_SESSIONS: dict[str, SessionRecord] = {}


# ── File persistence helpers ─────────────────────────────────────────────────


def _save_to_disk() -> None:
    """Persist ``_SESSIONS`` to a JSON file.  **Must be called with _lock held.**"""
    try:
        data: dict[str, dict[str, str | None]] = {}
        for sid, rec in _SESSIONS.items():
            data[sid] = {
                "session_id": rec["session_id"],
                "actor_id": rec["actor_id"],
                "created_at": rec["created_at"].isoformat(),
                "last_seen_at": rec["last_seen_at"].isoformat(),
                "reauth_at": (
                    rec["reauth_at"].isoformat() if rec["reauth_at"] else None
                ),
                "csrf_token": rec["csrf_token"],
            }
        pathlib.Path(_STORE_PATH).write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # best-effort — in-memory store still works


def _load_from_disk() -> None:
    """Load ``_SESSIONS`` from a JSON file.  **Must be called with _lock held.**"""
    try:
        path = pathlib.Path(_STORE_PATH)
        if not path.exists():
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        for sid, rd in raw.items():
            _SESSIONS[sid] = SessionRecord(
                session_id=rd["session_id"],
                actor_id=rd["actor_id"],
                created_at=datetime.fromisoformat(rd["created_at"]),
                last_seen_at=datetime.fromisoformat(rd["last_seen_at"]),
                reauth_at=(
                    datetime.fromisoformat(rd["reauth_at"])
                    if rd.get("reauth_at")
                    else None
                ),
                csrf_token=rd["csrf_token"],
            )
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        pass  # best-effort — start with empty store


# Load persisted sessions on module init
with _lock:
    _load_from_disk()


def _generate_session_id() -> str:
    """Generate a cryptographically secure session ID (hex, 64 chars)."""
    return secrets.token_hex(_SESSION_ID_BYTES)


def _generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token (hex, 64 chars)."""
    return secrets.token_hex(32)


def _now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


# ── Public API ───────────────────────────────────────────────────────────────


def create_session(actor_id: str) -> SessionRecord:
    """Create a new session for *actor_id* and return the record.

    Session ID rotation: always generates a fresh random ID.
    """
    now = _now()
    session_id = _generate_session_id()
    record = SessionRecord(
        session_id=session_id,
        actor_id=actor_id,
        created_at=now,
        last_seen_at=now,
        reauth_at=None,
        csrf_token=_generate_csrf_token(),
    )
    with _lock:
        _SESSIONS[session_id] = record
        _save_to_disk()
    return record


def get_session(session_id: str) -> SessionRecord | None:
    """Retrieve a session if it exists and is not expired.

    Returns:
        The session record, or None if missing/expired.
    Side effects:
        - Removes expired sessions from the store.
        - Updates ``last_seen_at`` on valid sessions.
    """
    with _lock:
        record = _SESSIONS.get(session_id)
        if record is None:
            return None

        now = _now()

        # Check max lifetime
        max_delta = timedelta(hours=SESSION_MAX_HOURS)
        if now - record["created_at"] > max_delta:
            _SESSIONS.pop(session_id, None)
            _save_to_disk()
            return None

        # Check idle timeout
        idle_delta = timedelta(minutes=SESSION_IDLE_MINUTES)
        if now - record["last_seen_at"] > idle_delta:
            _SESSIONS.pop(session_id, None)
            _save_to_disk()
            return None

        # Touch the session
        record["last_seen_at"] = now
        _save_to_disk()
        return record


def invalidate_session(session_id: str) -> bool:
    """Remove a session from the store. Return True if it existed."""
    with _lock:
        removed = _SESSIONS.pop(session_id, None) is not None
        if removed:
            _save_to_disk()
        return removed


def mark_reauth(session_id: str) -> bool:
    """Mark a session as recently re-authenticated.

    Returns True if the session was found and updated.
    """
    with _lock:
        record = _SESSIONS.get(session_id)
        if record is None:
            return False
        record["reauth_at"] = _now()
        _save_to_disk()
        return True


def rotate_session_id(old_session_id: str) -> SessionRecord | None:
    """Rotate the session ID (session fixation prevention).

    Creates a new session_id while preserving the session data.
    Invalidates the old session_id.

    Returns:
        The updated session record with new session_id, or None.
    """
    with _lock:
        old_record = _SESSIONS.pop(old_session_id, None)
        if old_record is None:
            return None

        new_id = _generate_session_id()
        new_csrf = _generate_csrf_token()
        new_record = SessionRecord(
            session_id=new_id,
            actor_id=old_record["actor_id"],
            created_at=old_record["created_at"],
            last_seen_at=_now(),
            reauth_at=old_record["reauth_at"],
            csrf_token=new_csrf,
        )
        _SESSIONS[new_id] = new_record
        _save_to_disk()
        return new_record


def is_recently_reauthed(session_id: str) -> bool:
    """Return True if the session was re-authenticated within the reauth window."""
    with _lock:
        record = _SESSIONS.get(session_id)
        if record is None:
            return False
        reauth_at = record.get("reauth_at")
        if reauth_at is None:
            return False
        window = timedelta(minutes=REAUTH_WINDOW_MINUTES)
        return _now() - reauth_at <= window


def get_csrf_token(session_id: str) -> str | None:
    """Return the CSRF token for a session, or None."""
    with _lock:
        record = _SESSIONS.get(session_id)
        if record is None:
            return None
        return record["csrf_token"]


def reset_sessions() -> None:
    """Clear all sessions — **for testing only**."""
    with _lock:
        _SESSIONS.clear()
        _save_to_disk()


def active_session_count() -> int:
    """Return the number of active sessions — **for testing/monitoring**."""
    with _lock:
        return len(_SESSIONS)
