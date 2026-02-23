"""Authentication service — thin adapter over infrastructure auth_service.

Delegates to ``infrastructure.auth.auth_service`` for all logic.
The Gradio adapter uses ``actor_id`` strings (not session IDs) as the
primary handle, so this module maps between the two worlds.
"""

from __future__ import annotations

import html as _html
from typing import Any

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

    Validates that *session_id* belongs to *actor_id* before invalidating.
    Returns ``{"ok": True, "actor_id": "", "message": "Logged out."}``.
    """
    if session_id:
        from infrastructure.auth.session_store import get_session, invalidate_session

        session = get_session(session_id)
        if session is not None and session["actor_id"] == actor_id:
            invalidate_session(session_id)
    return {"ok": True, "actor_id": "", "message": "Logged out."}


def get_profile(actor_id: str) -> dict[str, Any]:
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
    new_password: str = "",  # nosec B107 — empty sentinel, not a default password
    confirm_new_password: str = "",  # nosec B107
) -> dict[str, Any]:
    """Update profile fields for *actor_id*.

    Validates name and email before persisting.
    If *new_password* and *confirm_new_password* are both non-empty,
    validates and changes the password as well.
    """
    from infrastructure.auth.user_store import email_exists, update_user_profile
    from infrastructure.auth.validators import validate_registration_password

    name = name.strip()
    email = email.strip()

    if not validate_display_name(name):
        return {
            "ok": False,
            "message": "Invalid display name (1-64 printable characters).",
        }

    if not validate_email(email):
        return {"ok": False, "message": "Invalid email format."}

    # ── Email uniqueness (exclude current user) ──────────────────
    if email_exists(email, exclude_username=actor_id):
        return {"ok": False, "message": "Email is already registered."}

    # ── Optional password change ─────────────────────────────────
    wants_pw_change = bool(new_password or confirm_new_password)
    if wants_pw_change:
        if new_password != confirm_new_password:
            return {"ok": False, "message": "Passwords do not match."}
        pw_ok, pw_errors = validate_registration_password(new_password)
        if not pw_ok:
            return {"ok": False, "message": pw_errors[0]}

    if not update_user_profile(actor_id, name, email):
        return {"ok": False, "message": "User not found."}

    if wants_pw_change:
        from infrastructure.auth.user_store import change_password

        change_password(actor_id, new_password)
        return {"ok": True, "message": "Profile and password updated."}

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
    """Return an HTML user-pill for the current session.

    The pill shows a user icon + display name (truncated via CSS).
    If no display name is stored, it falls back to the username.
    """
    if not actor_id:
        return ""
    profile = get_user_profile(actor_id)
    display = profile["name"] if profile and profile.get("name") else actor_id
    # SVG user icon (Heroicons "user" outline, 18 x 18)
    icon_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" '
        'viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">'
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z'
        "M4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75"
        'c-2.676 0-5.216-.584-7.499-1.632Z"/>'
        "</svg>"
    )
    safe_name = _html.escape(display, quote=True)
    return (
        f'<span class="sb-userpill" title="{safe_name}">'
        f'<span class="sb-userpill__icon">{icon_svg}</span>'
        f'<span class="sb-userpill__name">{safe_name}</span>'
        f"</span>"
    )


def register(
    username: str,
    password: str,
    confirm_password: str,
    name: str = "",
    email: str = "",  # Empty will be rejected by auth_service validation
) -> dict[str, object]:
    """Register a new user — delegates to infrastructure auth service.

    Returns the same contract as ``auth_service.register()``.
    """
    result: dict[str, object] = _infra_svc.register(
        username,
        password,
        confirm_password,
        name,
        email,
    )
    return result


def check_username_available(username: str) -> dict[str, object]:
    """Check username availability — delegates to infrastructure auth service."""
    result: dict[str, object] = _infra_svc.check_username_available(username)
    return result
