"""Authentication service — thin adapter over infrastructure auth_service.

Delegates to ``infrastructure.auth.auth_service`` for all logic.
The Gradio adapter uses ``actor_id`` strings (not session IDs) as the
primary handle, so this module maps between the two worlds.
"""

from __future__ import annotations

from infrastructure.auth import auth_service as _infra_svc
from infrastructure.auth.user_store import get_user_profile
from infrastructure.auth.validators import (
    validate_display_name,
    validate_email,
)

# ── Thin re-export for backward compatibility ────────────────────────────────


def authenticate(username: str, password: str) -> dict[str, object]:
    """Authenticate a user — delegates to infrastructure auth service.

    Returns the same contract as before (``ok``, ``actor_id``, ``message``).
    Session creation is handled internally.
    """
    result: dict[str, object] = _infra_svc.authenticate(username, password)
    return result


def logout(actor_id: str, session_id: str = "") -> dict[str, object]:
    """Logout the current user — invalidates the server-side session.

    Returns ``{"ok": True, "actor_id": "", "message": "Logged out."}``.
    """
    if session_id:
        from infrastructure.auth.session_store import invalidate_session

        invalidate_session(session_id)
    return {"ok": True, "actor_id": "", "message": "Logged out."}


def get_profile(actor_id: str) -> dict[str, object]:
    """Fetch profile data for *actor_id* from user store.

    Returns:
        ``{"ok": True, "profile": {...}}`` or ``{"ok": False, ...}``.
    """
    profile = get_user_profile(actor_id)
    if profile is None:
        return {"ok": False, "message": "User not found."}
    return {"ok": True, "profile": profile}


def update_profile(
    actor_id: str,
    name: str,
    email: str,
) -> dict[str, object]:
    """Update profile fields for *actor_id*.

    Validates name and email before persisting.
    """
    from infrastructure.auth.user_store import update_user_profile

    name = name.strip()
    email = email.strip()

    if not validate_display_name(name):
        return {
            "ok": False,
            "message": "Invalid display name (1-64 printable characters).",
        }

    if not validate_email(email):
        return {"ok": False, "message": "Invalid email format."}

    if not update_user_profile(actor_id, name, email):
        return {"ok": False, "message": "User not found."}

    return {"ok": True, "message": "Profile updated."}


def is_session_valid(session_id: str) -> bool:
    """Return True if *session_id* refers to a live, non-expired session.

    Checks idle timeout and max lifetime via the infrastructure session store.
    """
    if not session_id:
        return False
    from infrastructure.auth.session_store import get_session

    return get_session(session_id) is not None


def get_logged_in_label(actor_id: str) -> str:
    """Return a human-readable label for the current session."""
    if not actor_id:
        return ""
    return f"Logged in as: {actor_id}"
