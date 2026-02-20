"""Flask auth routes — login, logout, me, reauth.

All endpoints use HttpOnly cookies for session management.
No tokens are exposed in JSON responses (except CSRF token for double-submit).

Cookie: ``sb_session`` — HttpOnly, Secure (configurable), SameSite=Lax, Path=/
"""

from __future__ import annotations

import os

from flask import Blueprint, jsonify, make_response, request
from infrastructure.auth import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ── Cookie configuration ─────────────────────────────────────────────────────
_COOKIE_NAME = "sb_session"
_CSRF_COOKIE_NAME = "sb_csrf"
_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
_COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "Lax")
_COOKIE_PATH = "/"

_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}


def _set_session_cookie(
    response,
    session_id: str,
    csrf_token: str,
):
    """Set the session cookie (HttpOnly) and CSRF cookie (non-HttpOnly)."""
    response.set_cookie(
        _COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path=_COOKIE_PATH,
    )
    # CSRF token in a readable cookie (double-submit pattern)
    response.set_cookie(
        _CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,  # JS must read this
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path=_COOKIE_PATH,
    )


def _clear_session_cookie(response):
    """Clear both session and CSRF cookies."""
    response.delete_cookie(_COOKIE_NAME, path=_COOKIE_PATH)
    response.delete_cookie(_CSRF_COOKIE_NAME, path=_COOKIE_PATH)


# ── POST /auth/login ─────────────────────────────────────────────────────────


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and set HttpOnly session cookie."""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))

    result = auth_service.authenticate(username, password)

    if not result["ok"]:
        resp = make_response(
            jsonify({"ok": False, "message": result["message"]}),
            401,
        )
        for k, v in _NO_CACHE_HEADERS.items():
            resp.headers[k] = v
        return resp

    session_id = str(result["session_id"])
    csrf_token = str(result["csrf_token"])
    actor_id = str(result["actor_id"])

    body = {
        "ok": True,
        "actor_id": actor_id,
        "message": result["message"],
    }
    resp = make_response(jsonify(body), 200)
    _set_session_cookie(resp, session_id, csrf_token)
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp


# ── POST /auth/logout ────────────────────────────────────────────────────────


@auth_bp.route("/logout", methods=["POST"])
def logout_route():
    """Invalidate session and clear cookie."""
    session_id = request.cookies.get(_COOKIE_NAME, "")
    auth_service.logout(session_id)

    resp = make_response(jsonify({"ok": True, "message": "Logged out."}), 200)
    _clear_session_cookie(resp)
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp


# ── GET /auth/me ──────────────────────────────────────────────────────────────


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return the profile of the authenticated user."""
    session_id = request.cookies.get(_COOKIE_NAME, "")
    result = auth_service.get_me(session_id)

    if not result["ok"]:
        resp = make_response(
            jsonify({"ok": False, "message": result["message"]}),
            401,
        )
        for k, v in _NO_CACHE_HEADERS.items():
            resp.headers[k] = v
        return resp

    resp = make_response(jsonify({"ok": True, "profile": result["profile"]}), 200)
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp


# ── POST /auth/reauth ────────────────────────────────────────────────────────


@auth_bp.route("/reauth", methods=["POST"])
def reauth_route():
    """Re-authenticate within an existing session.

    Validates password, marks ``reauth_at``, rotates session ID.
    """
    session_id = request.cookies.get(_COOKIE_NAME, "")
    if not session_id:
        return jsonify({"ok": False, "message": "Not authenticated."}), 401

    data = request.get_json(silent=True) or {}
    password = str(data.get("password", ""))

    result = auth_service.reauth(session_id, password)

    if not result["ok"]:
        status = 401
        resp = make_response(
            jsonify({"ok": False, "message": result["message"]}),
            status,
        )
        for k, v in _NO_CACHE_HEADERS.items():
            resp.headers[k] = v
        return resp

    new_session_id = str(result["session_id"])
    new_csrf = str(result["csrf_token"])

    body = {"ok": True, "message": result["message"]}
    resp = make_response(jsonify(body), 200)
    _set_session_cookie(resp, new_session_id, new_csrf)
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp


# ── POST /auth/profile ───────────────────────────────────────────────────────


@auth_bp.route("/profile", methods=["POST"])
def update_profile_route():
    """Update profile (display name + email) for the session owner."""
    session_id = request.cookies.get(_COOKIE_NAME, "")
    if not session_id:
        return jsonify({"ok": False, "message": "Not authenticated."}), 401

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", ""))
    email = str(data.get("email", ""))

    result = auth_service.update_profile(session_id, name, email)

    status = 200 if result["ok"] else 400
    resp = make_response(
        jsonify({"ok": result["ok"], "message": result["message"]}),
        status,
    )
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp


# ── POST /auth/register ─────────────────────────────────────────────────────


@auth_bp.route("/register", methods=["POST"])
def register_route():
    """Register a new user and set session cookie (auto-login)."""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))
    confirm_password = str(data.get("confirm_password", ""))
    name = str(data.get("name", ""))
    email = str(data.get("email", ""))

    result = auth_service.register(username, password, confirm_password, name, email)

    if not result["ok"]:
        body: dict[str, object] = {
            "ok": False,
            "message": result["message"],
        }
        if "errors" in result:
            body["errors"] = result["errors"]
        resp = make_response(jsonify(body), 400)
        for k, v in _NO_CACHE_HEADERS.items():
            resp.headers[k] = v
        return resp

    session_id = str(result["session_id"])
    csrf_token = str(result["csrf_token"])
    actor_id = str(result["actor_id"])

    body = {
        "ok": True,
        "actor_id": actor_id,
        "message": result["message"],
    }
    resp = make_response(jsonify(body), 201)
    _set_session_cookie(resp, session_id, csrf_token)
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp


# ── GET /auth/check-username ─────────────────────────────────────────────────


@auth_bp.route("/check-username", methods=["GET"])
def check_username_route():
    """Check if a username is available for registration."""
    username = request.args.get("username", "").strip()
    result = auth_service.check_username_available(username)

    resp = make_response(jsonify(result), 200)
    for k, v in _NO_CACHE_HEADERS.items():
        resp.headers[k] = v
    return resp
