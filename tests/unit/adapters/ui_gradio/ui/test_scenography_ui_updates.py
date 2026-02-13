"""Tests for _scenography UI updates — visibility + coordinate conversion."""

from __future__ import annotations

from adapters.ui_gradio.ui.wiring._scenography._ui_updates import (
    convert_scenography_coordinates,
    scenography_type_visibility,
)


class TestScenographyTypeVisibility:
    def test_circle(self):
        vis = scenography_type_visibility("circle")
        assert vis == {"circle": True, "rect": False, "polygon": False}

    def test_rect(self):
        vis = scenography_type_visibility("rect")
        assert vis == {"circle": False, "rect": True, "polygon": False}

    def test_polygon(self):
        vis = scenography_type_visibility("polygon")
        assert vis == {"circle": False, "rect": False, "polygon": True}

    def test_unknown_type(self):
        vis = scenography_type_visibility("unknown")
        assert vis == {"circle": False, "rect": False, "polygon": False}


class TestConvertScenographyCoordinates:
    def test_same_unit_noop(self):
        result = convert_scenography_coordinates(
            10, 20, 5, 30, 40, 50, 60, [[1, 2]], "cm", "cm"
        )
        assert result == (10, 20, 5, 30, 40, 50, 60, [[1, 2]], "cm")

    def test_cm_to_in(self):
        # 25cm = 10in (CM_PER_INCH=2.5)
        result = convert_scenography_coordinates(
            25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, None, "cm", "in"
        )
        assert result[0] == 10.0
        assert result[1] == 10.0
        assert result[-1] == "in"

    def test_returns_new_unit_in_last_position(self):
        result = convert_scenography_coordinates(1, 2, 3, 4, 5, 6, 7, None, "cm", "in")
        assert result[-1] == "in"

    def test_polygon_data_converted(self):
        poly = [[25.0, 50.0], [75.0, 100.0]]  # cm values (CM_PER_INCH=2.5)
        result = convert_scenography_coordinates(0, 0, 0, 0, 0, 0, 0, poly, "cm", "in")
        converted_poly = result[7]
        assert len(converted_poly) == 2
        assert converted_poly[0][0] == 10.0
        assert converted_poly[0][1] == 20.0

    def test_polygon_none_preserved(self):
        result = convert_scenography_coordinates(0, 0, 0, 0, 0, 0, 0, None, "cm", "in")
        assert result[7] is None
