"""Config helpers for UI state."""

from __future__ import annotations

import os


def get_default_actor_id() -> str:
    """Get default actor ID from environment."""
    return os.environ.get("DEFAULT_ACTOR_ID", "demo-user")
