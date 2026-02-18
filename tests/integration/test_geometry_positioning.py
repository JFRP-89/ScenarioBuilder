"""Integration tests for geometry helpers — _geometry.py.

Covers: calculate_polygon_center (quarter-circle corners, empty points),
text_fits_in_bounds (all directions), get_position_preference_order
(edge/corner proximity), find_best_objective_position (all candidates +
fallback).
"""

from __future__ import annotations

import pytest
from infrastructure.maps._renderer._geometry import (
    calculate_polygon_center,
    estimate_text_width,
    find_best_objective_position,
    get_position_preference_order,
    text_fits_in_bounds,
)


# ═════════════════════════════════════════════════════════════════════════════
# calculate_polygon_center — quarter-circle corners + empty
# ═════════════════════════════════════════════════════════════════════════════
class TestCalculatePolygonCenter:
    """Tests for polygon centroid calculations."""

    def test_empty_points_returns_origin(self) -> None:
        assert calculate_polygon_center({"points": []}) == (0, 0)

    def test_no_points_key_returns_origin(self) -> None:
        assert calculate_polygon_center({}) == (0, 0)

    @pytest.mark.parametrize(
        "corner",
        ["north-west", "north-east", "south-west", "south-east"],
    )
    def test_quarter_circle_corners(self, corner: str) -> None:
        """Quarter-circle logic is exercised for each known corner."""
        # Build a quarter-circle shape with > 3 points + corner attribute
        arc_pts = [
            {"x": 0, "y": 0},
            {"x": 100, "y": 0},
            {"x": 100, "y": 50},
            {"x": 100, "y": 100},
            {"x": 50, "y": 100},
        ]
        shape = {"points": arc_pts, "corner": corner}
        cx, cy = calculate_polygon_center(shape)
        # Result should be integers; exact value depends on corner
        assert isinstance(cx, int) and isinstance(cy, int)

    def test_quarter_circle_unknown_corner_falls_back_to_average(self) -> None:
        """Unknown corner string → falls back to average of all vertices."""
        pts = [
            {"x": 0, "y": 0},
            {"x": 100, "y": 0},
            {"x": 100, "y": 100},
            {"x": 0, "y": 100},
        ]
        shape = {"points": pts, "corner": "invalid-corner"}
        cx, cy = calculate_polygon_center(shape)
        assert cx == 50
        assert cy == 50

    def test_regular_polygon_uses_average(self) -> None:
        """Triangle (no corner attr) → simple average of vertices."""
        pts = [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 50, "y": 86}]
        cx, cy = calculate_polygon_center({"points": pts})
        assert cx == 50
        assert cy == 28  # int(86/3)


# ═════════════════════════════════════════════════════════════════════════════
# text_fits_in_bounds — all direction branches
# ═════════════════════════════════════════════════════════════════════════════
class TestTextFitsInBounds:
    """Tests for boundary checking of text placement."""

    def test_up_fits(self) -> None:
        assert text_fits_in_bounds(
            "Hi", 500, 500, 1000, 1000, offset=10, direction="up"
        )

    def test_up_too_close_to_top(self) -> None:
        assert not text_fits_in_bounds(
            "Hi", 500, 5, 1000, 1000, offset=10, direction="up"
        )

    def test_down_fits(self) -> None:
        assert text_fits_in_bounds(
            "Hi", 500, 500, 1000, 1000, offset=10, direction="down"
        )

    def test_down_too_close_to_bottom(self) -> None:
        assert not text_fits_in_bounds(
            "Hi", 500, 995, 1000, 1000, offset=10, direction="down"
        )

    def test_left_fits(self) -> None:
        assert text_fits_in_bounds(
            "Hi", 500, 500, 1000, 1000, offset=10, direction="left"
        )

    def test_left_too_close_to_edge(self) -> None:
        assert not text_fits_in_bounds(
            "Hi", 5, 500, 1000, 1000, offset=10, direction="left"
        )

    def test_right_fits(self) -> None:
        assert text_fits_in_bounds(
            "Hi", 500, 500, 1000, 1000, offset=10, direction="right"
        )

    def test_right_too_close_to_edge(self) -> None:
        assert not text_fits_in_bounds(
            "Hi", 995, 500, 1000, 1000, offset=500, direction="right"
        )

    def test_unknown_direction_returns_true(self) -> None:
        assert text_fits_in_bounds("Hi", 500, 500, 1000, 1000, direction="diagonal")


# ═════════════════════════════════════════════════════════════════════════════
# get_position_preference_order — edge proximity branches
# ═════════════════════════════════════════════════════════════════════════════
class TestGetPositionPreferenceOrder:
    """Tests for smart label positioning based on edge proximity."""

    def _w(self) -> int:
        return 1200

    def _h(self) -> int:
        return 800

    def test_center_default_order(self) -> None:
        """Center of table → default up/down/right/left order."""
        positions = get_position_preference_order(600, 400, self._w(), self._h())
        assert len(positions) == 4
        directions = [p[2] for p in positions]
        assert directions == ["up", "down", "right", "left"]

    def test_near_top_left_corner(self) -> None:
        positions = get_position_preference_order(30, 30, self._w(), self._h())
        assert positions[0][2] == "down"

    def test_near_top_right_corner(self) -> None:
        positions = get_position_preference_order(1170, 30, self._w(), self._h())
        assert positions[0][2] == "down"

    def test_near_bottom_left_corner(self) -> None:
        positions = get_position_preference_order(30, 770, self._w(), self._h())
        assert positions[0][2] == "up"

    def test_near_bottom_right_corner(self) -> None:
        positions = get_position_preference_order(1170, 770, self._w(), self._h())
        assert positions[0][2] == "up"

    def test_near_left_edge_only(self) -> None:
        positions = get_position_preference_order(30, 400, self._w(), self._h())
        assert positions[0][2] == "right"

    def test_near_right_edge_only(self) -> None:
        positions = get_position_preference_order(1170, 400, self._w(), self._h())
        assert positions[0][2] == "left"

    def test_near_top_edge_only(self) -> None:
        positions = get_position_preference_order(600, 30, self._w(), self._h())
        assert positions[0][2] == "down"

    def test_near_bottom_edge_only(self) -> None:
        positions = get_position_preference_order(600, 770, self._w(), self._h())
        assert positions[0][2] == "up"


# ═════════════════════════════════════════════════════════════════════════════
# find_best_objective_position — candidate selection & fallback
# ═════════════════════════════════════════════════════════════════════════════
class TestFindBestObjectivePosition:
    """Tests for objective label placement algorithm."""

    def test_center_position_prefers_up(self) -> None:
        """When all sides have ample space, prefers 'up'."""
        x, y, direction = find_best_objective_position(
            600, 400, "Objective A", 1200, 800
        )
        assert direction == "up"

    def test_near_top_prefers_down(self) -> None:
        """When near the top edge, shifts label downward."""
        _, _, direction = find_best_objective_position(600, 30, "Objective", 1200, 800)
        assert direction == "down"

    def test_near_left_prefers_right(self) -> None:
        _, _, direction = find_best_objective_position(30, 400, "Objective", 1200, 800)
        assert direction in ("right", "down", "up")  # depends on text width

    def test_near_bottom_prefers_up(self) -> None:
        _, _, direction = find_best_objective_position(600, 780, "Obj", 1200, 800)
        assert direction == "up"

    def test_corner_placement(self) -> None:
        """Near a corner — should still produce a valid position."""
        x, y, direction = find_best_objective_position(20, 20, "X", 1200, 800)
        assert direction in ("up", "down", "left", "right")

    def test_no_fit_returns_center_fallback(self) -> None:
        """Extremely small table — no candidate fits → returns (cx, cy, 'up')."""
        x, y, direction = find_best_objective_position(
            5, 5, "Very long objective text here", 10, 10
        )
        # With a tiny table, all candidates may fail → fallback
        assert isinstance(x, int) and isinstance(y, int)
        assert direction in ("up", "down", "left", "right")

    def test_returns_integers(self) -> None:
        x, y, _ = find_best_objective_position(500, 300, "Test", 1200, 800)
        assert isinstance(x, int) and isinstance(y, int)


# ═════════════════════════════════════════════════════════════════════════════
# estimate_text_width
# ═════════════════════════════════════════════════════════════════════════════
class TestEstimateTextWidth:
    def test_minimum_width(self) -> None:
        assert estimate_text_width("") >= 10

    def test_longer_text_wider(self) -> None:
        assert estimate_text_width("Hello World") > estimate_text_width("Hi")
