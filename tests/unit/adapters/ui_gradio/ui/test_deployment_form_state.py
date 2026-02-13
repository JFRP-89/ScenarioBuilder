"""Unit tests for _deployment/_form_state.py — pure form-state helpers.

Tests cover:
- default_zone_form: expected keys and default values
- selected_zone_form: reconstruction for each zone type (rect/tri/circle)
- selected_zone_form: unit conversion when stored unit ≠ display unit
- selected_zone_form: missing form_params → all shape fields UNCHANGED
- UNCHANGED sentinel semantics
"""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._deployment._form_state import (
    UNCHANGED,
    default_zone_form,
    selected_zone_form,
)


# ---------------------------------------------------------------------------
# default_zone_form
# ---------------------------------------------------------------------------
class TestDefaultZoneForm:
    """Verify the default reset dict."""

    def test_returns_dict(self):
        result = default_zone_form()
        assert isinstance(result, dict)

    def test_zone_type_is_rectangle(self):
        assert default_zone_form()["zone_type"] == "rectangle"

    def test_visibility_defaults(self):
        d = default_zone_form()
        assert d["border_row_visible"] is True
        assert d["corner_row_visible"] is False
        assert d["rect_dimensions_row_visible"] is True
        assert d["triangle_dimensions_row_visible"] is False
        assert d["circle_dimensions_row_visible"] is False

    def test_editing_state_defaults(self):
        d = default_zone_form()
        assert d["editing_id"] is None
        assert d["add_btn_text"] == "+ Add Zone"
        assert d["cancel_btn_visible"] is False

    def test_numeric_defaults(self):
        d = default_zone_form()
        assert d["width"] == 120
        assert d["height"] == 20
        assert d["triangle_side1"] == 30
        assert d["triangle_side2"] == 30
        assert d["circle_radius"] == 30
        assert d["sep_x"] == 0
        assert d["sep_y"] == 0

    def test_all_expected_keys_present(self):
        d = default_zone_form()
        expected = {
            "zone_type",
            "border",
            "corner",
            "fill_side",
            "perfect_triangle",
            "description",
            "width",
            "height",
            "triangle_side1",
            "triangle_side2",
            "circle_radius",
            "sep_x",
            "sep_y",
            "border_row_visible",
            "corner_row_visible",
            "fill_side_row_visible",
            "perfect_triangle_row_visible",
            "rect_dimensions_row_visible",
            "triangle_dimensions_row_visible",
            "circle_dimensions_row_visible",
            "separation_row_visible",
            "editing_id",
            "add_btn_text",
            "cancel_btn_visible",
        }
        assert set(d.keys()) == expected


# ---------------------------------------------------------------------------
# selected_zone_form — rectangle
# ---------------------------------------------------------------------------
class TestSelectedZoneFormRect:
    """Reconstruct form for a stored rectangle zone."""

    @pytest.fixture()
    def rect_zone(self):
        return {
            "id": "z1",
            "form_type": "rectangle",
            "data": {"description": "Front line"},
            "form_params": {
                "unit": "cm",
                "border": "south",
                "fill_side": False,
                "width": 100,
                "height": 20,
                "sep_x": 5,
                "sep_y": 10,
            },
        }

    def test_zone_type(self, rect_zone):
        r = selected_zone_form(rect_zone, zone_unit="cm")
        assert r["zone_type"] == "rectangle"

    def test_description(self, rect_zone):
        r = selected_zone_form(rect_zone, zone_unit="cm")
        assert r["description"] == "Front line"

    def test_editing_state(self, rect_zone):
        r = selected_zone_form(rect_zone, zone_unit="cm")
        assert r["editing_id"] == "z1"
        assert r["add_btn_text"] == "\u270f\ufe0f Update Zone"
        assert r["cancel_btn_visible"] is True

    def test_rect_fields_populated(self, rect_zone):
        r = selected_zone_form(rect_zone, zone_unit="cm")
        assert r["border"] == "south"
        assert r["fill_side"] is False
        assert r["width"] == 100
        assert r["height"] == 20

    def test_non_rect_fields_unchanged(self, rect_zone):
        r = selected_zone_form(rect_zone, zone_unit="cm")
        assert r["triangle_side1"] is UNCHANGED
        assert r["triangle_side2"] is UNCHANGED
        assert r["circle_radius"] is UNCHANGED

    def test_visibility_rect(self, rect_zone):
        r = selected_zone_form(rect_zone, zone_unit="cm")
        assert r["border_row_visible"] is True
        assert r["corner_row_visible"] is False
        assert r["triangle_dimensions_row_visible"] is False
        assert r["circle_dimensions_row_visible"] is False

    def test_unit_conversion(self, rect_zone):
        """Stored in cm, display in in → values converted."""
        r = selected_zone_form(rect_zone, zone_unit="in")
        # 100 cm → 40.0 in (CM_PER_INCH = 2.5), rounded to 2 decimals
        assert r["width"] == 40.0


# ---------------------------------------------------------------------------
# selected_zone_form — triangle
# ---------------------------------------------------------------------------
class TestSelectedZoneFormTriangle:
    """Reconstruct form for a stored triangle zone."""

    @pytest.fixture()
    def tri_zone(self):
        return {
            "id": "z2",
            "form_type": "triangle",
            "data": {"description": "Corner"},
            "form_params": {
                "unit": "cm",
                "corner": "south-east",
                "side1": 25,
                "side2": 25,
                "perfect_triangle": True,
            },
        }

    def test_zone_type(self, tri_zone):
        r = selected_zone_form(tri_zone, zone_unit="cm")
        assert r["zone_type"] == "triangle"

    def test_triangle_fields(self, tri_zone):
        r = selected_zone_form(tri_zone, zone_unit="cm")
        assert r["corner"] == "south-east"
        assert r["perfect_triangle"] is True
        assert r["triangle_side1"] == 25
        assert r["triangle_side2"] == 25

    def test_non_triangle_fields_unchanged(self, tri_zone):
        r = selected_zone_form(tri_zone, zone_unit="cm")
        assert r["border"] is UNCHANGED
        assert r["fill_side"] is UNCHANGED
        assert r["width"] is UNCHANGED
        assert r["circle_radius"] is UNCHANGED

    def test_visibility_triangle(self, tri_zone):
        r = selected_zone_form(tri_zone, zone_unit="cm")
        assert r["border_row_visible"] is False
        assert r["corner_row_visible"] is True
        assert r["perfect_triangle_row_visible"] is True
        assert r["triangle_dimensions_row_visible"] is True


# ---------------------------------------------------------------------------
# selected_zone_form — circle
# ---------------------------------------------------------------------------
class TestSelectedZoneFormCircle:
    """Reconstruct form for a stored circle zone."""

    @pytest.fixture()
    def circle_zone(self):
        return {
            "id": "z3",
            "form_type": "circle",
            "data": {"description": "Arc"},
            "form_params": {
                "unit": "cm",
                "corner": "north-west",
                "radius": 15,
            },
        }

    def test_circle_fields(self, circle_zone):
        r = selected_zone_form(circle_zone, zone_unit="cm")
        assert r["corner"] == "north-west"
        assert r["circle_radius"] == 15

    def test_non_circle_fields_unchanged(self, circle_zone):
        r = selected_zone_form(circle_zone, zone_unit="cm")
        assert r["border"] is UNCHANGED
        assert r["width"] is UNCHANGED
        assert r["triangle_side1"] is UNCHANGED

    def test_visibility_circle(self, circle_zone):
        r = selected_zone_form(circle_zone, zone_unit="cm")
        assert r["circle_dimensions_row_visible"] is True
        assert r["rect_dimensions_row_visible"] is False
        assert r["triangle_dimensions_row_visible"] is False


# ---------------------------------------------------------------------------
# selected_zone_form — no form_params
# ---------------------------------------------------------------------------
class TestSelectedZoneFormNoParams:
    """When form_params is empty, all shape-specific fields are UNCHANGED."""

    def test_all_shape_fields_unchanged(self):
        zone = {
            "id": "z4",
            "form_type": "rectangle",
            "data": {"description": "Legacy"},
        }
        r = selected_zone_form(zone, zone_unit="cm")
        for key in (
            "border",
            "corner",
            "fill_side",
            "perfect_triangle",
            "width",
            "height",
            "sep_x",
            "sep_y",
            "triangle_side1",
            "triangle_side2",
            "circle_radius",
        ):
            assert r[key] is UNCHANGED, f"{key} should be UNCHANGED"


# ---------------------------------------------------------------------------
# UNCHANGED sentinel
# ---------------------------------------------------------------------------
class TestUnchangedSentinel:
    """UNCHANGED is a unique identity sentinel."""

    def test_is_not_none(self):
        assert UNCHANGED is not None

    def test_identity(self):
        assert UNCHANGED is UNCHANGED
