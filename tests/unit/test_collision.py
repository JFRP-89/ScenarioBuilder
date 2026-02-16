"""Unit tests for domain.maps.collision -- overlap and bounds checks."""

from __future__ import annotations

from domain.maps.collision import (
    find_first_collision,
    has_no_collisions,
    shape_in_bounds,
    shapes_overlap,
)


# =============================================================================
# RECT x RECT
# =============================================================================
class TestRectRectOverlap:
    """Tests for rectangle-rectangle overlap detection."""

    def test_no_overlap_separated_horizontally(self) -> None:
        a = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        b = {"type": "rect", "x": 200, "y": 0, "width": 100, "height": 100}
        assert not shapes_overlap(a, b)

    def test_no_overlap_separated_vertically(self) -> None:
        a = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        b = {"type": "rect", "x": 0, "y": 200, "width": 100, "height": 100}
        assert not shapes_overlap(a, b)

    def test_overlap_direct(self) -> None:
        a = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        b = {"type": "rect", "x": 50, "y": 50, "width": 100, "height": 100}
        assert shapes_overlap(a, b)

    def test_clearance_violation(self) -> None:
        """Rects separated by less than MIN_CLEARANCE_MM are overlapping."""
        a = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        # Gap is 5mm (< 10mm clearance)
        b = {"type": "rect", "x": 105, "y": 0, "width": 100, "height": 100}
        assert shapes_overlap(a, b, clearance=10)

    def test_exactly_at_clearance_no_overlap(self) -> None:
        """Rects separated by exactly clearance are NOT overlapping."""
        a = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        b = {"type": "rect", "x": 110, "y": 0, "width": 100, "height": 100}
        assert not shapes_overlap(a, b, clearance=10)

    def test_zero_clearance_touching_no_overlap(self) -> None:
        """Touching rects with zero clearance are not overlapping."""
        a = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        b = {"type": "rect", "x": 100, "y": 0, "width": 100, "height": 100}
        assert not shapes_overlap(a, b, clearance=0)

    def test_contained_rect_overlaps(self) -> None:
        a = {"type": "rect", "x": 0, "y": 0, "width": 200, "height": 200}
        b = {"type": "rect", "x": 50, "y": 50, "width": 50, "height": 50}
        assert shapes_overlap(a, b)


# =============================================================================
# CIRCLE x CIRCLE
# =============================================================================
class TestCircleCircleOverlap:
    """Tests for circle-circle overlap detection."""

    def test_no_overlap_distant_circles(self) -> None:
        a = {"type": "circle", "cx": 100, "cy": 100, "r": 50}
        b = {"type": "circle", "cx": 300, "cy": 100, "r": 50}
        assert not shapes_overlap(a, b)

    def test_overlap_intersecting_circles(self) -> None:
        a = {"type": "circle", "cx": 100, "cy": 100, "r": 50}
        b = {"type": "circle", "cx": 150, "cy": 100, "r": 50}
        assert shapes_overlap(a, b)

    def test_clearance_violation_circles(self) -> None:
        """Circles separated by less than clearance overlap."""
        a = {"type": "circle", "cx": 100, "cy": 100, "r": 50}
        # Distance between edges: 200 - 100 - 50 - 50 = 0, plus clearance=10
        b = {"type": "circle", "cx": 205, "cy": 100, "r": 50}
        # Edge gap = 205 - 100 - 50 - 50 = 5 < 10
        assert shapes_overlap(a, b, clearance=10)

    def test_concentric_circles_overlap(self) -> None:
        a = {"type": "circle", "cx": 100, "cy": 100, "r": 80}
        b = {"type": "circle", "cx": 100, "cy": 100, "r": 30}
        assert shapes_overlap(a, b)


# =============================================================================
# RECT x CIRCLE
# =============================================================================
class TestRectCircleOverlap:
    """Tests for rectangle-circle overlap detection."""

    def test_no_overlap_distant(self) -> None:
        rect = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        circle = {"type": "circle", "cx": 300, "cy": 300, "r": 50}
        assert not shapes_overlap(rect, circle)

    def test_overlap_circle_inside_rect(self) -> None:
        rect = {"type": "rect", "x": 0, "y": 0, "width": 200, "height": 200}
        circle = {"type": "circle", "cx": 100, "cy": 100, "r": 30}
        assert shapes_overlap(rect, circle)

    def test_overlap_circle_intersects_edge(self) -> None:
        rect = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        circle = {"type": "circle", "cx": 110, "cy": 50, "r": 30}
        assert shapes_overlap(rect, circle)

    def test_clearance_violation_rect_circle(self) -> None:
        rect = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        # Circle center at 105, r=2 → edge at 103, gap = 3mm < 10mm
        circle = {"type": "circle", "cx": 105, "cy": 50, "r": 2}
        assert shapes_overlap(rect, circle, clearance=10)

    def test_order_independent(self) -> None:
        """shapes_overlap(rect, circle) == shapes_overlap(circle, rect)."""
        rect = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        circle = {"type": "circle", "cx": 80, "cy": 80, "r": 30}
        assert shapes_overlap(rect, circle) == shapes_overlap(circle, rect)


# =============================================================================
# POLYGON (skip / conservative)
# =============================================================================
class TestPolygonOverlap:
    """Polygons are conservatively treated as non-overlapping."""

    def test_polygon_vs_rect_returns_false(self) -> None:
        poly = {
            "type": "polygon",
            "points": [{"x": 0, "y": 0}, {"x": 50, "y": 0}, {"x": 25, "y": 50}],
        }
        rect = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        assert not shapes_overlap(poly, rect)

    def test_polygon_vs_polygon_returns_false(self) -> None:
        a = {
            "type": "polygon",
            "points": [{"x": 0, "y": 0}, {"x": 50, "y": 0}, {"x": 25, "y": 50}],
        }
        b = {
            "type": "polygon",
            "points": [{"x": 10, "y": 10}, {"x": 60, "y": 10}, {"x": 35, "y": 60}],
        }
        assert not shapes_overlap(a, b)


# =============================================================================
# find_first_collision
# =============================================================================
class TestFindFirstCollision:
    """Tests for find_first_collision."""

    def test_no_collision_returns_none(self) -> None:
        shapes = [
            {"type": "rect", "x": 0, "y": 0, "width": 50, "height": 50},
            {"type": "rect", "x": 200, "y": 200, "width": 50, "height": 50},
        ]
        assert find_first_collision(shapes) is None

    def test_collision_returns_pair(self) -> None:
        shapes = [
            {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100},
            {"type": "rect", "x": 50, "y": 50, "width": 100, "height": 100},
        ]
        result = find_first_collision(shapes)
        assert result == (0, 1)

    def test_multiple_collisions_returns_first(self) -> None:
        shapes = [
            {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100},
            {"type": "rect", "x": 50, "y": 50, "width": 100, "height": 100},
            {"type": "rect", "x": 70, "y": 70, "width": 100, "height": 100},
        ]
        result = find_first_collision(shapes)
        assert result == (0, 1)

    def test_empty_list_returns_none(self) -> None:
        assert find_first_collision([]) is None

    def test_single_shape_returns_none(self) -> None:
        shapes = [{"type": "rect", "x": 0, "y": 0, "width": 50, "height": 50}]
        assert find_first_collision(shapes) is None


# =============================================================================
# has_no_collisions
# =============================================================================
class TestHasNoCollisions:
    """Tests for has_no_collisions convenience function."""

    def test_no_collisions(self) -> None:
        shapes = [
            {"type": "rect", "x": 0, "y": 0, "width": 50, "height": 50},
            {"type": "rect", "x": 200, "y": 200, "width": 50, "height": 50},
        ]
        assert has_no_collisions(shapes)

    def test_with_collisions(self) -> None:
        shapes = [
            {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100},
            {"type": "rect", "x": 50, "y": 50, "width": 100, "height": 100},
        ]
        assert not has_no_collisions(shapes)


# =============================================================================
# allow_overlap flag
# =============================================================================
class TestAllowOverlapFlag:
    """Tests for allow_overlap opt-out behavior."""

    def test_allow_overlap_skips_collision(self) -> None:
        a = {
            "type": "rect",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "allow_overlap": True,
        }
        b = {"type": "rect", "x": 50, "y": 50, "width": 100, "height": 100}
        assert not shapes_overlap(a, b)

    def test_allow_overlap_list_has_no_collisions(self) -> None:
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "allow_overlap": True,
            },
            {"type": "rect", "x": 50, "y": 50, "width": 100, "height": 100},
        ]
        assert has_no_collisions(shapes)


# =============================================================================
# shape_in_bounds
# =============================================================================
class TestShapeInBounds:
    """Tests for shape_in_bounds."""

    def test_rect_in_bounds(self) -> None:
        shape = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        assert shape_in_bounds(shape, 1200, 1200)

    def test_rect_out_of_bounds(self) -> None:
        shape = {"type": "rect", "x": 1100, "y": 0, "width": 200, "height": 100}
        assert not shape_in_bounds(shape, 1200, 1200)

    def test_circle_in_bounds(self) -> None:
        shape = {"type": "circle", "cx": 200, "cy": 200, "r": 50}
        assert shape_in_bounds(shape, 1200, 1200)

    def test_circle_out_of_bounds(self) -> None:
        shape = {"type": "circle", "cx": 20, "cy": 200, "r": 50}
        assert not shape_in_bounds(shape, 1200, 1200)

    def test_polygon_in_bounds(self) -> None:
        shape = {
            "type": "polygon",
            "points": [{"x": 10, "y": 10}, {"x": 100, "y": 10}, {"x": 50, "y": 100}],
        }
        assert shape_in_bounds(shape, 1200, 1200)

    def test_polygon_out_of_bounds(self) -> None:
        shape = {
            "type": "polygon",
            "points": [{"x": -1, "y": 10}, {"x": 100, "y": 10}, {"x": 50, "y": 100}],
        }
        assert not shape_in_bounds(shape, 1200, 1200)
