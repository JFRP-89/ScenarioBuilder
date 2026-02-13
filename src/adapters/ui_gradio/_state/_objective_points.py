"""Objective points state helpers."""

from __future__ import annotations

import uuid
from typing import Any


def add_objective_point(
    current_state: list[dict[str, Any]],
    cx: float,
    cy: float,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Add a new objective point to state.

    Returns:
        Tuple of (updated_state, error_message).
    """
    # Check max 10 limit
    if len(current_state) >= 10:
        return current_state, "Maximum 10 objective points allowed per board"

    # Validate bounds
    if cx < 0 or cx > table_width_mm:
        return (
            current_state,
            f"Objective point X coordinate {cx} out of bounds (0-{table_width_mm})",
        )
    if cy < 0 or cy > table_height_mm:
        return (
            current_state,
            f"Objective point Y coordinate {cy} out of bounds (0-{table_height_mm})",
        )

    # Check for duplicate coordinates
    for existing_point in current_state:
        if existing_point["cx"] == cx and existing_point["cy"] == cy:
            return (
                current_state,
                f"Objective point already exists at coordinates ({cx:.0f}, {cy:.0f})",
            )

    description = description.strip() if description else ""
    new_point: dict[str, Any] = {
        "id": str(uuid.uuid4())[:8],
        "cx": cx,
        "cy": cy,
    }
    if description:
        new_point["description"] = description

    return [*current_state, new_point], None


def remove_last_objective_point(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove the last objective point from the state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_objective_point(
    current_state: list[dict[str, Any]], point_id: str
) -> list[dict[str, Any]]:
    """Remove selected objective point from state."""
    return [point for point in current_state if point.get("id") != point_id]


def get_objective_points_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from objective points state."""
    if not state:
        return [("No points", "")]
    return [
        (
            (
                f"{point.get('description', '')} ({point['cx']:.0f}, {point['cy']:.0f})"
                if point.get("description")
                else f"Point ({point['cx']:.0f}, {point['cy']:.0f})"
            ),
            point["id"],
        )
        for point in state
    ]


def update_objective_point(
    current_state: list[dict[str, Any]],
    point_id: str,
    cx: float,
    cy: float,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Update an existing objective point in place.

    Validates bounds and duplicate coords, excluding the point being edited.
    """
    if cx < 0 or cx > table_width_mm:
        return (
            current_state,
            f"Objective point X coordinate {cx} out of bounds (0-{table_width_mm})",
        )
    if cy < 0 or cy > table_height_mm:
        return (
            current_state,
            f"Objective point Y coordinate {cy} out of bounds (0-{table_height_mm})",
        )

    for existing_point in current_state:
        if existing_point["id"] == point_id:
            continue
        if existing_point["cx"] == cx and existing_point["cy"] == cy:
            return (
                current_state,
                f"Objective point already exists at coordinates ({cx:.0f}, {cy:.0f})",
            )

    description = description.strip() if description else ""
    updated: list[dict[str, Any]] = []
    for point in current_state:
        if point["id"] == point_id:
            new_point: dict[str, Any] = {**point, "cx": cx, "cy": cy}
            if description:
                new_point["description"] = description
            elif "description" in new_point:
                del new_point["description"]
            updated.append(new_point)
        else:
            updated.append(point)
    return updated, None
