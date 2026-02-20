"""PostgreSQL session store — all sessions persisted in ``sessions`` table.

Drop-in replacement for the file-backed ``session_store.py``.
Implements the same public API so ``auth_service.py`` can switch backends
via the bootstrap composition root.

Security:
- ``session_id``: 256-bit cryptographically random hex token.
- ``csrf_token``: 256-bit random hex (stored as plaintext — already opaque).
- Soft revocation via ``revoked_at`` column (not hard-delete).
- ``expires_at`` enforces max lifetime; ``last_seen_at`` enforces idle timeout.
- Touch throttling: ``last_seen_at`` is updated at most once per ``TOUCH_INTERVAL``.

Thread-safety: each operation opens its own SQLAlchemy session
(same pattern as ``PostgresCardRepository``).
"""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Callable, TypedDict

from application.ports.clock import Clock
from infrastructure.clock import SystemClock
from infrastructure.db.models import SessionModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ── Configuration (overridable via env) ──────────────────────────────────────
SESSION_IDLE_MINUTES = int(os.environ.get("SESSION_IDLE_MINUTES", "15"))
SESSION_MAX_HOURS = int(os.environ.get("SESSION_MAX_HOURS", "12"))
REAUTH_WINDOW_MINUTES = int(os.environ.get("REAUTH_WINDOW_MINUTES", "10"))
TOUCH_THROTTLE_SECONDS = int(os.environ.get("SESSION_TOUCH_THROTTLE", "30"))

_SESSION_ID_BYTES = 32  # 256-bit random


# ── Types ────────────────────────────────────────────────────────────────────
class SessionRecord(TypedDict):
    session_id: str
    actor_id: str
    created_at: datetime
    last_seen_at: datetime
    reauth_at: datetime | None
    csrf_token: str


# ── Helpers ──────────────────────────────────────────────────────────────────


def _generate_session_id() -> str:
    """Generate a cryptographically secure session ID (hex, 64 chars)."""
    return secrets.token_hex(_SESSION_ID_BYTES)


def _generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token (hex, 64 chars)."""
    return secrets.token_hex(32)


# ── Clock (injectable for testing) ───────────────────────────────────────────
_clock_holder: list[Clock] = [SystemClock()]


def set_clock(clock: Clock) -> None:
    """Replace the module clock — **for testing only**."""
    _clock_holder[0] = clock


def _now() -> datetime:
    """Return current UTC time via the configured clock."""
    return _clock_holder[0].now_utc()


def _model_to_record(model: SessionModel) -> SessionRecord:
    """Convert ORM model to the dict contract used by auth_service."""
    return SessionRecord(
        session_id=model.session_id,  # type: ignore[typeddict-item]
        actor_id=model.username,  # type: ignore[typeddict-item]
        created_at=model.created_at,  # type: ignore[typeddict-item]
        last_seen_at=model.last_seen_at,  # type: ignore[typeddict-item]
        reauth_at=model.reauth_at,  # type: ignore[typeddict-item]
        csrf_token=model.csrf_token,  # type: ignore[typeddict-item]
    )


def _is_valid(model: SessionModel, now: datetime) -> bool:
    """Return True if the session is not revoked and not expired."""
    if model.revoked_at is not None:
        return False
    if now > model.expires_at:
        return False
    idle_limit = now - timedelta(minutes=SESSION_IDLE_MINUTES)
    return model.last_seen_at >= idle_limit


# ── PostgresSessionStore ─────────────────────────────────────────────────────


class PostgresSessionStore:
    """PostgreSQL-backed session store.

    All methods follow the session-per-operation pattern: create a
    SQLAlchemy session, do work, commit/rollback, close.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._sf = session_factory

    # ── create ───────────────────────────────────────────────────

    def create_session(self, actor_id: str) -> SessionRecord:
        """Create a new session row and return the record."""
        now = _now()
        session_id = _generate_session_id()
        csrf_token = _generate_csrf_token()
        expires_at = now + timedelta(hours=SESSION_MAX_HOURS)

        model = SessionModel(
            session_id=session_id,
            username=actor_id,
            created_at=now,
            last_seen_at=now,
            expires_at=expires_at,
            csrf_token=csrf_token,
            reauth_at=None,
            revoked_at=None,
        )

        db = self._sf()
        try:
            db.add(model)
            db.commit()
            record = _model_to_record(model)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        logger.debug("session_created: sid=%s… user=%s", session_id[:8], actor_id)
        return record

    # ── read ─────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> SessionRecord | None:
        """Retrieve a valid session, touching ``last_seen_at``.

        Returns None if the session is missing, revoked, or expired.
        """
        if not session_id:
            return None

        db = self._sf()
        try:
            model = db.query(SessionModel).filter_by(session_id=session_id).first()
            if model is None:
                return None

            now = _now()
            if not _is_valid(model, now):
                return None

            # Touch with throttling
            delta = (now - model.last_seen_at).total_seconds()
            if delta >= TOUCH_THROTTLE_SECONDS:
                model.last_seen_at = now  # type: ignore[assignment]
                db.commit()

            record = _model_to_record(model)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return record

    # ── invalidate / revoke ──────────────────────────────────────

    def invalidate_session(self, session_id: str) -> bool:
        """Soft-revoke a session. Return True if it existed and was active."""
        db = self._sf()
        try:
            model = db.query(SessionModel).filter_by(session_id=session_id).first()
            if model is None or model.revoked_at is not None:
                return False
            model.revoked_at = _now()
            db.commit()
            logger.debug("session_revoked: sid=%s…", session_id[:8])
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def revoke_all_sessions(self, username: str) -> int:
        """Revoke all active sessions for *username*. Return count revoked."""
        now = _now()
        db = self._sf()
        try:
            models = (
                db.query(SessionModel)
                .filter_by(username=username)
                .filter(SessionModel.revoked_at.is_(None))
                .all()
            )
            count = 0
            for m in models:
                m.revoked_at = now  # type: ignore[assignment]
                count += 1
            db.commit()
            if count:
                logger.info(
                    "sessions_revoked_all: user=%s count=%d",
                    username,
                    count,
                )
            return count
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── reauth ───────────────────────────────────────────────────

    def mark_reauth(self, session_id: str) -> bool:
        """Mark a session as recently re-authenticated."""
        db = self._sf()
        try:
            model = db.query(SessionModel).filter_by(session_id=session_id).first()
            if model is None or model.revoked_at is not None:
                return False
            model.reauth_at = _now()
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def is_recently_reauthed(self, session_id: str) -> bool:
        """Return True if the session was re-authenticated within the window."""
        db = self._sf()
        try:
            model = db.query(SessionModel).filter_by(session_id=session_id).first()
            if model is None or model.revoked_at is not None:
                return False
            if model.reauth_at is None:
                return False
            window = timedelta(minutes=REAUTH_WINDOW_MINUTES)
            return bool(_now() - model.reauth_at <= window)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── rotation ─────────────────────────────────────────────────

    def rotate_session_id(self, old_session_id: str) -> SessionRecord | None:
        """Rotate: revoke old session, create new one preserving data.

        Done in a single DB transaction for atomicity.
        """
        db = self._sf()
        try:
            old = db.query(SessionModel).filter_by(session_id=old_session_id).first()
            if old is None or old.revoked_at is not None:
                return None

            now = _now()
            if not _is_valid(old, now):
                return None

            # Revoke old
            old.revoked_at = now

            # Create new
            new_id = _generate_session_id()
            new_csrf = _generate_csrf_token()
            new_model = SessionModel(
                session_id=new_id,
                username=old.username,
                created_at=old.created_at,
                last_seen_at=now,
                expires_at=old.expires_at,
                csrf_token=new_csrf,
                reauth_at=old.reauth_at,
                revoked_at=None,
            )
            db.add(new_model)
            db.commit()

            logger.debug(
                "session_rotated: old=%s… new=%s… user=%s",
                old_session_id[:8],
                new_id[:8],
                old.username,
            )
            record = _model_to_record(new_model)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return record

    # ── CSRF ─────────────────────────────────────────────────────

    def get_csrf_token(self, session_id: str) -> str | None:
        """Return the CSRF token for a valid session, or None."""
        db = self._sf()
        try:
            model = db.query(SessionModel).filter_by(session_id=session_id).first()
            if model is None or model.revoked_at is not None:
                return None
            now = _now()
            if not _is_valid(model, now):
                return None
            token: str | None = model.csrf_token
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return token

    # ── housekeeping ─────────────────────────────────────────────

    def cleanup_expired_sessions(self) -> int:
        """Hard-delete sessions that are expired or revoked for > 24h."""
        cutoff = _now() - timedelta(hours=24)
        db = self._sf()
        try:
            expired = (
                db.query(SessionModel).filter(SessionModel.expires_at < _now()).count()
            )
            db.query(SessionModel).filter(
                SessionModel.expires_at < _now(),
            ).delete(synchronize_session="fetch")

            revoked_old = (
                db.query(SessionModel)
                .filter(
                    SessionModel.revoked_at.isnot(None),
                    SessionModel.revoked_at < cutoff,
                )
                .count()
            )
            db.query(SessionModel).filter(
                SessionModel.revoked_at.isnot(None),
                SessionModel.revoked_at < cutoff,
            ).delete(synchronize_session="fetch")

            db.commit()
            total = int(expired + revoked_old)
            if total:
                logger.info(
                    "sessions_cleaned: expired=%d revoked_old=%d",
                    expired,
                    revoked_old,
                )
            return total
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def active_session_count(self) -> int:
        """Return the number of non-revoked, non-expired sessions."""
        now = _now()
        idle_limit = now - timedelta(minutes=SESSION_IDLE_MINUTES)
        db = self._sf()
        try:
            return int(
                db.query(SessionModel)
                .filter(
                    SessionModel.revoked_at.is_(None),
                    SessionModel.expires_at > now,
                    SessionModel.last_seen_at >= idle_limit,
                )
                .count()
            )
        finally:
            db.close()

    def reset_sessions(self) -> None:
        """Delete ALL sessions — **for testing only**."""
        db = self._sf()
        try:
            db.query(SessionModel).delete()
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
