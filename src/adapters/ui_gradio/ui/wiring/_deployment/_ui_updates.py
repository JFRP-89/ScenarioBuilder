"""Pure UI-state helpers for deployment-zone form updates.

Functions here compute *what* to show / hide / lock, returning plain
dicts with string keys.  **No Gradio dependency.**
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Zone-type row visibility
# ---------------------------------------------------------------------------
def zone_type_visibility(zone_type: str) -> dict[str, bool]:
    """Return row-visibility flags for a given zone type.

    Keys match the ``*_row_visible`` convention used by ``_form_state``.
    """
    is_rect = zone_type == "rectangle"
    is_triangle = zone_type == "triangle"
    is_circle = zone_type == "circle"
    return {
        "border_row": is_rect,
        "corner_row": is_triangle or is_circle,
        "fill_side_row": is_rect,
        "perfect_triangle_row": is_triangle,
        "rect_dimensions_row": is_rect,
        "triangle_dimensions_row": is_triangle,
        "circle_dimensions_row": is_circle,
        "separation_row": is_rect,
    }


# ---------------------------------------------------------------------------
# Border / fill-side field locking
# ---------------------------------------------------------------------------
def border_fill_field_states(
    border: str,
    fill_side: bool,
    table_w_unit: float,
    table_h_unit: float,
    zone_unit: str,
) -> dict[str, dict[str, object]]:
    """Compute per-field state dicts for the border/fill_side change handler.

    Returns a dict keyed by field name (``"width"``, ``"height"``,
    ``"sep_x"``, ``"sep_y"``).  Each value is a dict with optional keys:

    * ``value`` — new numeric value (only when locked)
    * ``interactive`` — ``True`` / ``False``
    * ``label`` — display label string
    """
    locked_suffix = " [LOCKED]"

    if fill_side:
        if border in ("north", "south"):
            return {
                "width": {
                    "value": round(table_w_unit, 2),
                    "interactive": False,
                    "label": f"Width ({zone_unit}){locked_suffix}",
                },
                "height": {
                    "interactive": True,
                    "label": f"Height ({zone_unit})",
                },
                "sep_x": {
                    "value": 0,
                    "interactive": False,
                    "label": f"Separation X ({zone_unit}){locked_suffix}",
                },
                "sep_y": {
                    "interactive": True,
                    "label": f"Separation Y ({zone_unit})",
                },
            }
        else:
            return {
                "width": {
                    "interactive": True,
                    "label": f"Width ({zone_unit})",
                },
                "height": {
                    "value": round(table_h_unit, 2),
                    "interactive": False,
                    "label": f"Height ({zone_unit}){locked_suffix}",
                },
                "sep_x": {
                    "interactive": True,
                    "label": f"Separation X ({zone_unit})",
                },
                "sep_y": {
                    "value": 0,
                    "interactive": False,
                    "label": f"Separation Y ({zone_unit}){locked_suffix}",
                },
            }

    # fill_side is False — everything unlocked
    return {
        "width": {"interactive": True, "label": f"Width ({zone_unit})"},
        "height": {"interactive": True, "label": f"Height ({zone_unit})"},
        "sep_x": {"interactive": True, "label": f"Separation X ({zone_unit})"},
        "sep_y": {"interactive": True, "label": f"Separation Y ({zone_unit})"},
    }


# ---------------------------------------------------------------------------
# Perfect-triangle side2 state
# ---------------------------------------------------------------------------
def perfect_triangle_side2(
    is_perfect: bool,
    side1: float,
    zone_unit: str,
) -> dict[str, object]:
    """Compute the ``side2`` field state for the perfect-triangle toggle.

    Returns a dict with keys ``value`` (optional), ``interactive``, ``label``.
    """
    if is_perfect:
        return {
            "value": side1,
            "interactive": False,
            "label": f"Y ({zone_unit}) [LOCKED]",
        }
    return {
        "interactive": True,
        "label": f"Y ({zone_unit})",
    }
