"""Unit tests for _deployment/_ui_updates.py — pure UI-state helpers.

Tests cover:
- zone_type_visibility: all three zone types
- border_fill_field_states: fill_side True/False x north-south/east-west
- perfect_triangle_side2: locked/unlocked
"""

from __future__ import annotations

from adapters.ui_gradio.ui.wiring._deployment._ui_updates import (
    border_fill_field_states,
    perfect_triangle_side2,
    zone_type_visibility,
)


# ---------------------------------------------------------------------------
# zone_type_visibility
# ---------------------------------------------------------------------------
class TestZoneTypeVisibility:
    """Visibility flags per zone type."""

    def test_rectangle(self):
        v = zone_type_visibility("rectangle")
        assert v["border_row"] is True
        assert v["corner_row"] is False
        assert v["rect_dimensions_row"] is True
        assert v["triangle_dimensions_row"] is False
        assert v["circle_dimensions_row"] is False

    def test_triangle(self):
        v = zone_type_visibility("triangle")
        assert v["border_row"] is False
        assert v["corner_row"] is True
        assert v["perfect_triangle_row"] is True
        assert v["triangle_dimensions_row"] is True
        assert v["rect_dimensions_row"] is False

    def test_circle(self):
        v = zone_type_visibility("circle")
        assert v["corner_row"] is True
        assert v["circle_dimensions_row"] is True
        assert v["border_row"] is False
        assert v["triangle_dimensions_row"] is False

    def test_unknown_type(self):
        """Unknown types behave like rectangle (all False except 'separation_row')."""
        v = zone_type_visibility("hexagon")
        assert v["border_row"] is False
        assert v["corner_row"] is False

    def test_returns_all_eight_keys(self):
        v = zone_type_visibility("rectangle")
        assert len(v) == 8


# ---------------------------------------------------------------------------
# border_fill_field_states
# ---------------------------------------------------------------------------
class TestBorderFillFieldStates:
    """Per-field lock state for border/fill_side combinations."""

    def test_fill_north_locks_width_and_sep_x(self):
        fs = border_fill_field_states("north", True, 120.0, 80.0, "cm")
        assert fs["width"]["interactive"] is False
        assert fs["width"]["value"] == 120.0
        assert fs["sep_x"]["interactive"] is False
        assert fs["sep_x"]["value"] == 0
        # height and sep_y stay interactive
        assert fs["height"]["interactive"] is True
        assert fs["sep_y"]["interactive"] is True

    def test_fill_south_same_as_north(self):
        fs = border_fill_field_states("south", True, 100.0, 50.0, "cm")
        assert fs["width"]["interactive"] is False
        assert fs["height"]["interactive"] is True

    def test_fill_east_locks_height_and_sep_y(self):
        fs = border_fill_field_states("east", True, 120.0, 80.0, "cm")
        assert fs["height"]["interactive"] is False
        assert fs["height"]["value"] == 80.0
        assert fs["sep_y"]["interactive"] is False
        assert fs["width"]["interactive"] is True
        assert fs["sep_x"]["interactive"] is True

    def test_fill_west_same_as_east(self):
        fs = border_fill_field_states("west", True, 120.0, 80.0, "cm")
        assert fs["height"]["interactive"] is False
        assert fs["width"]["interactive"] is True

    def test_no_fill_all_interactive(self):
        fs = border_fill_field_states("north", False, 120.0, 80.0, "cm")
        for name in ("width", "height", "sep_x", "sep_y"):
            assert fs[name]["interactive"] is True

    def test_labels_contain_unit(self):
        fs = border_fill_field_states("north", False, 120.0, 80.0, "in")
        for name in ("width", "height", "sep_x", "sep_y"):
            assert "(in)" in fs[name]["label"]  # type: ignore[operator]

    def test_locked_labels_contain_locked_suffix(self):
        fs = border_fill_field_states("north", True, 120.0, 80.0, "cm")
        assert "[LOCKED]" in fs["width"]["label"]  # type: ignore[operator]
        assert "[LOCKED]" not in fs["height"]["label"]  # type: ignore[operator]


# ---------------------------------------------------------------------------
# perfect_triangle_side2
# ---------------------------------------------------------------------------
class TestPerfectTriangleSide2:
    """Side2 lock/unlock state."""

    def test_perfect_locks_side2(self):
        s = perfect_triangle_side2(True, 25.0, "cm")
        assert s["value"] == 25.0
        assert s["interactive"] is False
        assert "[LOCKED]" in s["label"]  # type: ignore[operator]

    def test_not_perfect_unlocks_side2(self):
        s = perfect_triangle_side2(False, 25.0, "cm")
        assert "value" not in s
        assert s["interactive"] is True
        assert "[LOCKED]" not in s["label"]  # type: ignore[operator]

    def test_label_contains_unit(self):
        s = perfect_triangle_side2(False, 10.0, "ft")
        assert "(ft)" in s["label"]  # type: ignore[operator]
