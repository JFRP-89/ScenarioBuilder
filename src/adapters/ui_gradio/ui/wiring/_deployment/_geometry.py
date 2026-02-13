"""Pure geometry helpers for deployment zone shapes.

Every function here is a **pure function** — no Gradio, no API calls.
Only dependency: ``math`` for trigonometry.
"""

from __future__ import annotations

import math


def _calculate_triangle_vertices(
    corner: str, side1_mm: int, side2_mm: int, table_w_mm: int, table_h_mm: int
) -> list[tuple[int, int]]:
    """Calculate triangle vertices from corner position and side lengths.

    Creates a right isosceles triangle with one vertex at the specified corner
    and the other two vertices along the adjacent table edges.

    Args:
        corner: One of "north-west", "north-east", "south-west", "south-east"
        side1_mm: Length of first cathetus in mm (vertical from corner)
        side2_mm: Length of second cathetus in mm (horizontal from corner)
        table_w_mm: Table width in mm
        table_h_mm: Table height in mm

    Returns:
        List of 3 (x, y) tuples representing the triangle vertices in mm coordinates
    """
    if corner == "north-west":
        # Corner at (0, 0)
        return [(0, 0), (0, side2_mm), (side1_mm, 0)]
    elif corner == "north-east":
        # Corner at (W, 0)
        return [(table_w_mm, 0), (table_w_mm, side2_mm), (table_w_mm - side1_mm, 0)]
    elif corner == "south-west":
        # Corner at (0, H)
        return [(0, table_h_mm), (0, table_h_mm - side2_mm), (side1_mm, table_h_mm)]
    elif corner == "south-east":
        # Corner at (W, H)
        return [
            (table_w_mm, table_h_mm),
            (table_w_mm, table_h_mm - side2_mm),
            (table_w_mm - side1_mm, table_h_mm),
        ]
    else:
        raise ValueError(f"Invalid corner: {corner}")


def _calculate_circle_vertices(
    corner: str,
    radius_mm: int,
    table_w_mm: int,
    table_h_mm: int,
    num_points: int = 20,
) -> list[tuple[int, int]]:
    """Calculate quarter-circle vertices from corner position and radius.

    Creates a quarter circle anchored at the specified corner,
    approximated as a polygon with num_points vertices.

    Args:
        corner: One of "north-west", "north-east", "south-west", "south-east"
        radius_mm: Radius of the quarter circle in mm
        table_w_mm: Table width in mm
        table_h_mm: Table height in mm
        num_points: Number of points to approximate the arc (default 20)

    Returns:
        List of (x, y) tuples representing the quarter-circle vertices in mm coordinates
    """
    # Generate arc points (0 to 90 degrees)
    vertices: list[tuple[int, int]] = []

    if corner == "north-west":
        # Quarter circle from (radius, 0) to (0, radius), corner at (0, 0)
        vertices.append((0, 0))
        for i in range(num_points + 1):
            angle = math.pi / 2 * i / num_points  # 0 to 90 degrees
            x = int(radius_mm * math.cos(angle))
            y = int(radius_mm * math.sin(angle))
            vertices.append((x, y))

    elif corner == "north-east":
        # Quarter circle from (W - radius, 0) to (W, radius), corner at (W, 0)
        vertices.append((table_w_mm, 0))
        for i in range(num_points + 1):
            angle = math.pi / 2 * i / num_points
            x = int(table_w_mm - radius_mm * math.cos(angle))
            y = int(radius_mm * math.sin(angle))
            vertices.append((x, y))

    elif corner == "south-west":
        # Quarter circle from (0, H - radius) to (radius, H), corner at (0, H)
        vertices.append((0, table_h_mm))
        for i in range(num_points + 1):
            angle = math.pi / 2 * i / num_points
            x = int(radius_mm * math.cos(angle))
            y = int(table_h_mm - radius_mm * math.sin(angle))
            vertices.append((x, y))

    elif corner == "south-east":
        # Quarter circle from (W, H - radius) to (W - radius, H), corner at (W, H)
        vertices.append((table_w_mm, table_h_mm))
        for i in range(num_points + 1):
            angle = math.pi / 2 * i / num_points
            x = int(table_w_mm - radius_mm * math.cos(angle))
            y = int(table_h_mm - radius_mm * math.sin(angle))
            vertices.append((x, y))
    else:
        raise ValueError(f"Invalid corner: {corner}")

    return vertices
