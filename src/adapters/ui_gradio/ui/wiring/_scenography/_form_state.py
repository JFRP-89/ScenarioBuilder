"""Scenography form state management.

Pure functions that transform element data into flat form dicts.
No Gradio, no side effects.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.units import convert_from_cm

# Sentinel: "don't update this field"
UNCHANGED = object()

CIRCLE_DEFAULTS: dict[str, int] = {"cx": 90, "cy": 90, "r": 15}
RECT_DEFAULTS: dict[str, int] = {"x": 30, "y": 30, "width": 40, "height": 30}


def default_scenography_form() -> dict[str, Any]:
    """Return form dict with all defaults (add / cancel mode)."""
    return {
        "description": "",
        "type": "circle",
        "cx": CIRCLE_DEFAULTS["cx"],
        "cy": CIRCLE_DEFAULTS["cy"],
        "r": CIRCLE_DEFAULTS["r"],
        "x": RECT_DEFAULTS["x"],
        "y": RECT_DEFAULTS["y"],
        "width": RECT_DEFAULTS["width"],
        "height": RECT_DEFAULTS["height"],
        "polygon_points": UNCHANGED,
        "allow_overlap": False,
        "editing_id": None,
    }


def selected_scenography_form(
    elem: dict[str, Any],
    scenography_unit: str,
) -> dict[str, Any]:
    """Build form dict from an existing scenography element.

    Values for form fields not relevant to the element's type
    are set to ``UNCHANGED``.
    """
    data = elem.get("data", {})
    elem_type = elem.get("type", "circle")
    desc = data.get("description", "")
    overlap = elem.get("allow_overlap", False)

    form: dict[str, Any] = {
        "description": desc,
        "type": elem_type,
        "allow_overlap": overlap,
        "editing_id": elem.get("id"),
        "cx": UNCHANGED,
        "cy": UNCHANGED,
        "r": UNCHANGED,
        "x": UNCHANGED,
        "y": UNCHANGED,
        "width": UNCHANGED,
        "height": UNCHANGED,
        "polygon_points": UNCHANGED,
    }

    if elem_type == "circle":
        cx_cm = float(data.get("cx", 0)) / 10.0
        cy_cm = float(data.get("cy", 0)) / 10.0
        r_cm = float(data.get("r", 0)) / 10.0
        form["cx"] = round(convert_from_cm(cx_cm, scenography_unit), 2)
        form["cy"] = round(convert_from_cm(cy_cm, scenography_unit), 2)
        form["r"] = round(convert_from_cm(r_cm, scenography_unit), 2)
    elif elem_type == "rect":
        x_cm = float(data.get("x", 0)) / 10.0
        y_cm = float(data.get("y", 0)) / 10.0
        w_cm = float(data.get("width", 0)) / 10.0
        h_cm = float(data.get("height", 0)) / 10.0
        form["x"] = round(convert_from_cm(x_cm, scenography_unit), 2)
        form["y"] = round(convert_from_cm(y_cm, scenography_unit), 2)
        form["width"] = round(convert_from_cm(w_cm, scenography_unit), 2)
        form["height"] = round(convert_from_cm(h_cm, scenography_unit), 2)
    else:
        # polygon — convert mm → display unit
        points = data.get("points", [])
        points_display: list[list[float]] = []
        for p in points:
            if isinstance(p, dict):
                px_cm = float(p.get("x", 0)) / 10.0
                py_cm = float(p.get("y", 0)) / 10.0
            else:
                px_cm = float(p[0]) / 10.0
                py_cm = float(p[1]) / 10.0
            points_display.append(
                [
                    round(convert_from_cm(px_cm, scenography_unit), 2),
                    round(convert_from_cm(py_cm, scenography_unit), 2),
                ]
            )
        form["polygon_points"] = points_display

    return form
