"""Tactical-dark SVG ``<defs>`` block: patterns, filters, embedded styles.

All visual theming lives here so the rest of the renderer stays
geometry-only.  Nothing in this module touches coordinates or shapes.
"""

from __future__ import annotations

from infrastructure.maps._renderer._overlay import overlay_defs, overlay_style_full

# ---------------------------------------------------------------------------
# Palette tokens (keep in sync with tactical.css / tactical_gradio.css)
# ---------------------------------------------------------------------------
BG_MAP = "#0b0f14"
BG_TABLE = "#101820"
GRID_MINOR = "rgba(255,255,255,0.04)"
GRID_MAJOR = "rgba(246,212,28,0.08)"
BORDER_FRAME = "rgba(246,212,28,0.35)"
ACCENT = "#f6d41c"
TEXT_PRIMARY = "#e9eef6"
TEXT_MUTED = "#92a9c1"
ZONE_DEFENDER_TINT = "rgba(46,129,255,0.12)"
ZONE_DEFENDER_STROKE = "rgba(46,129,255,0.45)"
ZONE_ATTACKER_TINT = "rgba(255,76,76,0.12)"
ZONE_ATTACKER_STROKE = "rgba(255,76,76,0.45)"
TERRAIN_FILL = "rgba(200,220,255,0.08)"
TERRAIN_STROKE = "rgba(146,169,193,0.45)"
TERRAIN_PASSABLE_FILL = "rgba(200,220,255,0.03)"
TERRAIN_PASSABLE_STROKE = "rgba(146,169,193,0.30)"
OBJ_FILL = "#101820"
OBJ_STROKE = ACCENT
HATCH_DEFENDER = "rgba(46,129,255,0.18)"
HATCH_ATTACKER = "rgba(255,76,76,0.18)"

# ---------------------------------------------------------------------------
# Embedded <style> (for standalone SVG portability)
# ---------------------------------------------------------------------------
_STYLE_FULL = """\
<style type="text/css">
  /* === base resets === */
  .sbmap-full text {
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  }

  /* --- zones (deployment) --- */
  .sbmap-full .sb-zone-defender {
    fill: %(zone_def_tint)s;
    stroke: %(zone_def_stroke)s;
    stroke-width: 1.4;
    stroke-dasharray: 8 4;
    vector-effect: non-scaling-stroke;
    stroke-linejoin: round;
  }
  .sbmap-full .sb-zone-attacker {
    fill: %(zone_atk_tint)s;
    stroke: %(zone_atk_stroke)s;
    stroke-width: 1.4;
    stroke-dasharray: 8 4;
    vector-effect: non-scaling-stroke;
    stroke-linejoin: round;
  }

  /* --- terrain (scenography) --- */
  .sbmap-full .sb-terrain {
    fill: %(terrain_fill)s;
    stroke: %(terrain_stroke)s;
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
    stroke-linejoin: round;
  }
  .sbmap-full .sb-terrain-passable {
    fill: %(terrain_pass_fill)s;
    stroke: %(terrain_pass_stroke)s;
    stroke-width: 0.8;
    stroke-dasharray: 6 3 2 3;
    opacity: 0.75;
    vector-effect: non-scaling-stroke;
    stroke-linejoin: round;
  }

  /* --- objectives --- */
  .sbmap-full .sb-objective-ring {
    fill: %(obj_fill)s;
    stroke: %(accent)s;
    stroke-width: 2.4;
    vector-effect: non-scaling-stroke;
  }
  .sbmap-full .sb-objective-num {
    fill: %(accent)s;
    font-size: 22px;
    font-weight: 700;
    text-anchor: middle;
    dominant-baseline: central;
  }

  /* --- labels --- */
  .sbmap-full .sb-label {
    fill: %(text_muted)s;
    font-size: 13px;
    font-weight: 600;
    text-anchor: middle;
    dominant-baseline: middle;
    paint-order: stroke fill;
    stroke: %(bg_table)s;
    stroke-width: 3px;
    stroke-linejoin: round;
    vector-effect: non-scaling-stroke;
  }
  .sbmap-full .sb-label-strong {
    fill: %(text_primary)s;
    font-size: 14px;
    font-weight: 700;
  }
  .sbmap-full .sb-label-zone {
    fill: %(text_muted)s;
    font-size: 11px;
    font-weight: 600;
    text-anchor: middle;
    dominant-baseline: middle;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    paint-order: stroke fill;
    stroke: %(bg_table)s;
    stroke-width: 3px;
    stroke-linejoin: round;
    vector-effect: non-scaling-stroke;
  }
  .sbmap-full .sb-label-obj {
    fill: %(text_primary)s;
    font-size: 13px;
    font-weight: 600;
    paint-order: stroke fill;
    stroke: %(bg_table)s;
    stroke-width: 3px;
    stroke-linejoin: round;
  }

  /* --- frame --- */
  .sbmap-full .sb-frame {
    fill: none;
    stroke: %(border_frame)s;
    stroke-width: 1.5;
    vector-effect: non-scaling-stroke;
  }
  .sbmap-full .sb-corner-bracket {
    fill: none;
    stroke: %(accent)s;
    stroke-width: 2;
    stroke-linecap: square;
    vector-effect: non-scaling-stroke;
  }

  /* --- grid --- */
  .sbmap-full .sb-grid-overlay {
    pointer-events: none;
  }
</style>
""" % {
    "zone_def_tint": ZONE_DEFENDER_TINT,
    "zone_def_stroke": ZONE_DEFENDER_STROKE,
    "zone_atk_tint": ZONE_ATTACKER_TINT,
    "zone_atk_stroke": ZONE_ATTACKER_STROKE,
    "terrain_fill": TERRAIN_FILL,
    "terrain_stroke": TERRAIN_STROKE,
    "terrain_pass_fill": TERRAIN_PASSABLE_FILL,
    "terrain_pass_stroke": TERRAIN_PASSABLE_STROKE,
    "obj_fill": OBJ_FILL,
    "accent": ACCENT,
    "text_primary": TEXT_PRIMARY,
    "text_muted": TEXT_MUTED,
    "bg_table": BG_TABLE,
    "border_frame": BORDER_FRAME,
}

# Thumb mode: minimal style, no labels, no grid
_STYLE_THUMB = """\
<style type="text/css">
  .sbmap-thumb text { font-family: 'JetBrains Mono', monospace; }
  .sbmap-thumb .sb-zone-defender {
    fill: %(zone_def_tint)s; stroke: %(zone_def_stroke)s;
    stroke-width: 1; vector-effect: non-scaling-stroke;
  }
  .sbmap-thumb .sb-zone-attacker {
    fill: %(zone_atk_tint)s; stroke: %(zone_atk_stroke)s;
    stroke-width: 1; vector-effect: non-scaling-stroke;
  }
  .sbmap-thumb .sb-terrain {
    fill: %(terrain_fill)s; stroke: %(terrain_stroke)s;
    stroke-width: 0.8; vector-effect: non-scaling-stroke;
  }
  .sbmap-thumb .sb-terrain-passable {
    fill: %(terrain_pass_fill)s; stroke: %(terrain_pass_stroke)s;
    stroke-width: 0.6; stroke-dasharray: 6 3 2 3; opacity: 0.75;
    vector-effect: non-scaling-stroke;
  }
  .sbmap-thumb .sb-objective-ring {
    fill: %(obj_fill)s; stroke: %(accent)s;
    stroke-width: 2; vector-effect: non-scaling-stroke;
  }
  .sbmap-thumb .sb-objective-num {
    fill: %(accent)s; font-size: 20px; font-weight: 700;
    text-anchor: middle; dominant-baseline: central;
  }
  .sbmap-thumb .sb-frame { fill: none; stroke: %(border_frame)s; stroke-width: 1; }
  .sbmap-thumb .sb-label, .sbmap-thumb .sb-label-strong,
  .sbmap-thumb .sb-label-zone, .sbmap-thumb .sb-label-obj { display: none; }
</style>
""" % {
    "zone_def_tint": ZONE_DEFENDER_TINT,
    "zone_def_stroke": ZONE_DEFENDER_STROKE,
    "zone_atk_tint": ZONE_ATTACKER_TINT,
    "zone_atk_stroke": ZONE_ATTACKER_STROKE,
    "terrain_fill": TERRAIN_FILL,
    "terrain_stroke": TERRAIN_STROKE,
    "terrain_pass_fill": TERRAIN_PASSABLE_FILL,
    "terrain_pass_stroke": TERRAIN_PASSABLE_STROKE,
    "obj_fill": OBJ_FILL,
    "accent": ACCENT,
    "border_frame": BORDER_FRAME,
}


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------


def _grid_patterns(cell: int = 50) -> str:
    """Minor/major grid ``<pattern>`` definitions.

    *cell* is the minor grid spacing in user units (mm).
    Major grid lines appear every 5 cells.
    """
    major = cell * 5
    return (
        # minor grid
        f'<pattern id="sb-grid-minor" width="{cell}" height="{cell}" '
        f'patternUnits="userSpaceOnUse">'
        f'<line x1="0" y1="0" x2="{cell}" y2="0" '
        f'stroke="{GRID_MINOR}" stroke-width="0.5" />'
        f'<line x1="0" y1="0" x2="0" y2="{cell}" '
        f'stroke="{GRID_MINOR}" stroke-width="0.5" />'
        f"</pattern>"
        # major grid
        f'<pattern id="sb-grid-major" width="{major}" height="{major}" '
        f'patternUnits="userSpaceOnUse">'
        f'<line x1="0" y1="0" x2="{major}" y2="0" '
        f'stroke="{GRID_MAJOR}" stroke-width="0.8" />'
        f'<line x1="0" y1="0" x2="0" y2="{major}" '
        f'stroke="{GRID_MAJOR}" stroke-width="0.8" />'
        f"</pattern>"
    )


def _hatch_patterns() -> str:
    """Diagonal hatch patterns for attacker / defender overlays."""
    return (
        # defender hatch (blue, 45°)
        '<pattern id="sb-hatch-defender" width="8" height="8" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="8" '
        f'stroke="{HATCH_DEFENDER}" stroke-width="1.5" />'
        "</pattern>"
        # attacker hatch (red, -45°)
        '<pattern id="sb-hatch-attacker" width="8" height="8" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
        f'<line x1="0" y1="0" x2="0" y2="8" '
        f'stroke="{HATCH_ATTACKER}" stroke-width="1.5" />'
        "</pattern>"
    )


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


def _glow_filter() -> str:
    """Subtle amber glow ``<filter>`` for objectives and accent elements."""
    return (
        '<filter id="sb-glow-accent" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />'
        '<feColorMatrix in="blur" type="matrix" '
        'values="1 0 0 0 0.96  0 1 0 0 0.83  0 0 1 0 0.11  0 0 0 0.55 0" '
        'result="glow" />'
        "<feMerge>"
        '<feMergeNode in="glow" />'
        '<feMergeNode in="SourceGraphic" />'
        "</feMerge>"
        "</filter>"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def tactical_defs(render_mode: str = "full") -> str:
    """Return the complete ``<defs>…</defs>`` block for tactical-dark SVG.

    Parameters
    ----------
    render_mode:
        ``"full"``  — all patterns, filters, full stylesheet.
        ``"thumb"`` — minimal stylesheet (labels hidden), no grid
                      patterns, no glow filter.
    """
    parts: list[str] = ["<defs>"]

    # style block
    if render_mode == "thumb":
        parts.append(_STYLE_THUMB)
    else:
        parts.append(_STYLE_FULL)
        # Overlay styles (dimension cotas + compass) — full mode only
        parts.append(f'<style type="text/css">{overlay_style_full()}</style>')
        parts.append(_grid_patterns())
        parts.append(_glow_filter())

    # hatch patterns always present (zones still need them in thumb)
    parts.append(_hatch_patterns())

    # Overlay markers (arrows) — always present so thumb doesn't break
    # if an SVG is accidentally rendered with overlay elements
    parts.append(overlay_defs())

    parts.append("</defs>")
    return "".join(parts)
