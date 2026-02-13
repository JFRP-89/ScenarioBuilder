"""Tests for _scenography form state management."""

from __future__ import annotations

from adapters.ui_gradio.ui.wiring._scenography._form_state import (
    CIRCLE_DEFAULTS,
    RECT_DEFAULTS,
    UNCHANGED,
    default_scenography_form,
    selected_scenography_form,
)


class TestDefaultScenographyForm:
    def test_returns_circle_type(self):
        form = default_scenography_form()
        assert form["type"] == "circle"

    def test_circle_defaults(self):
        form = default_scenography_form()
        assert form["cx"] == CIRCLE_DEFAULTS["cx"]
        assert form["cy"] == CIRCLE_DEFAULTS["cy"]
        assert form["r"] == CIRCLE_DEFAULTS["r"]

    def test_rect_defaults(self):
        form = default_scenography_form()
        assert form["x"] == RECT_DEFAULTS["x"]
        assert form["y"] == RECT_DEFAULTS["y"]
        assert form["width"] == RECT_DEFAULTS["width"]
        assert form["height"] == RECT_DEFAULTS["height"]

    def test_polygon_points_unchanged(self):
        form = default_scenography_form()
        assert form["polygon_points"] is UNCHANGED

    def test_description_empty(self):
        form = default_scenography_form()
        assert form["description"] == ""

    def test_allow_overlap_false(self):
        form = default_scenography_form()
        assert form["allow_overlap"] is False

    def test_editing_id_none(self):
        form = default_scenography_form()
        assert form["editing_id"] is None


class TestSelectedScenographyFormCircle:
    def test_circle_populates_coords(self):
        elem = {
            "id": "el-1",
            "type": "circle",
            "allow_overlap": True,
            "data": {
                "description": "Tree",
                "cx": 500,  # 50cm in mm
                "cy": 300,  # 30cm
                "r": 100,  # 10cm
            },
        }
        form = selected_scenography_form(elem, "cm")
        assert form["type"] == "circle"
        assert form["description"] == "Tree"
        assert form["allow_overlap"] is True
        assert form["editing_id"] == "el-1"
        assert form["cx"] == 50.0
        assert form["cy"] == 30.0
        assert form["r"] == 10.0

    def test_circle_leaves_rect_unchanged(self):
        elem = {
            "id": "el-1",
            "type": "circle",
            "data": {"cx": 100, "cy": 100, "r": 50},
        }
        form = selected_scenography_form(elem, "cm")
        assert form["x"] is UNCHANGED
        assert form["y"] is UNCHANGED
        assert form["width"] is UNCHANGED
        assert form["height"] is UNCHANGED
        assert form["polygon_points"] is UNCHANGED


class TestSelectedScenographyFormRect:
    def test_rect_populates_dims(self):
        elem = {
            "id": "el-2",
            "type": "rect",
            "data": {
                "description": "Wall",
                "x": 200,
                "y": 100,
                "width": 400,
                "height": 50,
            },
        }
        form = selected_scenography_form(elem, "cm")
        assert form["type"] == "rect"
        assert form["x"] == 20.0
        assert form["y"] == 10.0
        assert form["width"] == 40.0
        assert form["height"] == 5.0

    def test_rect_leaves_circle_unchanged(self):
        elem = {
            "id": "el-2",
            "type": "rect",
            "data": {"x": 0, "y": 0, "width": 100, "height": 100},
        }
        form = selected_scenography_form(elem, "cm")
        assert form["cx"] is UNCHANGED
        assert form["cy"] is UNCHANGED
        assert form["r"] is UNCHANGED


class TestSelectedScenographyFormPolygon:
    def test_polygon_builds_points_display(self):
        elem = {
            "id": "el-3",
            "type": "polygon",
            "data": {
                "description": "Area",
                "points": [
                    {"x": 100, "y": 200},
                    {"x": 300, "y": 400},
                    {"x": 500, "y": 600},
                ],
            },
        }
        form = selected_scenography_form(elem, "cm")
        assert form["type"] == "polygon"
        pts = form["polygon_points"]
        assert len(pts) == 3
        assert pts[0] == [10.0, 20.0]
        assert pts[1] == [30.0, 40.0]
        assert pts[2] == [50.0, 60.0]

    def test_polygon_with_list_points(self):
        elem = {
            "id": "el-4",
            "type": "polygon",
            "data": {
                "points": [[100, 200], [300, 400], [500, 600]],
            },
        }
        form = selected_scenography_form(elem, "cm")
        pts = form["polygon_points"]
        assert len(pts) == 3
        assert pts[0] == [10.0, 20.0]

    def test_polygon_leaves_circle_rect_unchanged(self):
        elem = {
            "id": "el-5",
            "type": "polygon",
            "data": {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}, {"x": 2, "y": 2}]},
        }
        form = selected_scenography_form(elem, "cm")
        assert form["cx"] is UNCHANGED
        assert form["x"] is UNCHANGED


class TestSelectedScenographyFormUnitConversion:
    def test_circle_units_in(self):
        """Values stored in mm \u2192 cm \u2192 inches (CM_PER_INCH=2.5)."""
        elem = {
            "id": "el-6",
            "type": "circle",
            "data": {"cx": 250, "cy": 250, "r": 250},  # 25cm = 10in
        }
        form = selected_scenography_form(elem, "in")
        assert form["cx"] == 10.0
        assert form["cy"] == 10.0
        assert form["r"] == 10.0
