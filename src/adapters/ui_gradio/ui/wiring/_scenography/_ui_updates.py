"""Scenography UI field visibility and coordinate conversion.

Pure functions — no Gradio, no widgets.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.units import convert_unit_to_unit

from ._polygon import convert_polygon_points


def scenography_type_visibility(elem_type: str) -> dict[str, bool]:
    """Which form sections should be visible for the given element type."""
    return {
        "circle": elem_type == "circle",
        "rect": elem_type == "rect",
        "polygon": elem_type == "polygon",
    }


def convert_scenography_coordinates(
    cx: float,
    cy: float,
    r: float,
    x: float,
    y: float,
    width: float,
    height: float,
    polygon_data: Any,
    prev_unit: str,
    new_unit: str,
) -> tuple[float, float, float, float, float, float, float, Any, str]:
    """Convert all scenography form coordinates between units.

    Returns ``(cx, cy, r, x, y, width, height, polygon_data, new_unit)``.
    Does nothing if *prev_unit* == *new_unit*.
    """
    if prev_unit == new_unit:
        return cx, cy, r, x, y, width, height, polygon_data, new_unit

    return (
        convert_unit_to_unit(cx, prev_unit, new_unit),
        convert_unit_to_unit(cy, prev_unit, new_unit),
        convert_unit_to_unit(r, prev_unit, new_unit),
        convert_unit_to_unit(x, prev_unit, new_unit),
        convert_unit_to_unit(y, prev_unit, new_unit),
        convert_unit_to_unit(width, prev_unit, new_unit),
        convert_unit_to_unit(height, prev_unit, new_unit),
        convert_polygon_points(polygon_data, prev_unit, new_unit),
        new_unit,
    )
