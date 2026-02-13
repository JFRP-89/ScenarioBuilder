"""Scenography state helpers."""

from __future__ import annotations

import uuid
from typing import Any

from adapters.ui_gradio._state._geometry import (
    shapes_overlap,
    validate_shape_within_table,
)


def add_scenography_element(
    current_state: list[dict[str, Any]],
    element_type: str,
    form_data: dict[str, Any],
    allow_overlap: bool,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Add new scenography element to state."""
    elem_id = str(uuid.uuid4())[:8]
    data: dict[str, Any] = {"type": element_type}

    description = description.strip() if description else ""
    if description:
        data["description"] = description

    if element_type == "circle":
        data["cx"] = int(form_data.get("cx", 0))
        data["cy"] = int(form_data.get("cy", 0))
        data["r"] = int(form_data.get("r", 0))
        label = (
            f"{description} (Circle {elem_id})" if description else f"Circle {elem_id}"
        )

    elif element_type == "rect":
        data["x"] = int(form_data.get("x", 0))
        data["y"] = int(form_data.get("y", 0))
        data["width"] = int(form_data.get("width", 0))
        data["height"] = int(form_data.get("height", 0))
        label = f"{description} (Rect {elem_id})" if description else f"Rect {elem_id}"

    elif element_type == "polygon":
        points = form_data.get("points", [])
        data["points"] = points
        label = (
            f"{description} (Polygon {elem_id} - {len(points)} pts)"
            if description
            else f"Polygon {elem_id} ({len(points)} pts)"
        )

    else:
        return current_state, f"Unknown element type: {element_type}"

    error = validate_shape_within_table(data, table_width_mm, table_height_mm)
    if error:
        return current_state, error

    if not allow_overlap:
        for existing in current_state:
            if not existing.get("allow_overlap", False) and shapes_overlap(
                data, existing["data"]
            ):
                return current_state, f"Shape overlaps with {existing['label']}"

    new_element = {
        "id": elem_id,
        "type": element_type,
        "label": label,
        "data": data,
        "allow_overlap": allow_overlap,
    }

    return [*current_state, new_element], None


def remove_last_scenography_element(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove last element from scenography state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_scenography_element(
    current_state: list[dict[str, Any]], selected_id: str
) -> list[dict[str, Any]]:
    """Remove selected element from scenography state."""
    return [elem for elem in current_state if elem["id"] != selected_id]


def get_scenography_choices(state: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Get dropdown choices from scenography state."""
    if not state:
        return [("No elements", "")]
    return [(elem["label"], elem["id"]) for elem in state]


def update_scenography_element(  # noqa: C901
    current_state: list[dict[str, Any]],
    elem_id: str,
    element_type: str,
    form_data: dict[str, Any],
    allow_overlap: bool,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Update an existing scenography element in place.

    Validates bounds and overlap with other elements (excluding self).
    """
    data: dict[str, Any] = {"type": element_type}

    description = description.strip() if description else ""
    if description:
        data["description"] = description

    if element_type == "circle":
        data["cx"] = int(form_data.get("cx", 0))
        data["cy"] = int(form_data.get("cy", 0))
        data["r"] = int(form_data.get("r", 0))
        label = (
            f"{description} (Circle {elem_id})" if description else f"Circle {elem_id}"
        )
    elif element_type == "rect":
        data["x"] = int(form_data.get("x", 0))
        data["y"] = int(form_data.get("y", 0))
        data["width"] = int(form_data.get("width", 0))
        data["height"] = int(form_data.get("height", 0))
        label = f"{description} (Rect {elem_id})" if description else f"Rect {elem_id}"
    elif element_type == "polygon":
        points = form_data.get("points", [])
        data["points"] = points
        label = (
            f"{description} (Polygon {elem_id} - {len(points)} pts)"
            if description
            else f"Polygon {elem_id} ({len(points)} pts)"
        )
    else:
        return current_state, f"Unknown element type: {element_type}"

    error = validate_shape_within_table(data, table_width_mm, table_height_mm)
    if error:
        return current_state, error

    if not allow_overlap:
        for existing in current_state:
            if existing["id"] == elem_id:
                continue
            if not existing.get("allow_overlap", False) and shapes_overlap(
                data, existing["data"]
            ):
                return current_state, f"Shape overlaps with {existing['label']}"

    updated_state: list[dict[str, Any]] = []
    for elem in current_state:
        if elem["id"] == elem_id:
            updated_state.append(
                {
                    "id": elem_id,
                    "type": element_type,
                    "label": label,
                    "data": data,
                    "allow_overlap": allow_overlap,
                }
            )
        else:
            updated_state.append(elem)
    return updated_state, None
