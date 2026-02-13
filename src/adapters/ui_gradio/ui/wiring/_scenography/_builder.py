"""Scenography data builder — validation and construction.

Pure, never-raises functions.  No Gradio, no state mutation.
"""

from __future__ import annotations

from typing import Any, cast

from adapters.ui_gradio.units import convert_to_cm

from ._polygon import parse_polygon_points


def build_scenography_data(  # noqa: C901
    description: str,
    elem_type: str,
    cx: float,
    cy: float,
    r: float,
    x: float,
    y: float,
    width: float,
    height: float,
    points_data: list[list[Any]],
    allow_overlap: bool,
    table_width_val: float,
    table_height_val: float,
    table_unit_val: str,
    scenography_unit_val: str,
) -> dict[str, Any]:
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
    desc = (description or "").strip()
    if not desc:
        return {
            "ok": False,
            "message": "Scenography Element requires Description to be filled.",
        }

    if not elem_type or not elem_type.strip():
        return {
            "ok": False,
            "message": "Scenography Element requires Type to be selected.",
        }

    table_w_mm = int(convert_to_cm(table_width_val, table_unit_val) * 10)
    table_h_mm = int(convert_to_cm(table_height_val, table_unit_val) * 10)

    form_data: dict[str, Any]

    if elem_type == "circle":
        if cx is None or cx < 0:
            return {"ok": False, "message": "Circle requires Center X >= 0."}
        if cy is None or cy < 0:
            return {"ok": False, "message": "Circle requires Center Y >= 0."}
        if r is None or r <= 0:
            return {"ok": False, "message": "Circle requires Radius > 0."}
        form_data = {
            "cx": int(convert_to_cm(cx, scenography_unit_val) * 10),
            "cy": int(convert_to_cm(cy, scenography_unit_val) * 10),
            "r": int(convert_to_cm(r, scenography_unit_val) * 10),
        }
    elif elem_type == "rect":
        if x is None or x < 0:
            return {"ok": False, "message": "Rectangle requires X >= 0."}
        if y is None or y < 0:
            return {"ok": False, "message": "Rectangle requires Y >= 0."}
        if width is None or width <= 0:
            return {"ok": False, "message": "Rectangle requires Width > 0."}
        if height is None or height <= 0:
            return {"ok": False, "message": "Rectangle requires Height > 0."}
        form_data = {
            "x": int(convert_to_cm(x, scenography_unit_val) * 10),
            "y": int(convert_to_cm(y, scenography_unit_val) * 10),
            "width": int(convert_to_cm(width, scenography_unit_val) * 10),
            "height": int(convert_to_cm(height, scenography_unit_val) * 10),
        }
    else:
        # polygon
        points_list, error_msg = parse_polygon_points(points_data, scenography_unit_val)
        if error_msg:
            return {"ok": False, "message": error_msg}
        form_data = cast(dict[str, Any], {"points": points_list})

    return {
        "ok": True,
        "data": form_data,
        "elem_type": elem_type,
        "description": desc,
        "allow_overlap": allow_overlap,
        "table_w_mm": table_w_mm,
        "table_h_mm": table_h_mm,
    }
