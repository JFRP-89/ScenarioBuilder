"""Pure zone-data builder for deployment zones.

Validates form inputs and builds the ``zone_data`` / ``form_params`` dicts
that the wiring layer stores in Gradio state.  **No Gradio dependency.**

Dependencies
------------
* ``adapters.ui_gradio.units.convert_to_cm`` — unit → cm conversion
* ``adapters.ui_gradio.state_helpers.validate_separation_coords`` — rect coords
* ``_deployment._geometry`` — triangle / circle vertex calculation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.ui_gradio.state_helpers import validate_separation_coords
from adapters.ui_gradio.ui.wiring._deployment._geometry import (
    _calculate_circle_vertices,
    _calculate_triangle_vertices,
)
from adapters.ui_gradio.units import to_mm

# ── public result type aliases ──────────────────────────────────────────────
# build_zone_data returns (zone_data, form_params, error_msg)
# Exactly one of (zone_data, error_msg) is non-None.
ZoneBuildResult = tuple[
    dict[str, Any] | None,  # zone_data
    dict[str, Any] | None,  # form_params
    str | None,  # error_msg
]


@dataclass(frozen=True)
class ZoneFormInput:
    """Immutable bundle of form values for zone creation/editing."""

    zone_type: str
    description: str
    border: str
    corner: str
    fill_side: bool
    width: float
    height: float
    tri_side1: float
    tri_side2: float
    circle_radius: float
    sep_x: float
    sep_y: float
    zone_unit: str


# ── helpers ─────────────────────────────────────────────────────────────────
def _to_mm(value: float, unit: str) -> int:
    """Convert a user-unit value to integer millimetres."""
    return to_mm(value, unit)


def _validate_vertices_in_bounds(
    vertices: list[tuple[int, int]],
    table_w_mm: int,
    table_h_mm: int,
    shape_label: str,
) -> str | None:
    """Return an error message if any vertex is outside the table bounds."""
    for x, y in vertices:
        if x < 0 or x > table_w_mm or y < 0 or y > table_h_mm:
            return f"{shape_label} extends beyond table bounds: vertex ({x}, {y})"
    return None


# ── triangle ────────────────────────────────────────────────────────────────
def _build_triangle(
    *,
    corner: str,
    tri_side1: float,
    tri_side2: float,
    zone_unit: str,
    table_w_mm: int,
    table_h_mm: int,
    description: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and build a triangle zone_data dict.

    Returns ``(zone_data, None)`` on success or ``(None, error_msg)`` on failure.
    """
    if not corner or not corner.strip():
        return None, "Triangle requires Corner to be selected."
    if not tri_side1 or tri_side1 <= 0:
        return None, "Triangle requires Side Length 1 > 0."
    if not tri_side2 or tri_side2 <= 0:
        return None, "Triangle requires Side Length 2 > 0."

    side1_mm = _to_mm(tri_side1, zone_unit)
    side2_mm = _to_mm(tri_side2, zone_unit)

    try:
        vertices = _calculate_triangle_vertices(
            corner, side1_mm, side2_mm, table_w_mm, table_h_mm
        )
    except ValueError as e:
        return None, f"Invalid triangle configuration: {e}"

    bounds_err = _validate_vertices_in_bounds(
        vertices, table_w_mm, table_h_mm, "Triangle"
    )
    if bounds_err:
        return None, bounds_err

    points_dict = [{"x": int(x), "y": int(y)} for x, y in vertices]
    zone_data: dict[str, Any] = {
        "type": "polygon",
        "description": description,
        "points": points_dict,
        "corner": corner,
    }
    return zone_data, None


# ── circle ──────────────────────────────────────────────────────────────────
def _build_circle(
    *,
    corner: str,
    circle_radius: float,
    zone_unit: str,
    table_w_mm: int,
    table_h_mm: int,
    description: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and build a circle (quarter-arc) zone_data dict."""
    if not corner or not corner.strip():
        return None, "Circle requires Corner to be selected."
    if not circle_radius or circle_radius <= 0:
        return None, "Circle requires Radius > 0."

    radius_mm = _to_mm(circle_radius, zone_unit)

    try:
        vertices = _calculate_circle_vertices(corner, radius_mm, table_w_mm, table_h_mm)
    except ValueError as e:
        return None, f"Invalid circle configuration: {e}"

    bounds_err = _validate_vertices_in_bounds(
        vertices, table_w_mm, table_h_mm, "Circle"
    )
    if bounds_err:
        return None, bounds_err

    points_dict = [{"x": int(x), "y": int(y)} for x, y in vertices]
    zone_data: dict[str, Any] = {
        "type": "polygon",
        "description": description,
        "points": points_dict,
        "corner": corner,
    }
    return zone_data, None


# ── rectangle ───────────────────────────────────────────────────────────────
def _build_rectangle(
    *,
    border: str,
    fill_side: bool,
    width: float,
    height: float,
    sep_x: float,
    sep_y: float,
    zone_unit: str,
    table_w_mm: int,
    table_h_mm: int,
    description: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and build a rectangle zone_data dict."""
    if not border or not border.strip():
        return None, "Deployment Zone requires Border to be selected."
    if not width or width <= 0:
        return None, "Deployment Zone requires Width > 0."
    if not height or height <= 0:
        return None, "Deployment Zone requires Height > 0."

    w_mm = _to_mm(width, zone_unit)
    h_mm = _to_mm(height, zone_unit)
    sx_mm = _to_mm(sep_x, zone_unit)
    sy_mm = _to_mm(sep_y, zone_unit)

    if fill_side:
        if border in ("north", "south"):
            w_mm = table_w_mm
            sx_mm = 0
        else:
            h_mm = table_h_mm
            sy_mm = 0

    _fx, _fy = validate_separation_coords(
        border, w_mm, h_mm, sx_mm, sy_mm, table_w_mm, table_h_mm
    )
    sx_mm = int(_fx)
    sy_mm = int(_fy)

    zone_data: dict[str, Any] = {
        "type": "rect",
        "description": description,
        "x": int(sx_mm),
        "y": int(sy_mm),
        "width": int(w_mm),
        "height": int(h_mm),
        "border": border,
    }
    return zone_data, None


# ── form_params builder ────────────────────────────────────────────────────
def _build_form_params(form: ZoneFormInput) -> dict[str, Any]:
    """Build the ``form_params`` dict stored alongside zone_data."""
    params: dict[str, Any] = {
        "description": form.description,
        "unit": form.zone_unit,
    }
    if form.zone_type == "triangle":
        params.update(
            corner=form.corner,
            side1=form.tri_side1,
            side2=form.tri_side2,
            perfect_triangle=(form.tri_side1 == form.tri_side2),
        )
    elif form.zone_type == "circle":
        params.update(corner=form.corner, radius=form.circle_radius)
    else:  # rectangle
        params.update(
            border=form.border,
            fill_side=form.fill_side,
            width=form.width,
            height=form.height,
            sep_x=form.sep_x,
            sep_y=form.sep_y,
        )
    return params


# ── main public API ─────────────────────────────────────────────────────────
def build_zone_data(
    form: ZoneFormInput,
    *,
    table_w_mm: int,
    table_h_mm: int,
) -> ZoneBuildResult:
    """Validate inputs and build ``zone_data`` + ``form_params``.

    Parameters
    ----------
    form : ZoneFormInput
        Immutable bundle of zone form field values.
    table_w_mm, table_h_mm : int
        Table dimensions in millimetres.

    Returns
    -------
    tuple[dict | None, dict | None, str | None]
        ``(zone_data, form_params, None)`` on success, or
        ``(None, None, error_msg)`` on validation failure.
        Never raises — all errors are returned as strings.
    """
    desc = (form.description or "").strip()
    if not desc:
        return None, None, "Deployment Zone requires Description to be filled."

    if form.zone_type == "triangle":
        zone_data, err = _build_triangle(
            corner=form.corner,
            tri_side1=form.tri_side1,
            tri_side2=form.tri_side2,
            zone_unit=form.zone_unit,
            table_w_mm=table_w_mm,
            table_h_mm=table_h_mm,
            description=desc,
        )
    elif form.zone_type == "circle":
        zone_data, err = _build_circle(
            corner=form.corner,
            circle_radius=form.circle_radius,
            zone_unit=form.zone_unit,
            table_w_mm=table_w_mm,
            table_h_mm=table_h_mm,
            description=desc,
        )
    else:  # rectangle
        zone_data, err = _build_rectangle(
            border=form.border,
            fill_side=form.fill_side,
            width=form.width,
            height=form.height,
            sep_x=form.sep_x,
            sep_y=form.sep_y,
            zone_unit=form.zone_unit,
            table_w_mm=table_w_mm,
            table_h_mm=table_h_mm,
            description=desc,
        )

    if err:
        return None, None, err

    form_params = _build_form_params(form)
    return zone_data, form_params, None
