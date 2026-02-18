"""SvgMapRenderer — SVG rendering for scenario maps (FACADE).

Delegates sanitisation, geometry and primitive rendering to
``_renderer._sanitize``, ``_renderer._geometry`` and
``_renderer._primitives`` respectively.
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
    escape_attr,
    escape_text,
    safe_numeric,
    safe_paint,
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
    def _escape_attr(value: str) -> str:  # pragma: no cover - delegate
        return escape_attr(value)

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
        return objective_point_svg(shape)

    def _shape_svg(self, shape: dict) -> str | None:
        return shape_svg(shape)

    def _text_label_svg(
        self,
        x: int,
        y: int,
        text: str,
        font_size: int = 16,
        fill: str = "#000",
        direction: str = "up",
    ) -> str:
        return text_label_svg(x, y, text, font_size, fill, direction)

    # -- public API ------------------------------------------------------------

    def render(self, table_mm: dict, shapes: list[dict]) -> str:
        """Render table and shapes to SVG.

        Args:
            table_mm: Dictionary with width_mm and height_mm keys.
            shapes: List of shape dictionaries (rect, circle, polygon).

        Returns:
            SVG string with rendered shapes.
        """
        self.table_width_mm = int(table_mm["width_mm"])
        self.table_height_mm = int(table_mm["height_mm"])

        width = self.table_width_mm
        height = self.table_height_mm

        parts: list[str] = []

        # SVG header
        parts.append(svg_header(width, height))

        # Canvas background (replaces CSS style="background" for security)
        parts.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" ' 'fill="#f5f5f5" />'
        )

        # Table background (white playing area with border)
        parts.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" '
            'fill="white" stroke="#333" stroke-width="3" />'
        )

        # Render shapes
        for shape in shapes:
            svg = shape_svg(shape)
            if svg:
                parts.append(svg)

            # Render label if description exists
            description = shape.get("description", "").strip()
            if description:
                label_svg = self._render_shape_label(shape)
                if label_svg:
                    parts.append(label_svg)

        # SVG footer
        parts.append("</svg>")

        return "".join(parts)

    def _render_shape_label(self, shape: dict) -> str | None:
        """Render label for a shape based on its type and description."""
        description = shape.get("description", "").strip()
        if not description:
            return None

        shape_type = shape.get("type")

        if shape_type == "rect":
            cx, cy = calculate_rect_center(shape)
            return text_label_svg(cx, cy, description, font_size=14, fill="#003")

        elif shape_type == "circle":
            cx, cy = calculate_circle_center(shape)
            return text_label_svg(cx, cy, description, font_size=14, fill="#333")

        elif shape_type == "polygon":
            cx, cy = calculate_polygon_center(shape)
            return text_label_svg(cx, cy, description, font_size=14, fill="#300")

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
                font_size=14,
                fill="#000",
                direction=direction,
            )

        return None

    def render_svg(self, map_spec: dict) -> str:
        """Legacy API wrapper for backward compatibility."""
        width_mm = int(map_spec.get("width_mm") or map_spec.get("width", 1100))
        height_mm = int(map_spec.get("height_mm") or map_spec.get("height", 700))
        shapes = map_spec.get("shapes", [])

        table_mm = {"width_mm": width_mm, "height_mm": height_mm}
        return self.render(table_mm=table_mm, shapes=shapes)
