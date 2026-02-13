"""Optional text-field helpers for payload construction.

Pure functions — no side effects, no UI dependencies.
"""

from __future__ import annotations

from typing import Any


def apply_optional_text_fields(
    payload: dict[str, Any],
    deployment: str | None = None,
    layout: str | None = None,
    objectives: str | None = None,
    initial_priority: str | None = None,
    armies: str | None = None,
    name: str | None = None,
) -> None:
    """Add optional text fields to payload if provided.

    Args:
        payload: Request payload (modified in-place)
        deployment: Deployment text
        layout: Layout text
        objectives: Objectives text
        initial_priority: Initial priority text
        armies: Armies text
        name: Scenario name
    """
    field_map = {
        "armies": armies,
        "deployment": deployment,
        "layout": layout,
        "objectives": objectives,
        "initial_priority": initial_priority,
        "name": name,
    }

    for key, value in field_map.items():
        if value and value.strip():
            payload[key] = value.strip()
