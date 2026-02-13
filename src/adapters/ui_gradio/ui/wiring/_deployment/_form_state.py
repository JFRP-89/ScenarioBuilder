"""Pure form-state helpers for the deployment-zone form.

Every function returns plain dicts/values — **no Gradio dependency**.
The sentinel ``UNCHANGED`` means "do not modify the current widget value".
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.units import convert_unit_to_unit

# ---------------------------------------------------------------------------
# Sentinel — the UI layer should emit ``gr.update()`` (no-op) for this.
# ---------------------------------------------------------------------------
UNCHANGED: object = object()


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
def default_zone_form() -> dict[str, Any]:
    """Return default (reset) values for every field in the zone form."""
    return {
        # Value fields
        "zone_type": "rectangle",
        "border": "north",
        "corner": "north-west",
        "fill_side": True,
        "perfect_triangle": True,
        "description": "",
        "width": 120,
        "height": 20,
        "triangle_side1": 30,
        "triangle_side2": 30,
        "circle_radius": 30,
        "sep_x": 0,
        "sep_y": 0,
        # Row visibility
        "border_row_visible": True,
        "corner_row_visible": False,
        "fill_side_row_visible": True,
        "perfect_triangle_row_visible": False,
        "rect_dimensions_row_visible": True,
        "triangle_dimensions_row_visible": False,
        "circle_dimensions_row_visible": False,
        "separation_row_visible": True,
        # Editing state
        "editing_id": None,
        "add_btn_text": "+ Add Zone",
        "cancel_btn_visible": False,
    }


# ---------------------------------------------------------------------------
# Reconstruct form from stored zone
# ---------------------------------------------------------------------------
def selected_zone_form(zone: dict[str, Any], *, zone_unit: str) -> dict[str, Any]:
    """Reconstruct form field values from a stored zone dict.

    Parameters
    ----------
    zone:
        A zone entry from ``deployment_zones_state``.  Expected keys:
        ``id``, ``form_type``, ``form_params``, ``data``.
    zone_unit:
        The current display unit selected by the user (``"cm"``, ``"in"``,
        ``"ft"``).

    Returns
    -------
    dict[str, Any]
        Same key-set as :func:`default_zone_form`.  Shape-specific fields
        that do not apply are set to :data:`UNCHANGED`.
    """
    form_params: dict[str, Any] = zone.get("form_params", {})
    form_type: str = zone.get("form_type", "rectangle")
    data: dict[str, Any] = zone.get("data", {})
    desc: str = data.get("description", "")

    is_rect = form_type == "rectangle"
    is_triangle = form_type == "triangle"
    is_circle = form_type == "circle"

    result: dict[str, Any] = {
        "description": desc,
        "zone_type": form_type,
        # Visibility
        "border_row_visible": is_rect,
        "corner_row_visible": is_triangle or is_circle,
        "fill_side_row_visible": is_rect,
        "perfect_triangle_row_visible": is_triangle,
        "rect_dimensions_row_visible": is_rect,
        "triangle_dimensions_row_visible": is_triangle,
        "circle_dimensions_row_visible": is_circle,
        "separation_row_visible": is_rect,
        # Editing
        "editing_id": zone.get("id"),
        "add_btn_text": "\u270f\ufe0f Update Zone",
        "cancel_btn_visible": True,
    }

    # Pre-fill all shape-specific fields as UNCHANGED
    for key in (
        "border",
        "corner",
        "fill_side",
        "perfect_triangle",
        "width",
        "height",
        "sep_x",
        "sep_y",
        "triangle_side1",
        "triangle_side2",
        "circle_radius",
    ):
        result[key] = UNCHANGED

    if not form_params:
        return result

    stored_unit: str = form_params.get("unit", "cm")

    if is_rect:
        w = form_params.get("width", 120)
        h = form_params.get("height", 20)
        sx = form_params.get("sep_x", 0)
        sy = form_params.get("sep_y", 0)
        if stored_unit != zone_unit:
            w = convert_unit_to_unit(w, stored_unit, zone_unit)
            h = convert_unit_to_unit(h, stored_unit, zone_unit)
            sx = convert_unit_to_unit(sx, stored_unit, zone_unit)
            sy = convert_unit_to_unit(sy, stored_unit, zone_unit)
        result["border"] = form_params.get("border", "north")
        result["fill_side"] = form_params.get("fill_side", True)
        result["width"] = round(w, 2)
        result["height"] = round(h, 2)
        result["sep_x"] = round(sx, 2)
        result["sep_y"] = round(sy, 2)

    elif is_triangle:
        s1 = form_params.get("side1", 30)
        s2 = form_params.get("side2", 30)
        if stored_unit != zone_unit:
            s1 = convert_unit_to_unit(s1, stored_unit, zone_unit)
            s2 = convert_unit_to_unit(s2, stored_unit, zone_unit)
        result["corner"] = form_params.get("corner", "north-west")
        result["perfect_triangle"] = form_params.get("perfect_triangle", True)
        result["triangle_side1"] = round(s1, 2)
        result["triangle_side2"] = round(s2, 2)

    elif is_circle:
        r = form_params.get("radius", 30)
        if stored_unit != zone_unit:
            r = convert_unit_to_unit(r, stored_unit, zone_unit)
        result["corner"] = form_params.get("corner", "north-west")
        result["circle_radius"] = round(r, 2)

    return result
