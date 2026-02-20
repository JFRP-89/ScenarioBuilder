"""Unit tests for _deployment/_zone_builder.py — zone data construction.

Tests cover:
- build_zone_data: rectangle, triangle, circle — valid and invalid inputs
- Validation errors returned as strings (never raises)
- Bounds checking for triangle and circle vertices
- form_params construction for each zone type
- Edge cases: empty description, zero/negative dimensions, missing corner
"""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._deployment._zone_builder import (
    ZoneFormInput,
    build_zone_data,
)

# -- Helpers ----------------------------------------------------------------
_COMMON = {
    "zone_type": "rectangle",
    "description": "Default",
    "border": "north",
    "corner": "north-west",
    "fill_side": False,
    "width": 120,
    "height": 20,
    "tri_side1": 30,
    "tri_side2": 30,
    "circle_radius": 30,
    "sep_x": 0,
    "sep_y": 0,
    "zone_unit": "cm",
}

_TABLE_W = 1200
_TABLE_H = 800


def _build(**overrides):
    """Call build_zone_data with defaults + overrides."""
    kw = {**_COMMON, **overrides}
    table_w = kw.pop("table_w_mm", _TABLE_W)
    table_h = kw.pop("table_h_mm", _TABLE_H)
    form = ZoneFormInput(**kw)
    return build_zone_data(form, table_w_mm=table_w, table_h_mm=table_h)


# ---------------------------------------------------------------------------
# Rectangle
# ---------------------------------------------------------------------------
class TestBuildRectangle:
    """build_zone_data with zone_type='rectangle'."""

    def test_valid_rect(self):
        zd, _, err = _build(zone_type="rectangle", description="Front")
        assert err is None
        assert zd is not None
        assert zd["type"] == "rect"
        assert zd["description"] == "Front"
        assert "width" in zd and "height" in zd

    def test_form_params_rect(self):
        _, fp, _ = _build(zone_type="rectangle", description="Front")
        assert fp is not None
        assert fp["unit"] == "cm"
        assert "border" in fp
        assert "width" in fp

    def test_missing_description(self):
        _, _, err = _build(zone_type="rectangle", description="")
        assert err is not None
        assert "Description" in err

    def test_whitespace_only_description(self):
        _, _, err = _build(zone_type="rectangle", description="   ")
        assert err is not None

    def test_zero_width(self):
        _, _, err = _build(zone_type="rectangle", description="X", width=0)
        assert err is not None
        assert "Width" in err

    def test_negative_height(self):
        _, _, err = _build(zone_type="rectangle", description="X", height=-5)
        assert err is not None
        assert "Height" in err

    def test_missing_border(self):
        _, _, err = _build(zone_type="rectangle", description="X", border="")
        assert err is not None
        assert "Border" in err

    def test_fill_side_north_locks_width(self):
        """When fill_side=True + border=north, width should equal table width."""
        zd, _, _ = _build(
            zone_type="rectangle",
            description="Full",
            fill_side=True,
            border="north",
            width=50,
        )
        assert zd is not None
        assert zd["width"] == 1200  # table_w_mm

    def test_fill_side_east_locks_height(self):
        zd, _, _ = _build(
            zone_type="rectangle",
            description="Full",
            fill_side=True,
            border="east",
            height=10,
        )
        assert zd is not None
        assert zd["height"] == 800  # table_h_mm

    def test_never_raises(self):
        """Even with absurd inputs, the function returns an error string."""
        _, _, err = _build(
            zone_type="rectangle",
            description="X",
            width=None,
        )
        assert err is not None


# ---------------------------------------------------------------------------
# Triangle
# ---------------------------------------------------------------------------
class TestBuildTriangle:
    """build_zone_data with zone_type='triangle'."""

    def test_valid_triangle(self):
        zd, _, err = _build(
            zone_type="triangle",
            description="Corner",
            corner="north-west",
            tri_side1=20,
            tri_side2=20,
        )
        assert err is None
        assert zd is not None
        assert zd["type"] == "polygon"
        assert len(zd["points"]) == 3
        assert zd["corner"] == "north-west"

    def test_form_params_triangle(self):
        _, fp, _ = _build(
            zone_type="triangle",
            description="Corner",
            tri_side1=20,
            tri_side2=20,
        )
        assert fp is not None
        assert "side1" in fp
        assert "side2" in fp
        assert "perfect_triangle" in fp

    def test_missing_corner(self):
        _, _, err = _build(zone_type="triangle", description="X", corner="")
        assert err is not None
        assert "Corner" in err

    def test_zero_side1(self):
        _, _, err = _build(zone_type="triangle", description="X", tri_side1=0)
        assert err is not None
        assert "Side Length 1" in err

    def test_negative_side2(self):
        _, _, err = _build(zone_type="triangle", description="X", tri_side2=-1)
        assert err is not None
        assert "Side Length 2" in err

    def test_points_have_xy_keys(self):
        zd, _, _ = _build(
            zone_type="triangle",
            description="T",
            tri_side1=10,
            tri_side2=10,
        )
        assert zd is not None
        for pt in zd["points"]:
            assert "x" in pt and "y" in pt

    def test_perfect_triangle_flag(self):
        _, fp, _ = _build(
            zone_type="triangle",
            description="T",
            tri_side1=20,
            tri_side2=20,
        )
        assert fp["perfect_triangle"] is True

    def test_non_perfect_triangle_flag(self):
        _, fp, _ = _build(
            zone_type="triangle",
            description="T",
            tri_side1=20,
            tri_side2=15,
        )
        assert fp["perfect_triangle"] is False


# ---------------------------------------------------------------------------
# Circle
# ---------------------------------------------------------------------------
class TestBuildCircle:
    """build_zone_data with zone_type='circle'."""

    def test_valid_circle(self):
        zd, _, err = _build(
            zone_type="circle",
            description="Arc",
            corner="south-east",
            circle_radius=20,
        )
        assert err is None
        assert zd is not None
        assert zd["type"] == "polygon"
        assert len(zd["points"]) > 3
        assert zd["corner"] == "south-east"

    def test_form_params_circle(self):
        _, fp, _ = _build(
            zone_type="circle",
            description="Arc",
            circle_radius=20,
        )
        assert fp is not None
        assert "radius" in fp
        assert "corner" in fp

    def test_missing_corner(self):
        _, _, err = _build(zone_type="circle", description="X", corner="")
        assert err is not None
        assert "Corner" in err

    def test_zero_radius(self):
        _, _, err = _build(zone_type="circle", description="X", circle_radius=0)
        assert err is not None
        assert "Radius" in err

    def test_negative_radius(self):
        _, _, err = _build(zone_type="circle", description="X", circle_radius=-5)
        assert err is not None
        assert "Radius" in err


# ---------------------------------------------------------------------------
# Bounds checking
# ---------------------------------------------------------------------------
class TestBoundsChecking:
    """Triangle/circle that exceed table dimensions → error."""

    def test_triangle_out_of_bounds(self):
        """Triangle sides larger than the table → vertex out of bounds."""
        _, _, err = _build(
            zone_type="triangle",
            description="Huge",
            corner="north-west",
            tri_side1=500,
            tri_side2=500,
            table_w_mm=100,
            table_h_mm=100,
        )
        assert err is not None
        assert "bounds" in err.lower()

    def test_circle_out_of_bounds(self):
        """Circle radius larger than table → vertex out of bounds."""
        _, _, err = _build(
            zone_type="circle",
            description="Huge",
            corner="north-west",
            circle_radius=500,
            table_w_mm=100,
            table_h_mm=100,
        )
        assert err is not None
        assert "bounds" in err.lower()


# ---------------------------------------------------------------------------
# Never raises
# ---------------------------------------------------------------------------
class TestNeverRaises:
    """build_zone_data must never raise — all errors returned as strings."""

    @pytest.mark.parametrize(
        "zone_type",
        ["rectangle", "triangle", "circle", "unknown"],
    )
    def test_no_exception(self, zone_type):
        """build_zone_data must not raise for any zone_type."""
        # If it raises, the test fails automatically — no catch needed.
        _build(zone_type=zone_type, description="test")


# ---------------------------------------------------------------------------
# Compatibility: result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    """build_zone_data always returns a 3-tuple."""

    def test_success_tuple(self):
        result = _build(zone_type="rectangle", description="OK")
        assert isinstance(result, tuple) and len(result) == 3

    def test_error_tuple(self):
        result = _build(zone_type="rectangle", description="")
        assert isinstance(result, tuple) and len(result) == 3
        assert result[0] is None and result[1] is None and result[2] is not None
