"""Authentication package for Gradio UI adapter.

Provides demo login/logout, profile management, and brute-force lockout.

Public API
~~~~~~~~~~
- ``authenticate(username, password)`` → result dict
- ``logout(actor_id)`` → result dict
- ``get_profile(actor_id)`` → profile dict
- ``update_profile(actor_id, name, email)`` → result dict
- ``get_logged_in_label(actor_id)`` → display string
- ``check_auth(request)`` → auth state tuple for Gradio page load
"""

from __future__ import annotations

from adapters.ui_gradio.auth._check_auth import check_auth
from adapters.ui_gradio.auth._service import (
    authenticate,
    check_username_available,
    get_logged_in_label,
    get_profile,
    is_session_valid,
    logout,
    register,
    update_profile,
)

__all__ = [
    "authenticate",
    "check_auth",
    "check_username_available",
    "get_logged_in_label",
    "get_profile",
    "is_session_valid",
    "logout",
    "register",
    "update_profile",
]
