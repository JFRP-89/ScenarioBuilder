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
    clear_failed_attempts,
    get_user_profile,
    is_locked,
    record_failed_attempt,
    update_user_profile,
    verify_credentials,
)
from infrastructure.auth.validators import (
    validate_display_name,
    validate_email,
    validate_password,
    validate_username,
)

logger = logging.getLogger(__name__)

# ── Generic error messages (uniform — anti-enumeration) ──────────────────────
_INVALID_CREDENTIALS = "Invalid credentials."
_ACCOUNT_LOCKED_TPL = "Account locked until {until}."
_SESSION_EXPIRED = "Session expired."
_REAUTH_REQUIRED = "Re-authentication required."


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
                until=until.strftime("%H:%M:%S UTC"),
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
                    until=locked_until.strftime("%H:%M:%S UTC"),
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
                until=until.strftime("%H:%M:%S UTC"),
            ),
        }

    if not verify_credentials(actor_id, password):
        now_locked, locked_until = record_failed_attempt(actor_id)
        if now_locked and locked_until is not None:
            return {
                "ok": False,
                "message": _ACCOUNT_LOCKED_TPL.format(
                    until=locked_until.strftime("%H:%M:%S UTC"),
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
) -> dict[str, object]:
    """Update profile fields for the session owner.

    Validates name and email before persisting.
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

    if not update_user_profile(session["actor_id"], name, email):
        return {"ok": False, "message": "User not found."}

    return {"ok": True, "message": "Profile updated."}
