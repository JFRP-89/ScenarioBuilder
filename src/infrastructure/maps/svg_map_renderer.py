"""SvgMapRenderer — SVG rendering for scenario maps (FACADE).

Tactical-dark theme with layered structure:

1. ``layer-bg``      — dark background + vignette
2. ``layer-grid``    — minor / major grid overlay (full mode only)
3. ``layer-zones``   — deployment zone overlays + hatch
4. ``layer-terrain`` — scenography / terrain shapes
5. ``layer-markers`` — objective points (numbered)
6. ``layer-labels``  — text labels (full mode only)
7. ``layer-frame``   — outer frame, corner brackets

Delegates sanitisation, geometry and primitive rendering to
``_renderer._sanitize``, ``_renderer._geometry``,
``_renderer._primitives`` and ``_renderer._tactical_defs``.
"""

from __future__ import annotations

from infrastructure.maps._renderer._geometry import (
    calculate_circle_center,
    calculate_polygon_center,
    calculate_rect_center,
    estimate_text_width,
    find_best_objective_position,
    get_position_preference_order,
    text_fits_in_bounds,
)
from infrastructure.maps._renderer._overlay import layer_overlay
from infrastructure.maps._renderer._primitives import (
    circle_svg,
    objective_point_svg,
    polygon_svg,
    rect_svg,
    shape_svg,
    svg_header,
    text_label_svg,
)
from infrastructure.maps._renderer._sanitize import (  # - keep importable
    escape_text,
    safe_numeric,
    safe_paint,
)
from infrastructure.maps._renderer._tactical_defs import (
    ACCENT,
    BG_MAP,
    BG_TABLE,
    BORDER_FRAME,
    TEXT_MUTED,
    TEXT_PRIMARY,
    tactical_defs,
)


class SvgMapRenderer:
    """SVG map renderer for the modern API.

    Renders table dimensions and shapes to SVG format.
    """

    def __init__(self) -> None:
        """Initialize renderer with table dimensions."""
        self.table_width_mm = 0
        self.table_height_mm = 0

    # -- kept for backward compat (tests reference via instance) ---------------
    def _escape_text(self, text: str) -> str:  # pragma: no cover - delegate
        return escape_text(text)

    @staticmethod
    def _safe_paint(value: str, default: str) -> str:  # pragma: no cover - delegate
        return safe_paint(value, default)

    @staticmethod
    def _safe_numeric(value: str, default: str) -> str:  # pragma: no cover - delegate
        return safe_numeric(value, default)

    # -- geometry delegates (tests call these via instance) --------------------
    def _calculate_rect_center(self, shape: dict) -> tuple[int, int]:
        return calculate_rect_center(shape)

    def _calculate_circle_center(self, shape: dict) -> tuple[int, int]:
        return calculate_circle_center(shape)

    def _calculate_polygon_center(self, shape: dict) -> tuple[int, int]:
        return calculate_polygon_center(shape)

    def _estimate_text_width(self, text: str, font_size_px: int = 14) -> int:
        return estimate_text_width(text, font_size_px)

    def _text_fits_in_bounds(
        self,
        text: str,
        center_x: int,
        center_y: int,
        offset: int = 0,
        direction: str = "up",
    ) -> bool:
        return text_fits_in_bounds(
            text,
            center_x,
            center_y,
            self.table_width_mm,
            self.table_height_mm,
            offset,
            direction,
        )

    def _get_position_preference_order(
        self,
        cx: int,
        cy: int,
    ) -> list[tuple[int, int, str]]:
        return get_position_preference_order(
            cx,
            cy,
            self.table_width_mm,
            self.table_height_mm,
        )

    def _find_best_objective_position(
        self,
        cx: int,
        cy: int,
        text: str,
    ) -> tuple[int, int, str]:
        return find_best_objective_position(
            cx,
            cy,
            text,
            self.table_width_mm,
            self.table_height_mm,
        )

    # -- primitive delegates (tests call these via instance) -------------------
    def _svg_header(self, width: int, height: int) -> str:
        return svg_header(width, height)

    def _rect_svg(self, shape: dict) -> str:
        return rect_svg(shape)

    def _circle_svg(self, shape: dict) -> str:
        return circle_svg(shape)

    def _polygon_svg(self, shape: dict) -> str:
        return polygon_svg(shape)

    def _objective_point_svg(self, shape: dict) -> str:
        return objective_point_svg(shape, index=0)

    def _shape_svg(self, shape: dict) -> str | None:
        return shape_svg(shape)

    def _text_label_svg(
        self,
        x: int,
        y: int,
        text: str,
        font_size: int = 13,
        fill: str = "",
        direction: str = "up",
    ) -> str:
        return text_label_svg(x, y, text, font_size, fill, direction)

    # -- public API ------------------------------------------------------------

    def render(
        self,
        table_mm: dict,
        shapes: list[dict],
        render_mode: str = "full",
        display_units: str = "cm",
    ) -> str:
        """Render table and shapes to tactical-dark SVG.

        Args:
            table_mm: Dictionary with width_mm and height_mm keys.
            shapes: List of shape dictionaries (rect, circle, polygon).
            render_mode: ``"full"`` for detail view, ``"thumb"`` for cards.
            display_units: Unit system for dimension labels
                (``"cm"``, ``"in"``, or ``"ft"``).

        Returns:
            SVG string with layered tactical-dark rendering.
        """
        self.table_width_mm = int(table_mm["width_mm"])
        self.table_height_mm = int(table_mm["height_mm"])

        w = self.table_width_mm
        h = self.table_height_mm
        is_full = render_mode != "thumb"

        zones, terrain, markers = self._classify_shapes(shapes)

        # Compute UI margin for overlay (full mode only)
        ui_margin = max(w, h) * 0.08 if is_full else 0.0

        svg_class = f"sbmap-{render_mode}"
        parts: list[str] = [
            svg_header(w, h, css_class=svg_class, margin=ui_margin),
            tactical_defs(render_mode),
            self._layer_bg(w, h),
        ]
        if is_full:
            parts.append(self._layer_grid(w, h))
        parts.append(self._layer_zones(zones))
        parts.append(self._layer_terrain(terrain))
        parts.append(self._layer_markers(markers))
        if is_full:
            parts.append(self._layer_labels(zones, terrain, markers))
        parts.append(self._layer_frame(w, h, is_full))
        if is_full:
            parts.append(layer_overlay(w, h, ui_margin, display_units))
        parts.append("</svg>")

        return "".join(parts)

    # -- layer builders --------------------------------------------------------

    @staticmethod
    def _classify_shapes(
        shapes: list[dict],
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Classify shapes into zones / terrain / markers.

        Classification is by **logical role**, not geometric type:
        - Deployment zones have ``"border"`` or ``"corner"`` keys.
        - Objective markers have ``type == "objective_point"``.
        - Everything else is terrain / scenography.
        """
        zones: list[dict] = []
        terrain: list[dict] = []
        markers: list[dict] = []
        for shape in shapes:
            stype = shape.get("type")
            if stype == "objective_point":
                markers.append(shape)
            elif "border" in shape or "corner" in shape:
                zones.append(shape)
            else:
                terrain.append(shape)
        return zones, terrain, markers

    @staticmethod
    def _layer_bg(w: int, h: int) -> str:
        return (
            '<g id="layer-bg">'
            f'<rect class="sb-map-bg" x="0" y="0" width="{w}" height="{h}" '
            f'fill="{BG_MAP}" />'
            f'<rect class="sb-table" x="0" y="0" width="{w}" height="{h}" '
            f'fill="{BG_TABLE}" />'
            "</g>"
        )

    @staticmethod
    def _layer_grid(w: int, h: int) -> str:
        return (
            '<g id="layer-grid" class="sb-grid-overlay">'
            f'<rect class="sb-grid-minor" x="0" y="0" width="{w}" '
            f'height="{h}" fill="url(#sb-grid-minor)" />'
            f'<rect class="sb-grid-major" x="0" y="0" width="{w}" '
            f'height="{h}" fill="url(#sb-grid-major)" />'
            "</g>"
        )

    @staticmethod
    def _layer_zones(zones: list[dict]) -> str:
        parts = ['<g id="layer-zones">']
        for shape in zones:
            svg = shape_svg(shape, css_class="sb-zone-defender")
            if svg:
                parts.append(svg)
        # hatch overlays
        for shape in zones:
            parts.append(SvgMapRenderer._hatch_overlay(shape, "sb-hatch-defender"))
        parts.append("</g>")
        return "".join(parts)

    @staticmethod
    def _layer_terrain(terrain: list[dict]) -> str:
        parts = ['<g id="layer-terrain">']
        for shape in terrain:
            cls = (
                "sb-terrain-passable"
                if shape.get("allow_overlap", False)
                else "sb-terrain"
            )
            svg = shape_svg(shape, css_class=cls)
            if svg:
                parts.append(svg)
        parts.append("</g>")
        return "".join(parts)

    @staticmethod
    def _layer_markers(markers: list[dict]) -> str:
        parts = ['<g id="layer-markers">']
        for idx, shape in enumerate(markers, start=1):
            svg = shape_svg(shape, obj_index=idx)
            if svg:
                parts.append(svg)
        parts.append("</g>")
        return "".join(parts)

    def _layer_labels(
        self,
        zones: list[dict],
        terrain: list[dict],
        markers: list[dict],
    ) -> str:
        parts = ['<g id="layer-labels">']
        for shape in zones:
            label = self._render_shape_label(shape, css_class="sb-label-zone")
            if label:
                parts.append(label)
        for shape in terrain:
            label = self._render_shape_label(shape, css_class="sb-label")
            if label:
                parts.append(label)
        for shape in markers:
            label = self._render_shape_label(shape, css_class="sb-label-obj")
            if label:
                parts.append(label)
        parts.append("</g>")
        return "".join(parts)

    @staticmethod
    def _layer_frame(w: int, h: int, is_full: bool) -> str:
        parts = [
            '<g id="layer-frame">',
            f'<rect class="sb-frame" x="0" y="0" width="{w}" height="{h}" '
            f'fill="none" stroke="{BORDER_FRAME}" stroke-width="1.5" '
            f'vector-effect="non-scaling-stroke" />',
        ]
        if is_full:
            parts.append(SvgMapRenderer._corner_brackets(w, h))
        parts.append("</g>")
        return "".join(parts)

    # -- shape helpers ---------------------------------------------------------
    @staticmethod
    def _hatch_overlay(shape: dict, pattern_id: str) -> str:
        """Render a hatch-pattern overlay matching the shape geometry."""
        stype = shape.get("type")
        if stype == "rect":
            x = int(shape["x"])
            y = int(shape["y"])
            w = int(shape["width"])
            h = int(shape["height"])
            return (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="url(#{pattern_id})" stroke="none" />'
            )
        if stype == "polygon":
            points = shape["points"]
            pts = " ".join(f'{int(p["x"])},{int(p["y"])}' for p in points)
            return (
                f'<polygon points="{pts}" '
                f'fill="url(#{pattern_id})" stroke="none" />'
            )
        return ""

    @staticmethod
    def _corner_brackets(w: int, h: int, size: int = 30) -> str:
        """HUD-style corner brackets (amber accent)."""
        s = min(size, w // 6, h // 6)
        parts: list[str] = []
        # Each corner: two perpendicular lines
        corners = [
            # top-left
            (
                f'<line x1="0" y1="{s}" x2="0" y2="0" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
                f'<line x1="0" y1="0" x2="{s}" y2="0" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
            ),
            # top-right
            (
                f'<line x1="{w - s}" y1="0" x2="{w}" y2="0" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
                f'<line x1="{w}" y1="0" x2="{w}" y2="{s}" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
            ),
            # bottom-right
            (
                f'<line x1="{w}" y1="{h - s}" x2="{w}" y2="{h}" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
                f'<line x1="{w}" y1="{h}" x2="{w - s}" y2="{h}" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
            ),
            # bottom-left
            (
                f'<line x1="{s}" y1="{h}" x2="0" y2="{h}" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
                f'<line x1="0" y1="{h}" x2="0" y2="{h - s}" class="sb-corner-bracket" '
                f'stroke="{ACCENT}" stroke-width="2" />'
            ),
        ]
        for block in corners:
            parts.append(block)
        return "".join(parts)

    def _render_shape_label(
        self,
        shape: dict,
        css_class: str = "sb-label",
    ) -> str | None:
        """Render label for a shape based on its type and description."""
        description = shape.get("description", "").strip()
        if not description:
            return None

        shape_type = shape.get("type")

        if shape_type == "rect":
            cx, cy = calculate_rect_center(shape)
            return text_label_svg(
                cx,
                cy,
                description,
                font_size=13,
                fill=TEXT_MUTED,
                css_class=css_class,
            )

        elif shape_type == "circle":
            cx, cy = calculate_circle_center(shape)
            return text_label_svg(
                cx,
                cy,
                description,
                font_size=13,
                fill=TEXT_MUTED,
                css_class=css_class,
            )

        elif shape_type == "polygon":
            cx, cy = calculate_polygon_center(shape)
            return text_label_svg(
                cx,
                cy,
                description,
                font_size=13,
                fill=TEXT_MUTED,
                css_class=css_class,
            )

        elif shape_type == "objective_point":
            cx = int(shape.get("cx", 0))
            cy = int(shape.get("cy", 0))
            text_x, text_y, direction = find_best_objective_position(
                cx,
                cy,
                description,
                self.table_width_mm,
                self.table_height_mm,
            )
            return text_label_svg(
                text_x,
                text_y,
                description,
                font_size=13,
                fill=TEXT_PRIMARY,
                direction=direction,
                css_class=css_class,
            )

        return None

    def render_svg(self, map_spec: dict) -> str:
        """Legacy API wrapper for backward compatibility."""
        width_mm = int(map_spec.get("width_mm") or map_spec.get("width", 1100))
        height_mm = int(map_spec.get("height_mm") or map_spec.get("height", 700))
        shapes = map_spec.get("shapes", [])

        table_mm = {"width_mm": width_mm, "height_mm": height_mm}
        return self.render(table_mm=table_mm, shapes=shapes)
