"""In-memory user store — users, password hashes, profiles, lockout state.

Shared across Flask and Gradio adapters.  No framework imports.

Security notes
~~~~~~~~~~~~~~
- Passwords are hashed with PBKDF2-HMAC-SHA256 (100 000 iterations + random salt).
- Lockout counters are per-username (anti brute-force).
- Demo users have ``password == username`` but are stored hashed.
"""

from __future__ import annotations

import hashlib
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import TypedDict

# ── Constants ────────────────────────────────────────────────────────────────
_PBKDF2_ITERATIONS = 100_000
_SALT_LENGTH = 32
_HASH_ALGO = "sha256"
_DK_LEN = 32

MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(hours=1)


# ── Types ────────────────────────────────────────────────────────────────────
class UserRecord(TypedDict):
    password_hash: bytes
    salt: bytes
    name: str
    email: str


class LockoutRecord(TypedDict):
    fail_count: int
    locked_until: datetime | None


# ── Hashing helpers ──────────────────────────────────────────────────────────
def _hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Hash *password* with PBKDF2-HMAC and return ``(hash, salt)``."""
    if salt is None:
        salt = os.urandom(_SALT_LENGTH)
    pw_hash = hashlib.pbkdf2_hmac(
        _HASH_ALGO,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_DK_LEN,
    )
    return pw_hash, salt


def _verify_password(password: str, pw_hash: bytes, salt: bytes) -> bool:
    """Return True if *password* matches the stored hash."""
    candidate, _ = _hash_password(password, salt)
    return candidate == pw_hash


# ── In-memory stores (module-level, protected by lock) ───────────────────────
_lock = threading.Lock()

_USERS: dict[str, UserRecord] = {}
_LOCKOUT: dict[str, LockoutRecord] = {}


def _seed_demo_users() -> None:
    """Populate demo users (idempotent)."""
    demo_accounts = {
        "demo-user": {"name": "Demo User", "email": "demo@example.com"},
        "alice": {"name": "Alice", "email": "alice@example.com"},
        "bob": {"name": "Bob", "email": "bob@example.com"},
        "charlie": {"name": "Charlie", "email": "charlie@example.com"},
        "dave": {"name": "Dave", "email": "dave@example.com"},
    }
    for username, info in demo_accounts.items():
        if username not in _USERS:
            pw_hash, salt = _hash_password(username)  # password == username
            _USERS[username] = UserRecord(
                password_hash=pw_hash,
                salt=salt,
                name=info["name"],
                email=info["email"],
            )


# Seed on import so they're always available
_seed_demo_users()


# ── Public API ───────────────────────────────────────────────────────────────
def user_exists(username: str) -> bool:
    """Return True if *username* is a registered user."""
    with _lock:
        return username in _USERS


def verify_credentials(username: str, password: str) -> bool:
    """Return True if credentials are valid. Does NOT check lockout."""
    with _lock:
        user = _USERS.get(username)
        if user is None:
            return False
        return _verify_password(password, user["password_hash"], user["salt"])


def is_locked(username: str) -> tuple[bool, datetime | None]:
    """Return ``(locked, locked_until)`` for *username*."""
    with _lock:
        rec = _LOCKOUT.get(username)
        if rec is None:
            return False, None
        until = rec.get("locked_until")
        if until is not None and datetime.now(timezone.utc) < until:
            return True, until
        # Expired — clear
        if until is not None:
            rec["fail_count"] = 0
            rec["locked_until"] = None
        return False, None


def record_failed_attempt(username: str) -> tuple[bool, datetime | None]:
    """Record a failed login attempt; return new lockout state."""
    with _lock:
        rec = _LOCKOUT.setdefault(
            username,
            LockoutRecord(fail_count=0, locked_until=None),
        )
        rec["fail_count"] += 1
        if rec["fail_count"] >= MAX_FAILED_ATTEMPTS:
            until = datetime.now(timezone.utc) + LOCKOUT_DURATION
            rec["locked_until"] = until
            return True, until
        return False, None


def clear_failed_attempts(username: str) -> None:
    """Reset failure counter on successful login."""
    with _lock:
        _LOCKOUT.pop(username, None)


def get_user_profile(username: str) -> dict[str, str] | None:
    """Return ``{username, name, email}`` or None."""
    with _lock:
        user = _USERS.get(username)
        if user is None:
            return None
        return {
            "username": username,
            "name": user["name"],
            "email": user["email"],
        }


def update_user_profile(username: str, name: str, email: str) -> bool:
    """Update display name and email. Return True on success."""
    with _lock:
        user = _USERS.get(username)
        if user is None:
            return False
        user["name"] = name
        user["email"] = email
        return True


def change_password(username: str, new_password: str) -> bool:
    """Change the password for *username*. Return True on success."""
    with _lock:
        user = _USERS.get(username)
        if user is None:
            return False
        pw_hash, salt = _hash_password(new_password)
        user["password_hash"] = pw_hash
        user["salt"] = salt
    return True


def reset_stores() -> None:
    """Reset all in-memory stores — **for testing only**."""
    with _lock:
        _USERS.clear()
        _LOCKOUT.clear()
    _seed_demo_users()


def create_user(
    username: str,
    password: str,
    name: str,
    email: str,
) -> bool:
    """Create a new user with hashed password.

    Stores in the in-memory store and optionally in PostgreSQL.

    Returns True on success, False if the username already exists.
    """
    with _lock:
        if username in _USERS:
            return False
        pw_hash, salt = _hash_password(password)
        _USERS[username] = UserRecord(
            password_hash=pw_hash,
            salt=salt,
            name=name,
            email=email,
        )

    # Best-effort persistence to PostgreSQL
    _persist_user_to_database(username)
    return True


def _persist_user_to_database(username: str) -> None:
    """Persist a single user to PostgreSQL (best-effort, no-op on failure)."""
    try:
        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal
        from sqlalchemy.exc import SQLAlchemyError

        with _lock:
            user_rec = _USERS.get(username)
            if user_rec is None:
                return

        session = SessionLocal()
        try:
            existing = session.query(UserModel).filter_by(username=username).first()
            if existing is None:
                model = UserModel(
                    username=username,
                    password_hash=user_rec["password_hash"],
                    salt=user_rec["salt"],
                    name=user_rec["name"],
                    email=user_rec["email"],
                )
                session.add(model)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
        finally:
            session.close()
    except ImportError:
        pass
    except (OSError, RuntimeError):
        pass


def seed_demo_users_to_database() -> None:
    """Attempt to seed demo users to PostgreSQL (if available, idempotent).

    This is called at app startup to populate the users table.
    If PostgreSQL is not available, silently skips (falls back to in-memory).
    """
    try:
        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal
        from sqlalchemy.exc import SQLAlchemyError

        demo_accounts = {
            "demo-user": {"name": "Demo User", "email": "demo@example.com"},
            "alice": {"name": "Alice", "email": "alice@example.com"},
            "bob": {"name": "Bob", "email": "bob@example.com"},
            "charlie": {"name": "Charlie", "email": "charlie@example.com"},
            "dave": {"name": "Dave", "email": "dave@example.com"},
        }

        session = SessionLocal()
        try:
            for username, _info in demo_accounts.items():
                existing = session.query(UserModel).filter_by(username=username).first()
                if existing is None and username in _USERS:
                    user_rec = _USERS[username]
                    model = UserModel(
                        username=username,
                        password_hash=user_rec["password_hash"],
                        salt=user_rec["salt"],
                        name=user_rec["name"],
                        email=user_rec["email"],
                    )
                    session.add(model)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()
    except ImportError:
        pass
    except (OSError, RuntimeError):
        pass
