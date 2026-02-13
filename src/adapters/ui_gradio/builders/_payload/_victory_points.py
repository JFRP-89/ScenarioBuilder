"""Victory-points validation for payload construction.

Pure functions — no side effects, no UI dependencies.
"""

from __future__ import annotations

from typing import Any


def validate_victory_points(
    vp_state: list[dict[str, Any]],
) -> tuple[list[str] | None, str | None]:
    """Validate victory points from state.

    Args:
        vp_state: List of victory point dicts with description

    Returns:
        Tuple of (normalized_vps, error_message)
    """
    if not vp_state:
        return [], None

    normalized: list[str] = []
    for idx, vp in enumerate(vp_state, 1):
        description = str(vp.get("description", "")).strip()
        if not description:
            return None, f"Victory Point {idx}: Description cannot be empty"
        normalized.append(description)

    return normalized, None
