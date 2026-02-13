"""Victory points state helpers."""

from __future__ import annotations

import uuid
from typing import Any


def add_victory_point(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add a new empty victory point to the state."""
    new_vp = {
        "id": str(uuid.uuid4())[:8],
        "description": "",
    }
    return [*current_state, new_vp]


def remove_last_victory_point(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove the last victory point from the state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_victory_point(
    current_state: list[dict[str, Any]], vp_id: str
) -> list[dict[str, Any]]:
    """Remove selected victory point from state."""
    return [vp for vp in current_state if vp.get("id") != vp_id]


def get_victory_points_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from victory points state."""
    if not state:
        return []
    return [
        (vp["description"][:50] if vp["description"] else "Empty", vp["id"])
        for vp in state
    ]


def update_victory_point(
    current_state: list[dict[str, Any]],
    vp_id: str,
    description: str,
) -> list[dict[str, Any]]:
    """Update an existing victory point in place."""
    return [
        {**vp, "description": description} if vp["id"] == vp_id else vp
        for vp in current_state
    ]
