"""SvgMapRenderer - SVG rendering for scenario maps.

A simple implementation that converts table dimensions and shapes
into SVG markup for visualization.
"""

from __future__ import annotations


class SvgMapRenderer:
    """SVG map renderer for the modern API.

    Renders table dimensions and shapes to SVG format.
    """

    def _svg_header(self, width: int, height: int) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        )

    def _rect_svg(self, shape: dict) -> str:
        x = int(shape["x"])
        y = int(shape["y"])
        w = int(shape["width"])
        h = int(shape["height"])
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" />'

    def _circle_svg(self, shape: dict) -> str:
        cx = int(shape["cx"])
        cy = int(shape["cy"])
        r = int(shape["r"])
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" />'

    def _polygon_svg(self, shape: dict) -> str:
        points = shape["points"]
        points_str = " ".join(f'{int(p["x"])},{int(p["y"])}' for p in points)
        return f'<polygon points="{points_str}" />'

    def _objective_point_svg(self, shape: dict) -> str:
        """Render an objective_point as a black filled circle with radius 25mm.

        Args:
            shape: Dictionary with cx and cy coordinates.

        Returns:
            SVG string for a black filled circle.
        """
        cx = int(shape["cx"])
        cy = int(shape["cy"])
        r = 25  # Fixed radius of 25mm
        # Black fill with black stroke
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="black" stroke="black" />'

    def _shape_svg(self, shape: dict) -> str | None:
        shape_type = shape.get("type")
        if shape_type == "rect":
            return self._rect_svg(shape)
        if shape_type == "circle":
            return self._circle_svg(shape)
        if shape_type == "polygon":
            return self._polygon_svg(shape)
        if shape_type == "objective_point":
            return self._objective_point_svg(shape)
        return None

    def render(self, table_mm: dict, shapes: list[dict]) -> str:
        """Render table and shapes to SVG.

        Args:
            table_mm: Dictionary with width_mm and height_mm keys.
            shapes: List of shape dictionaries (rect, circle, polygon).

        Returns:
            SVG string with rendered shapes.
        """
        width = int(table_mm["width_mm"])
        height = int(table_mm["height_mm"])

        parts: list[str] = []

        # SVG header
        parts.append(self._svg_header(width, height))

        # Render shapes
        for shape in shapes:
            svg = self._shape_svg(shape)
            if svg:
                parts.append(svg)

        # SVG footer
        parts.append("</svg>")

        return "".join(parts)

    def render_svg(self, map_spec: dict) -> str:
        """Legacy API wrapper for backward compatibility.

        Args:
            map_spec: Dictionary with width/width_mm, height/height_mm, and shapes.

        Returns:
            SVG string with rendered map.
        """
        # Support both width_mm and width keys
        width_mm = int(map_spec.get("width_mm") or map_spec.get("width", 1100))
        height_mm = int(map_spec.get("height_mm") or map_spec.get("height", 700))
        shapes = map_spec.get("shapes", [])

        table_mm = {"width_mm": width_mm, "height_mm": height_mm}
        return self.render(table_mm=table_mm, shapes=shapes)
