"""SvgMapRenderer - SVG rendering for scenario maps.

A simple implementation that converts table dimensions and shapes
into SVG markup for visualization.
"""

from __future__ import annotations

import html


class SvgMapRenderer:
    """SVG map renderer for the modern API.

    Renders table dimensions and shapes to SVG format.
    """

    def __init__(self) -> None:
        """Initialize renderer with table dimensions."""
        self.table_width_mm = 0
        self.table_height_mm = 0

    def _escape_text(self, text: str) -> str:
        """Escape text for safe inclusion in SVG."""
        return html.escape(text)

    def _calculate_rect_center(self, shape: dict) -> tuple[int, int]:
        """Calculate center coordinates of a rectangle."""
        x = int(shape["x"])
        y = int(shape["y"])
        w = int(shape["width"])
        h = int(shape["height"])
        return x + w // 2, y + h // 2

    def _calculate_circle_center(self, shape: dict) -> tuple[int, int]:
        """Calculate center coordinates of a circle."""
        cx = int(shape["cx"])
        cy = int(shape["cy"])
        return cx, cy

    def _calculate_polygon_center(self, shape: dict) -> tuple[int, int]:
        """Calculate approximate center of a polygon (centroid).

        For quarter-circles (identified by 'corner' field), calculates the true
        centroid using the formula: distance from corner = 4R/(3π).
        For other polygons, uses the average of all vertices.
        """
        points = shape.get("points", [])
        if not points:
            return 0, 0

        # Check if this is a quarter-circle (has corner attribute)
        corner = shape.get("corner")
        if corner and len(points) > 3:  # Quarter-circles have many points
            # Calculate radius from corner to furthest point
            x_coords = [int(p.get("x", 0)) for p in points]
            y_coords = [int(p.get("y", 0)) for p in points]

            # Identify corner position (first point is always the corner)
            corner_x = x_coords[0]
            corner_y = y_coords[0]

            # Estimate radius from corner to average of arc points
            # (exclude corner point itself)
            arc_points_x = x_coords[1:]
            arc_points_y = y_coords[1:]

            # Calculate approximate radius
            max_dist_x = max(abs(x - corner_x) for x in arc_points_x)
            max_dist_y = max(abs(y - corner_y) for y in arc_points_y)
            radius = max(max_dist_x, max_dist_y)

            # Centroid of quarter-circle: distance from corner = 4R/(3π) ≈ 0.4244*R
            import math

            centroid_distance = (4 * radius) / (3 * math.pi)

            # Calculate centroid position based on corner
            if corner == "north-west":
                # Corner at (0, 0), centroid towards (R, R)
                cx = int(corner_x + centroid_distance)
                cy = int(corner_y + centroid_distance)
            elif corner == "north-east":
                # Corner at (W, 0), centroid towards (W-R, R)
                cx = int(corner_x - centroid_distance)
                cy = int(corner_y + centroid_distance)
            elif corner == "south-west":
                # Corner at (0, H), centroid towards (R, H-R)
                cx = int(corner_x + centroid_distance)
                cy = int(corner_y - centroid_distance)
            elif corner == "south-east":
                # Corner at (W, H), centroid towards (W-R, H-R)
                cx = int(corner_x - centroid_distance)
                cy = int(corner_y - centroid_distance)
            else:
                # Fallback to average
                cx = sum(x_coords) // len(x_coords)
                cy = sum(y_coords) // len(y_coords)

            return cx, cy

        # For regular polygons (triangles, etc.), use average of vertices
        x_coords = [int(p.get("x", 0)) for p in points]
        y_coords = [int(p.get("y", 0)) for p in points]

        cx = sum(x_coords) // len(x_coords)
        cy = sum(y_coords) // len(y_coords)
        return cx, cy

    def _estimate_text_width(self, text: str, font_size_px: int = 14) -> int:
        """Estimate text width in mm for a given font size.

        Args:
            text: Text content
            font_size_px: Font size in SVG units (= mm in viewBox)

        Returns:
            Estimated width in mm
        """
        # For Arial Bold (used in SVG), each character is ~0.7 * font_size wide
        # font_size in SVG with viewBox = units in mm, not pixels
        char_width_mm = font_size_px * 0.7
        total_width_mm = int(len(text) * char_width_mm)
        return max(total_width_mm, 10)  # Minimum 10mm

    def _text_fits_in_bounds(
        self,
        text: str,
        center_x: int,
        center_y: int,
        offset: int = 0,
        direction: str = "up",
    ) -> bool:
        """Check if text fits within table bounds at a given position.

        Args:
            text: Text content
            center_x: X coordinate of text center
            center_y: Y coordinate of text center
            offset: Vertical offset in mm
            direction: Direction - 'up', 'down', 'left', 'right'

        Returns:
            True if text fits within bounds
        """
        text_width = self._estimate_text_width(text)
        text_height = 20  # Approximate text height at 14px

        if direction == "up":
            text_y = center_y - offset
            return text_y - text_height // 2 >= 0
        elif direction == "down":
            text_y = center_y + offset
            return text_y + text_height // 2 <= self.table_height_mm
        elif direction == "left":
            text_x = center_x - offset
            return text_x - text_width // 2 >= 0
        elif direction == "right":
            text_x = center_x + offset
            return text_x + text_width // 2 <= self.table_width_mm

        return True

    def _get_position_preference_order(
        self, cx: int, cy: int
    ) -> list[tuple[int, int, str]]:
        """Determine position preference order based on proximity to edges.

        For edge cases, intelligently selects positions away from edges.
        For corners, combines both axis logic to find best readable position.
        Adds extra offset for horizontal positions to account for objective radius.

        Args:
            cx: X coordinate of objective point
            cy: Y coordinate of objective point

        Returns:
            List of positions in preference order
        """
        offset_distance = 50  # Base offset from objective center
        extra_horizontal_offset = 50  # Extra offset for left/right (due to radius)
        space_up = cy
        space_down = self.table_height_mm - cy
        space_left = cx
        space_right = self.table_width_mm - cx

        # Threshold for considering a position "near" the edge
        near_threshold = offset_distance + 30

        # Determine which edge(s) we're close to
        near_left = space_left < near_threshold
        near_right = space_right < near_threshold
        near_top = space_up < near_threshold
        near_bottom = space_down < near_threshold

        positions = []

        # Corner cases: near two edges simultaneously
        if near_top and near_left:
            # Top-left corner: prefer down and right (with extra offset for right)
            positions.extend(
                [
                    (cx, cy + offset_distance, "down"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                    (cx, cy - offset_distance, "up"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                ]
            )
        elif near_top and near_right:
            # Top-right corner: prefer down and left (with extra offset for left)
            positions.extend(
                [
                    (cx, cy + offset_distance, "down"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                    (cx, cy - offset_distance, "up"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                ]
            )
        elif near_bottom and near_left:
            # Bottom-left corner: prefer up and right (with extra offset for right)
            positions.extend(
                [
                    (cx, cy - offset_distance, "up"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                    (cx, cy + offset_distance, "down"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                ]
            )
        elif near_bottom and near_right:
            # Bottom-right corner: prefer up and left (with extra offset for left)
            positions.extend(
                [
                    (cx, cy - offset_distance, "up"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                    (cx, cy + offset_distance, "down"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                ]
            )
        # Edge cases (near one edge only)
        elif near_left and not near_right:
            # Near left edge: prefer right (with extra offset)
            positions.extend(
                [
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                    (cx, cy - offset_distance, "up"),
                    (cx, cy + offset_distance, "down"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                ]
            )
        elif near_right and not near_left:
            # Near right edge: prefer left (with extra offset)
            positions.extend(
                [
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                    (cx, cy - offset_distance, "up"),
                    (cx, cy + offset_distance, "down"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                ]
            )
        elif near_top and not near_bottom:
            # Near top edge: prefer down
            positions.extend(
                [
                    (cx, cy + offset_distance, "down"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                    (cx, cy - offset_distance, "up"),
                ]
            )
        elif near_bottom and not near_top:
            # Near bottom edge: prefer up
            positions.extend(
                [
                    (cx, cy - offset_distance, "up"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                    (cx, cy + offset_distance, "down"),
                ]
            )
        else:
            # Not close to any edge, prefer vertical (more readable)
            # Always try up first, then down, then right/left with extra offset
            positions.extend(
                [
                    (cx, cy - offset_distance, "up"),
                    (cx, cy + offset_distance, "down"),
                    (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                    (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                ]
            )

        return positions

    def _find_best_objective_position(  # noqa: C901
        self, cx: int, cy: int, text: str
    ) -> tuple[int, int, str]:
        """Find the best position to place objective label text.

        Places text adjacent to objective circle (radius 25mm) ensuring
        it stays completely within table bounds.

        Args:
            cx: X coordinate of objective point
            cy: Y coordinate of objective point
            text: Text content to position

        Returns:
            Tuple of (x, y, direction) coordinates and direction for text label
        """
        text_width = self._estimate_text_width(text)
        text_height = 20  # Approximate text height at 14px
        objective_radius = 25  # mm - radius of objective circle
        margin = 25  # mm - comfortable gap between objective and text
        offset = objective_radius + margin  # 50mm from objective center

        # Calculate available space in each direction
        space_up = cy
        space_down = self.table_height_mm - cy
        space_left = cx
        space_right = self.table_width_mm - cx

        # Try positions in order of preference based on available space
        # Prefer positions with more space
        candidates = []

        # UP: text above objective (horizontal, no rotation)
        text_x_up = cx
        text_y_up = cy - offset
        # Clamp horizontally to keep text inside table
        if text_x_up - text_width // 2 < 0:
            text_x_up = text_width // 2
        elif text_x_up + text_width // 2 > self.table_width_mm:
            text_x_up = self.table_width_mm - text_width // 2
        # Check if fits vertically
        if text_y_up - text_height // 2 >= 0:
            candidates.append((space_up, text_x_up, text_y_up, "up"))

        # DOWN: text below objective (horizontal, no rotation)
        text_x_down = cx
        text_y_down = cy + offset
        # Clamp horizontally
        if text_x_down - text_width // 2 < 0:
            text_x_down = text_width // 2
        elif text_x_down + text_width // 2 > self.table_width_mm:
            text_x_down = self.table_width_mm - text_width // 2
        # Check if fits vertically
        if text_y_down + text_height // 2 <= self.table_height_mm:
            candidates.append((space_down, text_x_down, text_y_down, "down"))

        # RIGHT: text to right of objective (rotated 90°)
        text_x_right = cx + offset
        text_y_right = cy
        # When rotated, width becomes height - clamp vertically
        if text_y_right - text_width // 2 < 0:
            text_y_right = text_width // 2
        elif text_y_right + text_width // 2 > self.table_height_mm:
            text_y_right = self.table_height_mm - text_width // 2
        # Check if fits horizontally
        if text_x_right + text_height // 2 <= self.table_width_mm:
            candidates.append((space_right, text_x_right, text_y_right, "right"))

        # LEFT: text to left of objective (rotated -90°)
        text_x_left = cx - offset
        text_y_left = cy
        # When rotated, width becomes height - clamp vertically
        if text_y_left - text_width // 2 < 0:
            text_y_left = text_width // 2
        elif text_y_left + text_width // 2 > self.table_height_mm:
            text_y_left = self.table_height_mm - text_width // 2
        # Check if fits horizontally
        if text_x_left - text_height // 2 >= 0:
            candidates.append((space_left, text_x_left, text_y_left, "left"))

        # Return position with most available space
        if candidates:
            # Sort by space available (descending)
            candidates.sort(key=lambda x: x[0], reverse=True)

            # Apply UX preference (up > down > right > left) only when objective
            # is well-centered, meaning it's far from ALL edges (>= 200mm).
            # This ensures natural reading order when centered, while using
            # optimal direction when near any edge.
            min_edge_dist = min(space_up, space_down, space_left, space_right)
            if min_edge_dist >= 200:  # Far from all edges
                # Prefer up, then down, then right, then left
                preference_order = ["up", "down", "right", "left"]
                for preferred_dir in preference_order:
                    for _space, x, y, direction in candidates:
                        if direction == preferred_dir:
                            return x, y, direction

            # Otherwise: use candidate with most space (objective near edge)
            _, best_x, best_y, best_dir = candidates[0]
            return best_x, best_y, best_dir

        # Ultimate fallback: center text on objective
        return cx, cy, "up"

    def _text_label_svg(
        self,
        x: int,
        y: int,
        text: str,
        font_size: int = 16,
        fill: str = "#000",
        direction: str = "up",
    ) -> str:
        """Render a text label at specified coordinates.

        Args:
            x: X coordinate for text anchor
            y: Y coordinate for text baseline
            text: Text content (will be escaped)
            font_size: Font size in pixels
            fill: Text color
            direction: Direction of label (up, down, left, right) for rotation

        Returns:
            SVG text element string
        """
        escaped = self._escape_text(text)
        text_elem = (
            f'<text x="{x}" y="{y}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-size="{font_size}" font-family="Arial, sans-serif" '
            f'fill="{fill}" font-weight="bold">'
            f"{escaped}</text>"
        )

        # Apply rotation for left/right positioned labels
        if direction == "right":
            return f'<g transform="rotate(90 {x} {y})">{text_elem}</g>'
        elif direction == "left":
            return f'<g transform="rotate(-90 {x} {y})">{text_elem}</g>'
        else:
            return text_elem

    def _svg_header(self, width: int, height: int) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            'style="background:#f5f5f5;">'
        )

    def _rect_svg(self, shape: dict) -> str:
        """Render rect with deployment zone styling (semi-transparent fill)."""
        x = int(shape["x"])
        y = int(shape["y"])
        w = int(shape["width"])
        h = int(shape["height"])
        # Default to blue deployment zone styling
        fill = shape.get("fill", "rgba(100,150,250,0.3)")
        stroke = shape.get("stroke", "#4070c0")
        stroke_width = shape.get("stroke-width", "2")
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
        )

    def _circle_svg(self, shape: dict) -> str:
        """Render circle with scenography styling (gray outline, transparent fill)."""
        cx = int(shape["cx"])
        cy = int(shape["cy"])
        r = int(shape["r"])
        # Default to scenography styling
        fill = shape.get("fill", "rgba(128,128,128,0.2)")
        stroke = shape.get("stroke", "#666")
        stroke_width = shape.get("stroke-width", "2")
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
        )

    def _polygon_svg(self, shape: dict) -> str:
        """Render polygon with deployment zone styling."""
        points = shape["points"]
        points_str = " ".join(f'{int(p["x"])},{int(p["y"])}' for p in points)
        # Default to red deployment zone styling
        fill = shape.get("fill", "rgba(250,100,100,0.3)")
        stroke = shape.get("stroke", "#c04040")
        stroke_width = shape.get("stroke-width", "2")
        return (
            f'<polygon points="{points_str}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
        )

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
        self.table_width_mm = int(table_mm["width_mm"])
        self.table_height_mm = int(table_mm["height_mm"])

        width = self.table_width_mm
        height = self.table_height_mm

        parts: list[str] = []

        # SVG header
        parts.append(self._svg_header(width, height))

        # Table background (white playing area with border)
        parts.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" '
            'fill="white" stroke="#333" stroke-width="3" />'
        )

        # Render shapes
        for shape in shapes:
            svg = self._shape_svg(shape)
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
        """Render label for a shape based on its type and description.

        Args:
            shape: Shape dictionary with type, coordinates, and description

        Returns:
            SVG text element or None if no description or unsupported type
        """
        description = shape.get("description", "").strip()
        if not description:
            return None

        shape_type = shape.get("type")

        if shape_type == "rect":
            cx, cy = self._calculate_rect_center(shape)
            return self._text_label_svg(cx, cy, description, font_size=14, fill="#003")

        elif shape_type == "circle":
            cx, cy = self._calculate_circle_center(shape)
            return self._text_label_svg(cx, cy, description, font_size=14, fill="#333")

        elif shape_type == "polygon":
            cx, cy = self._calculate_polygon_center(shape)
            return self._text_label_svg(cx, cy, description, font_size=14, fill="#300")

        elif shape_type == "objective_point":
            # Find best position for text (intelligent placement)
            cx = int(shape.get("cx", 0))
            cy = int(shape.get("cy", 0))
            text_x, text_y, direction = self._find_best_objective_position(
                cx, cy, description
            )
            return self._text_label_svg(
                text_x,
                text_y,
                description,
                font_size=14,
                fill="#000",
                direction=direction,
            )

        return None

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
