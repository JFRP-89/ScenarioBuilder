"""SvgMapRenderer - SVG rendering for scenario maps.

A simple implementation that converts table dimensions and shapes
into SVG markup for visualization.
"""

from __future__ import annotations


class SvgMapRenderer:
    """SVG map renderer for the modern API.

    Renders table dimensions and shapes to SVG format.
    """

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
        parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        )

        # Render shapes
        for shape in shapes:
            shape_type = shape.get("type")

            if shape_type == "rect":
                x = int(shape["x"])
                y = int(shape["y"])
                w = int(shape["width"])
                h = int(shape["height"])
                parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" />')

            elif shape_type == "circle":
                cx = int(shape["cx"])
                cy = int(shape["cy"])
                r = int(shape["r"])
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" />')

            elif shape_type == "polygon":
                points = shape["points"]
                points_str = " ".join(f'{int(p["x"])},{int(p["y"])}' for p in points)
                parts.append(f'<polygon points="{points_str}" />')

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
