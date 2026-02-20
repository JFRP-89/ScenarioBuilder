"""Scenography state helpers."""

from __future__ import annotations

import uuid
from typing import Any

from adapters.ui_gradio._state._geometry import (
    shapes_overlap,
    validate_shape_within_table,
)

_MAX_SCENOGRAPHY = 6
_MAX_SOLID = 3  # solid elements (no overlap)
_MAX_PASSABLE = 3  # passable elements (overlap allowed)


def _check_scenography_limits(
    current_state: list[dict[str, Any]],
    allow_overlap: bool,
    *,
    exclude_id: str = "",
) -> str | None:
    """Return an error message if adding/switching would exceed limits, else None."""
    items = [e for e in current_state if e.get("id") != exclude_id]
    if len(items) >= _MAX_SCENOGRAPHY and not exclude_id:
        return f"Maximum {_MAX_SCENOGRAPHY} scenography elements reached."

    n_solid = sum(1 for e in items if not e.get("allow_overlap", False))
    n_passable = sum(1 for e in items if e.get("allow_overlap", False))

    if not allow_overlap and n_solid >= _MAX_SOLID:
        return f"Maximum {_MAX_SOLID} solid elements (allow_overlap=false) reached."
    if allow_overlap and n_passable >= _MAX_PASSABLE:
        return (
            f"Maximum {_MAX_PASSABLE} passable elements (allow_overlap=true) reached."
        )
    return None


def _build_element_data(
    element_type: str,
    form_data: dict[str, Any],
    elem_id: str,
    description: str,
) -> tuple[dict[str, Any], str, None] | tuple[None, None, str]:
    """Build data dict and label for a scenography element.

    Returns ``(data, label, None)`` on success or
    ``(None, None, error_msg)`` on failure.
    """
    data: dict[str, Any] = {"type": element_type}
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
        return None, None, f"Unknown element type: {element_type}"

    return data, label, None


def _check_overlap(
    data: dict[str, Any],
    allow_overlap: bool,
    current_state: list[dict[str, Any]],
    exclude_id: str = "",
) -> str | None:
    """Return error message if shape overlaps with existing solid shapes."""
    if allow_overlap:
        return None
    for existing in current_state:
        if existing.get("id") == exclude_id:
            continue
        if not existing.get("allow_overlap", False) and shapes_overlap(
            data, existing["data"]
        ):
            return f"Shape overlaps with {existing['label']}"
    return None


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
    limit_err = _check_scenography_limits(current_state, allow_overlap)
    if limit_err:
        return current_state, limit_err

    elem_id = str(uuid.uuid4())[:8]
    description = description.strip() if description else ""

    data, label, err = _build_element_data(
        element_type,
        form_data,
        elem_id,
        description,
    )
    if err or data is None:
        return current_state, err

    error = validate_shape_within_table(data, table_width_mm, table_height_mm)
    if error:
        return current_state, error

    overlap_err = _check_overlap(data, allow_overlap, current_state)
    if overlap_err:
        return current_state, overlap_err

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


def update_scenography_element(
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
    # ── Check allow_overlap balance when changing ────────────────
    old_elem = next((e for e in current_state if e["id"] == elem_id), None)
    if old_elem is not None and old_elem.get("allow_overlap", False) != allow_overlap:
        limit_err = _check_scenography_limits(
            current_state,
            allow_overlap,
            exclude_id=elem_id,
        )
        if limit_err:
            return current_state, limit_err

    description = description.strip() if description else ""

    data, label, err = _build_element_data(
        element_type,
        form_data,
        elem_id,
        description,
    )
    if err or data is None:
        return current_state, err

    error = validate_shape_within_table(data, table_width_mm, table_height_mm)
    if error:
        return current_state, error

    overlap_err = _check_overlap(
        data,
        allow_overlap,
        current_state,
        exclude_id=elem_id,
    )
    if overlap_err:
        return current_state, overlap_err

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
