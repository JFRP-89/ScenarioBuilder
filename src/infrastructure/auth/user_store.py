"""In-memory user store — users, password hashes, profiles, lockout state.

Shared across Flask and Gradio adapters.  No framework imports.

Security notes
~~~~~~~~~~~~~~
- Passwords are hashed with PBKDF2-HMAC-SHA256 (100 000 iterations + random salt).
- Lockout counters are per-username (anti brute-force).
"""

from __future__ import annotations

import hashlib
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, TypedDict, cast

# ── Optional database imports (best-effort persistence) ──────────────────────
try:
    from sqlalchemy.exc import SQLAlchemyError

    from infrastructure.db.models import UserModel
    from infrastructure.db.session import SessionLocal

    _HAS_DB = True
except ImportError:
    _HAS_DB = False

    if TYPE_CHECKING:
        from sqlalchemy.exc import SQLAlchemyError

        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal

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


# ── Public API ───────────────────────────────────────────────────────────────
def user_exists(username: str) -> bool:
    """Return True if *username* is a registered user."""
    with _lock:
        return username in _USERS


def email_exists(email: str, *, exclude_username: str | None = None) -> bool:
    """Return True if *email* is already registered by another user.

    Empty emails are never considered duplicates.
    If *exclude_username* is given, that user's email is ignored
    (used when updating your own profile).
    """
    if not email:
        return False
    with _lock:
        for uname, record in _USERS.items():
            if uname == exclude_username:
                continue
            if record["email"] == email:
                return True
        return False


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
    """Update display name and email. Return True on success.

    Returns False if *username* does not exist **or** if *email* is
    already registered by a different user.
    """
    with _lock:
        user = _USERS.get(username)
        if user is None:
            return False
        # Check email uniqueness (empty emails are exempt)
        if email:
            for uname, record in _USERS.items():
                if uname != username and record["email"] == email:
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
        # Check email uniqueness (empty emails are exempt)
        if email:
            for record in _USERS.values():
                if record["email"] == email:
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
    if not _HAS_DB:
        return
    try:
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
    except (OSError, RuntimeError):
        pass


def load_users_from_database() -> int:
    """Load all users from PostgreSQL into the in-memory store.

    Called once during ``build_services()`` so that users persisted in a
    previous run are available immediately after restart.

    Returns the number of users loaded.  Silently returns 0 when the
    database is unavailable or the dependency is not installed.
    """
    try:
        if not _HAS_DB:
            return 0
    except NameError:
        return 0

    try:
        session = SessionLocal()
        try:
            rows = session.query(UserModel).all()
            count = 0
            with _lock:
                for row in rows:
                    uname = cast(str, row.username)
                    if uname not in _USERS:
                        _USERS[uname] = UserRecord(
                            password_hash=cast(bytes, row.password_hash),
                            salt=cast(bytes, row.salt),
                            name=cast(str, row.name),
                            email=cast(str, row.email),
                        )
                        count += 1
            return count
        except SQLAlchemyError:
            return 0
        finally:
            session.close()
    except (OSError, RuntimeError):
        return 0
