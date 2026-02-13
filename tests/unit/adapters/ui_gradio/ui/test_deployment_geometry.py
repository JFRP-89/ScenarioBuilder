"""Unit tests for _deployment/_geometry.py — pure geometry helpers.

Tests cover:
- Triangle vertex calculation for all 4 corners
- Circle (quarter-arc) vertex calculation for all 4 corners
- Deterministic numeric results
- Edge cases (invalid corner)
"""

from __future__ import annotations

import math

import pytest
from adapters.ui_gradio.ui.wiring._deployment._geometry import (
    _calculate_circle_vertices,
    _calculate_triangle_vertices,
)


# ---------------------------------------------------------------------------
# _calculate_triangle_vertices
# ---------------------------------------------------------------------------
class TestCalculateTriangleVertices:
    """All triangles are right triangles anchored at a table corner."""

    def test_north_west(self):
        verts = _calculate_triangle_vertices("north-west", 300, 200, 1200, 800)
        assert len(verts) == 3
        assert verts[0] == (0, 0)  # corner
        assert verts[1] == (0, 200)  # along Y (side2)
        assert verts[2] == (300, 0)  # along X (side1)

    def test_north_east(self):
        verts = _calculate_triangle_vertices("north-east", 300, 200, 1200, 800)
        assert len(verts) == 3
        assert verts[0] == (1200, 0)  # corner
        assert verts[1] == (1200, 200)  # along Y
        assert verts[2] == (900, 0)  # W - side1

    def test_south_west(self):
        verts = _calculate_triangle_vertices("south-west", 300, 200, 1200, 800)
        assert len(verts) == 3
        assert verts[0] == (0, 800)  # corner
        assert verts[1] == (0, 600)  # H - side2
        assert verts[2] == (300, 800)  # along X

    def test_south_east(self):
        verts = _calculate_triangle_vertices("south-east", 300, 200, 1200, 800)
        assert len(verts) == 3
        assert verts[0] == (1200, 800)
        assert verts[1] == (1200, 600)
        assert verts[2] == (900, 800)

    def test_all_coords_are_ints(self):
        for corner in ("north-west", "north-east", "south-west", "south-east"):
            verts = _calculate_triangle_vertices(corner, 250, 150, 1000, 700)
            for x, y in verts:
                assert isinstance(x, int)
                assert isinstance(y, int)

    def test_invalid_corner_raises(self):
        with pytest.raises(ValueError, match="Invalid corner"):
            _calculate_triangle_vertices("center", 100, 100, 1200, 800)


# ---------------------------------------------------------------------------
# _calculate_circle_vertices
# ---------------------------------------------------------------------------
class TestCalculateCircleVertices:
    """Quarter-circle arcs anchored at table corners."""

    def test_north_west_vertex_count(self):
        verts = _calculate_circle_vertices("north-west", 300, 1200, 800, num_points=10)
        # corner + (num_points + 1) arc points = 12
        assert len(verts) == 12
        assert verts[0] == (0, 0)  # corner anchor

    def test_north_east_vertex_count(self):
        verts = _calculate_circle_vertices("north-east", 300, 1200, 800, num_points=10)
        assert len(verts) == 12
        assert verts[0] == (1200, 0)

    def test_south_west_vertex_count(self):
        verts = _calculate_circle_vertices("south-west", 300, 1200, 800, num_points=10)
        assert len(verts) == 12
        assert verts[0] == (0, 800)

    def test_south_east_vertex_count(self):
        verts = _calculate_circle_vertices("south-east", 300, 1200, 800, num_points=10)
        assert len(verts) == 12
        assert verts[0] == (1200, 800)

    def test_default_num_points(self):
        verts = _calculate_circle_vertices("north-west", 300, 1200, 800)
        # corner + 21 arc points = 22
        assert len(verts) == 22

    def test_all_coords_are_ints(self):
        for corner in ("north-west", "north-east", "south-west", "south-east"):
            verts = _calculate_circle_vertices(corner, 250, 1000, 700, num_points=8)
            for x, y in verts:
                assert isinstance(x, int)
                assert isinstance(y, int)

    def test_arc_points_within_radius(self):
        """Arc points (excluding corner) should be within radius of the corner."""
        radius = 300
        verts = _calculate_circle_vertices(
            "north-west", radius, 1200, 800, num_points=20
        )
        # Skip corner (index 0), check arc points
        for x, y in verts[1:]:
            dist = math.sqrt(x**2 + y**2)
            # Allow int rounding tolerance
            assert dist <= radius + 2, f"Point ({x},{y}) too far from corner: {dist}"

    def test_invalid_corner_raises(self):
        with pytest.raises(ValueError, match="Invalid corner"):
            _calculate_circle_vertices("center", 300, 1200, 800)
