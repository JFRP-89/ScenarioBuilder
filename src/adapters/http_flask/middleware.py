"""Flask middleware — session loading, CSRF verification, API auth gate.

Registered via ``init_middleware(app)`` in ``create_app()``.

Session lifecycle:
1. ``before_request``: load session from ``sb_session`` cookie → ``g.actor_id``
2. Auth gate: API routes (``/cards``, ``/favorites``, etc.) require valid session.
3. CSRF check on mutating methods (POST/PUT/PATCH/DELETE) for non-exempt routes.
4. Routes use ``g.actor_id`` (or the legacy ``X-Actor-Id`` header as fallback).
"""

from __future__ import annotations

import logging

from flask import Flask, g, jsonify, request
from infrastructure.auth import session_store

logger = logging.getLogger(__name__)

_COOKIE_NAME = "sb_session"
_CSRF_HEADER = "X-CSRF-Token"

# Routes exempt from CSRF (login itself, health, read-only auth endpoints)
_CSRF_EXEMPT_PREFIXES = (
    "/auth/login",
    "/auth/register",
    "/auth/check-username",
    "/health",
)

# Methods that require CSRF verification
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Prefixes that require a valid session (API routes).
# Auth routes handle their own session checks; health is public.
_AUTH_REQUIRED_PREFIXES = ("/cards", "/favorites", "/maps", "/presets")


def _load_session() -> None:
    """Load session from cookie and populate ``g.actor_id``."""
    session_id = request.cookies.get(_COOKIE_NAME, "")
    g.session_id = session_id
    g.actor_id = ""

    if not session_id:
        return

    session = session_store.get_session(session_id)
    if session is None:
        g.session_id = ""
        return

    g.actor_id = session["actor_id"]


def _is_csrf_exempt() -> bool:
    """Return True if the current request is exempt from CSRF checks."""
    if request.method not in _MUTATING_METHODS:
        return True
    return any(request.path.startswith(prefix) for prefix in _CSRF_EXEMPT_PREFIXES)


def _verify_csrf():
    """Verify CSRF token on mutating requests (double-submit pattern).

    Returns a 403 response tuple if verification fails, or None to proceed.
    """
    if _is_csrf_exempt():
        return None

    session_id = getattr(g, "session_id", "")
    if not session_id:
        return None

    expected_token = session_store.get_csrf_token(session_id)
    if not expected_token:
        return None

    provided_token = request.headers.get(_CSRF_HEADER, "")
    if not provided_token or provided_token != expected_token:
        logger.warning(
            "CSRF verification failed for session=%s path=%s",
            session_id[:8],
            request.path,
        )
        return jsonify({"ok": False, "message": "CSRF token invalid."}), 403

    return None


def _require_auth():
    """Return 401 for API routes that lack a valid session.

    Only applies to paths starting with ``_AUTH_REQUIRED_PREFIXES``.
    """
    if not any(request.path.startswith(p) for p in _AUTH_REQUIRED_PREFIXES):
        return None

    actor_id = getattr(g, "actor_id", "")
    if not actor_id:
        return jsonify({"ok": False, "message": "Authentication required."}), 401

    return None


def init_middleware(app: Flask) -> None:
    """Attach ``before_request`` hooks to the Flask application."""
    app.before_request(_load_session)
    app.before_request(_require_auth)
    app.before_request(_verify_csrf)
