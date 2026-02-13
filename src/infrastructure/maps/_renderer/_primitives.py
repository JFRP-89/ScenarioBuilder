"""SVG shape primitive rendering functions (stateless, no I/O)."""

from __future__ import annotations

from infrastructure.maps._renderer._sanitize import (
    escape_attr,
    escape_text,
    safe_numeric,
    safe_paint,
)

# ---------------------------------------------------------------------------
# SVG boilerplate
# ---------------------------------------------------------------------------


def svg_header(width: int, height: int) -> str:
    """Return an ``<svg ...>`` opening tag with a viewBox matching *width*x*height*."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )


# ---------------------------------------------------------------------------
# Shape primitives
# ---------------------------------------------------------------------------


def rect_svg(shape: dict) -> str:
    """Render rect with deployment zone styling (semi-transparent fill)."""
    x = int(shape["x"])
    y = int(shape["y"])
    w = int(shape["width"])
    h = int(shape["height"])
    fill = safe_paint(
        str(shape.get("fill", "rgba(100,150,250,0.3)")),
        "rgba(100,150,250,0.3)",
    )
    stroke = safe_paint(str(shape.get("stroke", "#4070c0")), "#4070c0")
    stroke_width = safe_numeric(str(shape.get("stroke-width", "2")), "2")
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
    )


def circle_svg(shape: dict) -> str:
    """Render circle with scenography styling (gray outline, transparent fill)."""
    cx = int(shape["cx"])
    cy = int(shape["cy"])
    r = int(shape["r"])
    fill = safe_paint(
        str(shape.get("fill", "rgba(128,128,128,0.2)")),
        "rgba(128,128,128,0.2)",
    )
    stroke = safe_paint(str(shape.get("stroke", "#666")), "#666")
    stroke_width = safe_numeric(str(shape.get("stroke-width", "2")), "2")
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
    )


def polygon_svg(shape: dict) -> str:
    """Render polygon with deployment zone styling."""
    points = shape["points"]
    points_str = " ".join(f'{int(p["x"])},{int(p["y"])}' for p in points)
    fill = safe_paint(
        str(shape.get("fill", "rgba(250,100,100,0.3)")),
        "rgba(250,100,100,0.3)",
    )
    stroke = safe_paint(str(shape.get("stroke", "#c04040")), "#c04040")
    stroke_width = safe_numeric(str(shape.get("stroke-width", "2")), "2")
    return (
        f'<polygon points="{points_str}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
    )


def objective_point_svg(shape: dict) -> str:
    """Render an objective_point as a black filled circle with radius 25mm."""
    cx = int(shape["cx"])
    cy = int(shape["cy"])
    r = 25
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="black" stroke="black" />'


def shape_svg(shape: dict) -> str | None:
    """Dispatch to the correct primitive renderer based on shape type."""
    shape_type = shape.get("type")
    if shape_type == "rect":
        return rect_svg(shape)
    if shape_type == "circle":
        return circle_svg(shape)
    if shape_type == "polygon":
        return polygon_svg(shape)
    if shape_type == "objective_point":
        return objective_point_svg(shape)
    return None


def text_label_svg(
    x: int,
    y: int,
    text: str,
    font_size: int = 16,
    fill: str = "#000",
    direction: str = "up",
) -> str:
    """Render a text label at specified coordinates.

    Applies rotation for ``left`` / ``right`` directions.
    """
    escaped = escape_text(text)
    safe_fill = escape_attr(safe_paint(fill, "#000"))
    text_elem = (
        f'<text x="{x}" y="{y}" '
        f'text-anchor="middle" dominant-baseline="middle" '
        f'font-size="{font_size}" font-family="Arial, sans-serif" '
        f'fill="{safe_fill}" font-weight="bold">'
        f"{escaped}</text>"
    )

    if direction == "right":
        return f'<g transform="rotate(90 {x} {y})">{text_elem}</g>'
    elif direction == "left":
        return f'<g transform="rotate(-90 {x} {y})">{text_elem}</g>'
    else:
        return text_elem
