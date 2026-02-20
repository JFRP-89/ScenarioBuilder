"""Scenography data builder — validation and construction.

Pure, never-raises functions.  No Gradio, no state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from adapters.ui_gradio.units import to_mm

from ._polygon import parse_polygon_points

# ── Per-type builders ───────────────────────────────────────────────────


def _build_circle(
    cx: float,
    cy: float,
    r: float,
    unit: str,
) -> dict[str, Any] | str:
    """Validate and build circle data. Returns error string on failure."""
    if cx is None or cx < 0:
        return "Circle requires Center X >= 0."
    if cy is None or cy < 0:
        return "Circle requires Center Y >= 0."
    if r is None or r <= 0:
        return "Circle requires Radius > 0."
    return {
        "cx": to_mm(cx, unit),
        "cy": to_mm(cy, unit),
        "r": to_mm(r, unit),
    }


def _build_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    unit: str,
) -> dict[str, Any] | str:
    """Validate and build rectangle data. Returns error string on failure."""
    if x is None or x < 0:
        return "Rectangle requires X >= 0."
    if y is None or y < 0:
        return "Rectangle requires Y >= 0."
    if width is None or width <= 0:
        return "Rectangle requires Width > 0."
    if height is None or height <= 0:
        return "Rectangle requires Height > 0."
    return {
        "x": to_mm(x, unit),
        "y": to_mm(y, unit),
        "width": to_mm(width, unit),
        "height": to_mm(height, unit),
    }


def _build_polygon(
    points_data: list[list[Any]],
    unit: str,
) -> dict[str, Any] | str:
    """Validate and build polygon data. Returns error string on failure."""
    points_list, error_msg = parse_polygon_points(points_data, unit)
    if error_msg:
        return error_msg
    return cast(dict[str, Any], {"points": points_list})


# ── Public entry point ─────────────────────────────────────────────────


@dataclass(frozen=True)
class ScenographyFormInput:
    """Immutable bundle of form values for scenography element creation."""

    description: str
    elem_type: str
    cx: float
    cy: float
    r: float
    x: float
    y: float
    width: float
    height: float
    points_data: list[list[Any]]
    allow_overlap: bool
    table_width_val: float
    table_height_val: float
    table_unit_val: str
    scenography_unit_val: str


def build_scenography_data(form: ScenographyFormInput) -> dict[str, Any]:
    """Validate form inputs and build scenography element data.

    **Never raises.**

    Returns a dict with shape::

        {"ok": True,
         "data": <form_data>,
         "elem_type": str,
         "description": str,
         "allow_overlap": bool,
         "table_w_mm": int,
         "table_h_mm": int}

    or::

        {"ok": False, "message": str}
    """
    desc = (form.description or "").strip()
    if not desc:
        return {
            "ok": False,
            "message": "Scenography Element requires Description to be filled.",
        }

    if not form.elem_type or not form.elem_type.strip():
        return {
            "ok": False,
            "message": "Scenography Element requires Type to be selected.",
        }

    table_w_mm = to_mm(form.table_width_val, form.table_unit_val)
    table_h_mm = to_mm(form.table_height_val, form.table_unit_val)

    builders = {
        "circle": lambda: _build_circle(
            form.cx,
            form.cy,
            form.r,
            form.scenography_unit_val,
        ),
        "rect": lambda: _build_rect(
            form.x,
            form.y,
            form.width,
            form.height,
            form.scenography_unit_val,
        ),
    }
    builder = builders.get(form.elem_type)
    result = (
        builder()
        if builder
        else _build_polygon(
            form.points_data,
            form.scenography_unit_val,
        )
    )

    if isinstance(result, str):
        return {"ok": False, "message": result}

    return {
        "ok": True,
        "data": result,
        "elem_type": form.elem_type,
        "description": desc,
        "allow_overlap": form.allow_overlap,
        "table_w_mm": table_w_mm,
        "table_h_mm": table_h_mm,
    }
