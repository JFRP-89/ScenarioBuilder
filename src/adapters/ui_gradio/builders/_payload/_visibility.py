"""Visibility helpers for payload construction.

Pure functions — no side effects, no UI dependencies.
"""

from __future__ import annotations

from typing import Any


def apply_visibility(
    payload: dict[str, Any],
    visibility: str,
    shared_with_text: str | None = None,
) -> None:
    """Add visibility configuration to payload.

    Args:
        payload: Request payload (modified in-place)
        visibility: Visibility level ("private", "public", "shared")
        shared_with_text: Comma-separated user IDs (for shared visibility)
    """
    payload["visibility"] = visibility

    if visibility == "shared" and shared_with_text and shared_with_text.strip():
        users = [u.strip() for u in shared_with_text.split(",") if u.strip()]
        if users:
            payload["shared_with"] = users
