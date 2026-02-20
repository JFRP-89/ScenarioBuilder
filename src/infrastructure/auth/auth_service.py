"""Authentication service — orchestrates validation, user store, sessions.

Shared backend logic used by Flask auth blueprint.
All functions return plain dicts (no framework types).
"""

from __future__ import annotations

import logging

from infrastructure.auth.session_store import (
    create_session,
    get_session,
    invalidate_session,
    is_recently_reauthed,
    mark_reauth,
    rotate_session_id,
)
from infrastructure.auth.user_store import (
    change_password,
    clear_failed_attempts,
    create_user,
    get_user_profile,
    is_locked,
    record_failed_attempt,
    update_user_profile,
    user_exists,
    verify_credentials,
)
from infrastructure.auth.validators import (
    validate_display_name,
    validate_email,
    validate_password,
    validate_registration_password,
    validate_username,
)

logger = logging.getLogger(__name__)

# ── Generic error messages (uniform — anti-enumeration) ──────────────────────
_INVALID_CREDENTIALS = "Invalid credentials."
_ACCOUNT_LOCKED_TPL = "Account locked until {until}."
_SESSION_EXPIRED = "Session expired."
_REAUTH_REQUIRED = "Re-authentication required."
_USERNAME_TAKEN = "Username is already taken."
_TIME_FMT = "%H:%M:%S UTC"


def _validate_registration_fields(
    username: str,
    password: str,
    confirm_password: str,
    name: str,
    email: str,
) -> tuple[list[str], str, str]:
    """Validate all registration inputs.

    Returns ``(errors, cleaned_name, cleaned_email)``.
    """
    errors: list[str] = []

    if not validate_username(username):
        errors.append(
            "Username must be 3-32 lowercase characters "
            "(letters, digits, hyphens, underscores)."
        )

    pw_valid, pw_errors = validate_registration_password(password)
    if not pw_valid:
        errors.extend(pw_errors)

    if password != confirm_password:
        errors.append("Passwords do not match.")

    email = email.strip()
    if email and not validate_email(email):
        errors.append("Invalid email format.")

    name = name.strip()
    if name and not validate_display_name(name):
        errors.append("Invalid display name (1-64 printable characters).")

    return errors, name, email


def register(
    username: str,
    password: str,
    confirm_password: str,
    name: str,
    email: str,
) -> dict[str, object]:
    """Register a new user account.

    Validates all inputs, checks username availability, creates user,
    and auto-logs in by creating a session.

    Returns:
        On success: ``{"ok": True, "actor_id": ..., "session_id": ...,
                       "csrf_token": ..., "message": ...}``
        On failure: ``{"ok": False, "message": ..., "errors": [...]}``
    """
    errors, name, email = _validate_registration_fields(
        username,
        password,
        confirm_password,
        name,
        email,
    )
    if errors:
        return {"ok": False, "message": errors[0], "errors": errors}

    # ── Username availability ────────────────────────────────────
    if user_exists(username):
        return {
            "ok": False,
            "message": _USERNAME_TAKEN,
            "errors": [_USERNAME_TAKEN],
        }

    # ── Create user ──────────────────────────────────────────────
    if not name:
        name = username
    if not email:
        email = ""

    created = create_user(username, password, name, email)
    if not created:
        return {
            "ok": False,
            "message": _USERNAME_TAKEN,
            "errors": [_USERNAME_TAKEN],
        }

    # ── Auto-login: create session ───────────────────────────────
    session = create_session(username)
    logger.info("register_ok: user=%s session=%s…", username, session["session_id"][:8])
    return {
        "ok": True,
        "actor_id": username,
        "session_id": session["session_id"],
        "csrf_token": session["csrf_token"],
        "message": f"Account created. Welcome, {username}!",
    }


def check_username_available(username: str) -> dict[str, object]:
    """Check if a username is available for registration.

    Returns ``{"available": True/False, "message": ...}``.
    """
    if not validate_username(username):
        return {
            "available": False,
            "message": "Username must be 3-32 lowercase characters "
            "(letters, digits, hyphens, underscores).",
        }
    if user_exists(username):
        return {"available": False, "message": _USERNAME_TAKEN}
    return {"available": True, "message": "Username is available."}


def authenticate(username: str, password: str) -> dict[str, object]:
    """Authenticate a user and create a server-side session.

    Returns:
        On success: ``{"ok": True, "actor_id": ..., "session_id": ...,
                       "csrf_token": ..., "message": ...}``
        On failure: ``{"ok": False, "actor_id": None, "message": ...}``
    """
    # ── Input validation (allowlist) ─────────────────────────────
    if not validate_username(username) or not validate_password(password):
        logger.info("login_rejected: invalid_format user=%s", username)
        return {"ok": False, "actor_id": None, "message": _INVALID_CREDENTIALS}

    # ── Lockout check (before credential verification) ───────────
    locked, until = is_locked(username)
    if locked and until is not None:
        logger.warning("login_rejected: lockout user=%s until=%s", username, until)
        return {
            "ok": False,
            "actor_id": None,
            "message": _ACCOUNT_LOCKED_TPL.format(
                until=until.strftime(_TIME_FMT),
            ),
        }

    # ── Credential verification ──────────────────────────────────
    if not verify_credentials(username, password):
        now_locked, locked_until = record_failed_attempt(username)
        if now_locked and locked_until is not None:
            logger.warning("login_lockout: user=%s until=%s", username, locked_until)
            return {
                "ok": False,
                "actor_id": None,
                "message": _ACCOUNT_LOCKED_TPL.format(
                    until=locked_until.strftime(_TIME_FMT),
                ),
            }
        logger.info("login_rejected: bad_password user=%s", username)
        return {"ok": False, "actor_id": None, "message": _INVALID_CREDENTIALS}

    # ── Success: create session ──────────────────────────────────
    clear_failed_attempts(username)
    session = create_session(username)
    logger.info("login_ok: user=%s session=%s…", username, session["session_id"][:8])
    return {
        "ok": True,
        "actor_id": username,
        "session_id": session["session_id"],
        "csrf_token": session["csrf_token"],
        "message": f"Welcome, {username}!",
    }


def logout(session_id: str) -> dict[str, object]:
    """Invalidate a session.

    Returns ``{"ok": True, "message": "Logged out."}``.
    """
    invalidated = invalidate_session(session_id)
    if invalidated:
        logger.info("logout_ok: session=%s…", session_id[:8])
    return {"ok": True, "message": "Logged out."}


def get_me(session_id: str) -> dict[str, object]:
    """Return the profile for the session owner.

    Returns ``{"ok": True, "profile": {...}}`` or ``{"ok": False, ...}``.
    """
    session = get_session(session_id)
    if session is None:
        return {"ok": False, "message": _SESSION_EXPIRED}
    profile = get_user_profile(session["actor_id"])
    if profile is None:
        return {"ok": False, "message": "User not found."}
    return {"ok": True, "profile": profile}


def reauth(session_id: str, password: str) -> dict[str, object]:
    """Re-authenticate within an existing session.

    Validates the password, marks ``reauth_at``, rotates session ID.

    Returns:
        ``{"ok": True, "session_id": ..., "csrf_token": ..., ...}`` on success.
        ``{"ok": False, "message": ...}`` on failure.
    """
    session = get_session(session_id)
    if session is None:
        return {"ok": False, "message": _SESSION_EXPIRED}

    actor_id = session["actor_id"]

    if not validate_password(password):
        return {"ok": False, "message": _INVALID_CREDENTIALS}

    # ── Lockout check ────────────────────────────────────────────
    locked, until = is_locked(actor_id)
    if locked and until is not None:
        return {
            "ok": False,
            "message": _ACCOUNT_LOCKED_TPL.format(
                until=until.strftime(_TIME_FMT),
            ),
        }

    if not verify_credentials(actor_id, password):
        now_locked, locked_until = record_failed_attempt(actor_id)
        if now_locked and locked_until is not None:
            return {
                "ok": False,
                "message": _ACCOUNT_LOCKED_TPL.format(
                    until=locked_until.strftime(_TIME_FMT),
                ),
            }
        return {"ok": False, "message": _INVALID_CREDENTIALS}

    # ── Success: mark reauth + rotate session ────────────────────
    clear_failed_attempts(actor_id)
    mark_reauth(session_id)
    rotated = rotate_session_id(session_id)
    if rotated is None:
        return {"ok": False, "message": _SESSION_EXPIRED}

    logger.info("reauth_ok: user=%s session=%s…", actor_id, rotated["session_id"][:8])
    return {
        "ok": True,
        "session_id": rotated["session_id"],
        "csrf_token": rotated["csrf_token"],
        "message": "Re-authenticated.",
    }


def check_reauth(session_id: str) -> bool:
    """Return True if the session was recently re-authenticated."""
    result: bool = is_recently_reauthed(session_id)
    return result


def update_profile(
    session_id: str,
    name: str,
    email: str,
    new_password: str = "",  # nosec B107 — empty sentinel, not a default password
    confirm_new_password: str = "",  # nosec B107
) -> dict[str, object]:
    """Update profile fields for the session owner.

    Validates name and email before persisting.  If *new_password* and
    *confirm_new_password* are both non-empty they must match and satisfy
    the strong-password policy; the password is then changed as well.
    When both are empty the password is left unchanged.
    """
    session = get_session(session_id)
    if session is None:
        return {"ok": False, "message": _SESSION_EXPIRED}

    name = name.strip()
    email = email.strip()

    if not validate_display_name(name):
        return {
            "ok": False,
            "message": "Invalid display name (1-64 printable characters).",
        }

    if not validate_email(email):
        return {"ok": False, "message": "Invalid email format."}

    # ── Optional password change ─────────────────────────────────
    wants_pw_change = bool(new_password or confirm_new_password)
    if wants_pw_change:
        if new_password != confirm_new_password:
            return {"ok": False, "message": "Passwords do not match."}
        pw_ok, pw_errors = validate_registration_password(new_password)
        if not pw_ok:
            return {"ok": False, "message": pw_errors[0]}

    if not update_user_profile(session["actor_id"], name, email):
        return {"ok": False, "message": "User not found."}

    if wants_pw_change:
        change_password(session["actor_id"], new_password)
        return {"ok": True, "message": "Profile and password updated."}

    return {"ok": True, "message": "Profile updated."}
