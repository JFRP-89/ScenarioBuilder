"""SVG shape primitive rendering functions (stateless, no I/O).

Tactical-dark palette defaults.  Each primitive accepts optional
``css_class`` so the renderer can assign semantic classes (e.g.
``sb-zone-defender``).  Inline ``fill``/``stroke`` attributes
serve as fallbacks when the SVG is rendered without its
``<defs><style>`` block.
"""

from __future__ import annotations

from infrastructure.maps._renderer._sanitize import (
    escape_attr,
    escape_text,
    safe_numeric,
    safe_paint,
)
from infrastructure.maps._renderer._tactical_defs import (
    TERRAIN_FILL,
    TERRAIN_STROKE,
    TEXT_MUTED,
)

# ---------------------------------------------------------------------------
# SVG boilerplate
# ---------------------------------------------------------------------------


def svg_header(
    width: int,
    height: int,
    css_class: str = "",
    margin: float = 0.0,
) -> str:
    """Return an ``<svg ...>`` opening tag with a viewBox matching *width* x *height*.

    Parameters
    ----------
    css_class:
        Optional CSS class to add to the root ``<svg>`` element.
        Used to scope embedded ``<style>`` rules when multiple
        SVGs coexist in the same DOM (e.g. Gradio SPA tabs).
    margin:
        Extra margin (in user units) added around all four sides of
        the viewBox.  The map content still occupies ``0..width`` and
        ``0..height``; the margin is purely for overlay decorations
        (dimension cotas, compass, etc.).
    """
    cls_attr = f' class="{css_class}"' if css_class else ""
    vb_x = -margin
    vb_y = -margin
    vb_w = width + 2 * margin
    vb_h = height + 2 * margin
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{vb_w}" height="{vb_h}" '
        f'viewBox="{vb_x} {vb_y} {vb_w} {vb_h}"{cls_attr}>'
    )


# ---------------------------------------------------------------------------
# Shape primitives — tactical-dark defaults
# ---------------------------------------------------------------------------


def rect_svg(shape: dict, *, css_class: str = "") -> str:
    """Render ``<rect>`` — default styling: terrain (subtle fill)."""
    x = int(shape["x"])
    y = int(shape["y"])
    w = int(shape["width"])
    h = int(shape["height"])
    fill = safe_paint(
        str(shape.get("fill", TERRAIN_FILL)),
        TERRAIN_FILL,
    )
    stroke = safe_paint(str(shape.get("stroke", TERRAIN_STROKE)), TERRAIN_STROKE)
    stroke_width = safe_numeric(str(shape.get("stroke-width", "1")), "1")
    cls = f' class="{escape_attr(css_class)}"' if css_class else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
        f'vector-effect="non-scaling-stroke" stroke-linejoin="round"{cls} />'
    )


def circle_svg(shape: dict, *, css_class: str = "") -> str:
    """Render ``<circle>`` — default styling: terrain (subtle fill)."""
    cx = int(shape["cx"])
    cy = int(shape["cy"])
    r = int(shape["r"])
    fill = safe_paint(
        str(shape.get("fill", TERRAIN_FILL)),
        TERRAIN_FILL,
    )
    stroke = safe_paint(str(shape.get("stroke", TERRAIN_STROKE)), TERRAIN_STROKE)
    stroke_width = safe_numeric(str(shape.get("stroke-width", "1")), "1")
    cls = f' class="{escape_attr(css_class)}"' if css_class else ""
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
        f'vector-effect="non-scaling-stroke" stroke-linejoin="round"{cls} />'
    )


def polygon_svg(shape: dict, *, css_class: str = "") -> str:
    """Render ``<polygon>`` — default styling: terrain (subtle fill)."""
    points = shape["points"]
    points_str = " ".join(f'{int(p["x"])},{int(p["y"])}' for p in points)
    fill = safe_paint(
        str(shape.get("fill", TERRAIN_FILL)),
        TERRAIN_FILL,
    )
    stroke = safe_paint(str(shape.get("stroke", TERRAIN_STROKE)), TERRAIN_STROKE)
    stroke_width = safe_numeric(str(shape.get("stroke-width", "1")), "1")
    cls = f' class="{escape_attr(css_class)}"' if css_class else ""
    return (
        f'<polygon points="{points_str}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
        f'vector-effect="non-scaling-stroke" stroke-linejoin="round"{cls} />'
    )


def objective_point_svg(shape: dict, *, index: int = 0) -> str:
    """Render an objective marker: dark circle + amber ring + number.

    Parameters
    ----------
    shape:
        Must contain ``cx``, ``cy``; ``r`` defaults to 25.
    index:
        1-based objective number shown inside the marker.
        If 0, the number is omitted.
    """
    cx = int(shape["cx"])
    cy = int(shape["cy"])
    r = 25
    parts = [
        # outer ring with glow
        f'<circle cx="{cx}" cy="{cy}" r="{r}" '
        f'class="sb-objective-ring" fill="#101820" '
        f'stroke="#f6d41c" stroke-width="2.4" '
        f'vector-effect="non-scaling-stroke" '
        f'filter="url(#sb-glow-accent)" />',
    ]
    if index:
        parts.append(
            f'<text x="{cx}" y="{cy}" class="sb-objective-num" '
            f'fill="#f6d41c" font-size="22" font-weight="bold" '
            f'text-anchor="middle" dominant-baseline="central" '
            f"font-family=\"'JetBrains Mono', monospace\">"
            f"{index}</text>"
        )
    return "".join(parts)


def shape_svg(shape: dict, *, css_class: str = "", obj_index: int = 0) -> str | None:
    """Dispatch to the correct primitive renderer based on shape type."""
    shape_type = shape.get("type")
    if shape_type == "rect":
        return rect_svg(shape, css_class=css_class)
    if shape_type == "circle":
        return circle_svg(shape, css_class=css_class)
    if shape_type == "polygon":
        return polygon_svg(shape, css_class=css_class)
    if shape_type == "objective_point":
        return objective_point_svg(shape, index=obj_index)
    return None


def text_label_svg(
    x: int,
    y: int,
    text: str,
    font_size: int = 13,
    fill: str = "",
    direction: str = "up",
    css_class: str = "sb-label",
) -> str:
    """Render a text label at specified coordinates.

    Applies rotation for ``left`` / ``right`` directions.
    Uses tactical-dark muted colour by default.
    """
    escaped = escape_text(text)
    # Use muted colour as default; keep backward-compat override
    effective_fill = fill if fill else TEXT_MUTED
    safe_fill = escape_attr(safe_paint(effective_fill, TEXT_MUTED))
    cls = f' class="{escape_attr(css_class)}"' if css_class else ""
    text_elem = (
        f'<text x="{x}" y="{y}" '
        f'text-anchor="middle" dominant-baseline="middle" '
        f'font-size="{font_size}" '
        f"font-family=\"'JetBrains Mono', monospace\" "
        f'fill="{safe_fill}" font-weight="bold" '
        f'paint-order="stroke fill" '
        f'stroke="#101820" stroke-width="3" stroke-linejoin="round"{cls}>'
        f"{escaped}</text>"
    )

    if direction == "right":
        return f'<g transform="rotate(90 {x} {y})">{text_elem}</g>'
    elif direction == "left":
        return f'<g transform="rotate(-90 {x} {y})">{text_elem}</g>'
    else:
        return text_elem
