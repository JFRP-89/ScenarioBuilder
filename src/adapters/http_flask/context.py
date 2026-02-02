"""Request context helpers for Flask adapter.

This module provides thin wrappers around Flask's current_app config
to eliminate boilerplate and provide a single point of access to services
and request context (like actor_id).

Usage in route handlers:
    from adapters.http_flask.context import get_services, get_actor_id

    def my_handler():
        actor_id = get_actor_id()  # Instead of current_app.config["get_actor_id"]()
        services = get_services()  # Instead of current_app.config["services"]
"""

from __future__ import annotations

from typing import cast

from flask import current_app


def get_services():
    """Get the services container from Flask app config.

    The services container is populated by build_services() during app creation.

    Returns:
        Services container with use case methods:
        - generate_scenario_card
        - get_card
        - list_cards
        - toggle_favorite
        - list_favorites
        - create_variant
        - render_map_svg

    Raises:
        KeyError: If "services" is not in app.config (indicates app initialization issue)
    """
    return current_app.config["services"]


def get_actor_id() -> str:
    """Get the actor ID from the current request context.

    The actor_id is extracted from the X-Actor-Id header by app._get_actor_id()
    during request handling. This helper retrieves the callable from config and invokes it.

    Returns:
        The actor ID from X-Actor-Id header.

    Raises:
        ValidationError: If X-Actor-Id header is missing or empty.
        KeyError: If "get_actor_id" is not in app.config (indicates app initialization issue)
    """
    return cast(str, current_app.config["get_actor_id"]())
