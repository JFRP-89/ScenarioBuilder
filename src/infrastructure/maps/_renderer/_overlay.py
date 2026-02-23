"""Tactical overlay layer: dimension annotations (cotas) + compass.

Renders measurement lines with arrows on the **south** (width) and
**east** (height) edges of the map, plus a vertical N/S compass on
the right margin.  All elements live in ``<g id="layer-overlay">``
and are drawn **outside** the map area (in the expanded viewBox
margin), so they never alter existing geometry.

Design tokens reuse the palette from ``_tactical_defs``.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

# ---------------------------------------------------------------------------
# Unit-formatting utility
# ---------------------------------------------------------------------------

# Wargame conversion factors (same as domain/maps/table_size.py)
_CM_PER_INCH = Decimal("2.5")
_CM_PER_FOOT = Decimal("30.0")

# Palette tokens (kept in sync with _tactical_defs — duplicated here to
# avoid circular imports since _tactical_defs imports from this module).
_ACCENT = "#f6d41c"

# Dim-line accent (slightly desaturated amber)
_DIM_STROKE = "rgba(246,212,28,0.55)"
_DIM_STROKE_FULL = _ACCENT  # for arrow markers
_COMPASS_STROKE = "rgba(246,212,28,0.30)"
_PILL_BG = "#1a1e24"
_PILL_BORDER = "rgba(246,212,28,0.50)"
_PILL_TEXT = _ACCENT


def format_dimension(mm: int, units: str = "cm") -> str:
    """Format a dimension in *mm* for display in the requested unit system.

    Parameters
    ----------
    mm:
        Internal dimension in millimetres.
    units:
        ``"cm"`` → centimetres (integer),
        ``"in"`` → inches (1 in = 2.5 cm) with ``"`` suffix,
        ``"ft"`` → feet (1 ft = 30 cm) with ``ft`` suffix.

    Returns
    -------
    Formatted string, e.g. ``"120 cm"``, ``'48"'``, ``"4 ft"``.
    """
    cm = Decimal(mm) / 10

    if units == "in":
        inches = cm / _CM_PER_INCH
        rounded = inches.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        # Show integer if close enough
        if rounded == rounded.to_integral_value():
            return f'{int(rounded)}"'
        return f'{rounded}"'

    if units == "ft":
        feet = cm / _CM_PER_FOOT
        rounded = feet.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        if rounded == rounded.to_integral_value():
            return f"{int(rounded)} ft"
        return f"{rounded} ft"

    # Default: cm (integer - mm is always a multiple of 10 in practice)
    return f"{int(cm)} cm"


# ---------------------------------------------------------------------------
# SVG defs for overlay markers
# ---------------------------------------------------------------------------


def overlay_defs() -> str:
    """Return ``<defs>`` content for dimension-arrow markers and glow filter."""
    return (
        # Arrow marker — end of dimension line
        '<marker id="sb-dim-arrow-end" markerWidth="10" markerHeight="8" '
        'refX="9" refY="4" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L10,4 L0,8 Z" fill="{_DIM_STROKE_FULL}" />'
        "</marker>"
        # Arrow marker — start (reversed)
        '<marker id="sb-dim-arrow-start" markerWidth="10" markerHeight="8" '
        'refX="1" refY="4" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M10,0 L0,4 L10,8 Z" fill="{_DIM_STROKE_FULL}" />'
        "</marker>"
        # Compass arrow (north, pointing up)
        '<marker id="sb-compass-arrow" markerWidth="8" markerHeight="10" '
        'refX="4" refY="1" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,10 L4,0 L8,10 Z" fill="{_DIM_STROKE_FULL}" />'
        "</marker>"
        # Subtle glow for pill labels
        '<filter id="sb-dim-glow" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />'
        '<feColorMatrix in="blur" type="matrix" '
        'values="1 0 0 0 0.96  0 1 0 0 0.83  0 0 1 0 0.11  0 0 0 0.25 0" '
        'result="glow" />'
        '<feMerge><feMergeNode in="glow" />'
        '<feMergeNode in="SourceGraphic" /></feMerge>'
        "</filter>"
    )


# ---------------------------------------------------------------------------
# Overlay CSS (embedded in <style> inside <defs>)
# ---------------------------------------------------------------------------


def overlay_style_full() -> str:
    """CSS rules for overlay elements in **full** mode."""
    return f"""
  /* --- dimension lines (cotas) --- */
  .sbmap-full .sb-dim-line {{
    stroke: {_DIM_STROKE};
    stroke-width: 1.4;
    vector-effect: non-scaling-stroke;
    fill: none;
  }}
  .sbmap-full .sb-dim-tick {{
    stroke: {_DIM_STROKE};
    stroke-width: 1.2;
    vector-effect: non-scaling-stroke;
  }}
  .sbmap-full .sb-dim-label-bg {{
    fill: {_PILL_BG};
    stroke: {_PILL_BORDER};
    stroke-width: 1;
    rx: 6;
    ry: 6;
    vector-effect: non-scaling-stroke;
  }}
  .sbmap-full .sb-dim-label-text {{
    fill: {_PILL_TEXT};
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
    font-size: 16px;
    font-weight: 700;
    text-anchor: middle;
    dominant-baseline: central;
    letter-spacing: 1px;
  }}

  /* --- compass --- */
  .sbmap-full .sb-compass-line {{
    stroke: {_COMPASS_STROKE};
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
    fill: none;
  }}
  .sbmap-full .sb-compass-text {{
    fill: {_PILL_TEXT};
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    text-anchor: middle;
    dominant-baseline: central;
    letter-spacing: 2px;
  }}

  /* --- overlay layer --- */
  .sbmap-full .sb-overlay {{
    pointer-events: none;
  }}

  /* hide overlay in thumb via class */
  .sbmap-thumb .sb-overlay {{ display: none; }}
  .sbmap-thumb .sb-dim-line,
  .sbmap-thumb .sb-dim-tick,
  .sbmap-thumb .sb-dim-label-bg,
  .sbmap-thumb .sb-dim-label-text,
  .sbmap-thumb .sb-compass-line,
  .sbmap-thumb .sb-compass-text {{ display: none; }}
"""


# ---------------------------------------------------------------------------
# Layer builder
# ---------------------------------------------------------------------------


def layer_overlay(
    w: int,
    h: int,
    margin: float,
    display_units: str = "cm",
) -> str:
    """Build ``<g id="layer-overlay">`` with dimension lines + compass.

    Parameters
    ----------
    w, h:
        Map width / height in mm (user-unit coordinates).
    margin:
        The *ui_margin* value (in the same user-units) that was added
        around the map when the viewBox was expanded.
    display_units:
        ``"cm"``, ``"in"``, or ``"ft"`` — used for label formatting.

    Returns
    -------
    SVG ``<g>`` fragment.
    """
    parts: list[str] = ['<g id="layer-overlay" class="sb-overlay">']

    # Formatted dimension labels
    width_label = format_dimension(w, display_units)
    height_label = format_dimension(h, display_units)

    # ── South dimension (width) ─────────────────────────────────
    _append_south_dimension(parts, w, h, margin, width_label)

    # ── East dimension (height) ──────────────────────────────────
    _append_east_dimension(parts, w, h, margin, height_label)

    # -- Compass (N-S) -----------------------------------------------
    _append_compass(parts, w, h)

    parts.append("</g>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _append_south_dimension(
    parts: list[str],
    w: int,
    h: int,
    margin: float,
    label: str,
) -> None:
    """Horizontal dimension line below the map (south edge)."""
    y = h + margin * 0.55
    tick_len = margin * 0.12

    # Tick marks at both ends
    parts.append(
        f'<line x1="0" y1="{h}" x2="0" y2="{y + tick_len}" class="sb-dim-tick" />'
    )
    parts.append(
        f'<line x1="{w}" y1="{h}" x2="{w}" y2="{y + tick_len}" '
        f'class="sb-dim-tick" />'
    )

    # Main dimension line with arrows
    parts.append(
        f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" '
        f'class="sb-dim-line" '
        f'marker-start="url(#sb-dim-arrow-start)" '
        f'marker-end="url(#sb-dim-arrow-end)" />'
    )

    # Pill label — centred
    lx = w / 2
    ly = y + margin * 0.22
    _pill_label(parts, lx, ly, label)


def _append_east_dimension(
    parts: list[str],
    w: int,
    h: int,
    margin: float,
    label: str,
) -> None:
    """Vertical dimension line to the right of the map (east edge)."""
    x = w + margin * 0.55
    tick_len = margin * 0.12

    # Tick marks at both ends
    parts.append(
        f'<line x1="{w}" y1="0" x2="{x + tick_len}" y2="0" class="sb-dim-tick" />'
    )
    parts.append(
        f'<line x1="{w}" y1="{h}" x2="{x + tick_len}" y2="{h}" '
        f'class="sb-dim-tick" />'
    )

    # Main dimension line with arrows
    parts.append(
        f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" '
        f'class="sb-dim-line" '
        f'marker-start="url(#sb-dim-arrow-start)" '
        f'marker-end="url(#sb-dim-arrow-end)" />'
    )

    # Pill label — centred, rotated -90° so text reads bottom-to-top
    lx = x + margin * 0.22
    ly = h / 2
    _pill_label(parts, lx, ly, label, rotate=-90)


# Compass sizing constants (in mm / SVG user-units)
_COMPASS_LENGTH = 300  # 30 cm
_COMPASS_NE_OFFSET = 100  # 10 cm diagonal from NE corner


def _append_compass(
    parts: list[str],
    w: int,
    h: int,
) -> None:
    """Vertical N/S compass indicator inside the map, near the NE corner.

    Placed ~10 cm toward the south-west from the north-east corner
    ``(w, 0)`` — i.e. **inside** the map area — so it is always
    visible and never overlaps with the east dimension line.
    The arrow is at most 30 cm (300 mm) long.
    """

    diag = _COMPASS_NE_OFFSET
    dx = diag * math.cos(math.radians(45))  # ~70.7 mm left from right edge
    dy = diag * math.sin(math.radians(45))  # ~70.7 mm down from top edge

    x = w - dx  # inside the map (to the left)
    y_top = dy  # inside the map (below the top edge)
    y_bottom = y_top + _COMPASS_LENGTH

    # Safety: never extend below the map bottom
    if y_bottom > h:
        y_bottom = h

    # Compass line with arrow on top (north)
    parts.append(
        f'<line x1="{x}" y1="{y_bottom}" x2="{x}" y2="{y_top}" '
        f'class="sb-compass-line" '
        f'marker-end="url(#sb-compass-arrow)" />'
    )

    # "N" label above the line
    n_y = y_top - 18
    parts.append(f'<text x="{x}" y="{n_y}" class="sb-compass-text">N</text>')

    # "S" label below the line
    s_y = y_bottom + 22
    parts.append(f'<text x="{x}" y="{s_y}" class="sb-compass-text">S</text>')


def _pill_label(
    parts: list[str],
    cx: float,
    cy: float,
    text: str,
    rotate: int = 0,
) -> None:
    """Render a "pill" shaped label (rounded rect + text).

    Parameters
    ----------
    cx, cy:
        Centre position of the pill.
    text:
        Dimension text to show.
    rotate:
        Rotation angle (degrees) around ``(cx, cy)``.
    """
    # Estimate pill size from text length  (monospace ≈ 10px per char at 16px)
    char_w = 10
    pad_x = 14
    pad_y = 8
    text_w = len(text) * char_w
    pill_w = text_w + pad_x * 2
    pill_h = 24 + pad_y

    rx = cx - pill_w / 2
    ry_rect = cy - pill_h / 2

    group_open = ""
    group_close = ""
    if rotate:
        group_open = f'<g transform="rotate({rotate},{cx},{cy})">'
        group_close = "</g>"

    parts.append(group_open)
    # Background pill
    parts.append(
        f'<rect x="{rx}" y="{ry_rect}" '
        f'width="{pill_w}" height="{pill_h}" '
        f'class="sb-dim-label-bg" '
        f'filter="url(#sb-dim-glow)" />'
    )
    # Text
    parts.append(f'<text x="{cx}" y="{cy}" class="sb-dim-label-text">{text}</text>')
    parts.append(group_close)
