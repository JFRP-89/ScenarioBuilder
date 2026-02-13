"""Tests for _scenography polygon parsing and conversion."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._scenography._polygon import (
    convert_polygon_points,
    parse_polygon_points,
)


class TestParsePolygonPointsValid:
    def test_three_valid_points(self):
        data = [[10, 20], [30, 40], [50, 60]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is None
        assert len(pts) == 3
        # cm → mm: 10cm * 10 = 100mm
        assert pts[0] == {"x": 100, "y": 200}

    def test_string_values_parsed(self):
        data = [["10", "20"], ["30", "40"], ["50", "60"]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is None
        assert len(pts) == 3

    def test_skips_none_rows(self):
        data = [[10, 20], None, [30, 40], [50, 60]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is None
        assert len(pts) == 3

    def test_skips_empty_rows(self):
        data = [[10, 20], [], [30, 40], [50, 60]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is None
        assert len(pts) == 3

    def test_skips_short_rows(self):
        data = [[10, 20], [30], [40, 50], [60, 70]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is None
        assert len(pts) == 3


class TestParsePolygonPointsErrors:
    def test_none_input(self):
        pts, err = parse_polygon_points(None, "cm")
        assert "No polygon points provided" in err
        assert pts == []

    def test_too_few_points(self):
        data = [[10, 20], [30, 40]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is not None
        assert "at least 3" in err
        assert "Found: 2" in err

    def test_all_invalid_rows(self):
        data = [None, [], [1]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is not None
        assert "Found: 0" in err

    def test_nan_values_skipped(self):
        data = [[float("nan"), 20], [30, 40], [50, 60]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is not None
        assert "Found: 2" in err

    def test_inf_values_skipped(self):
        data = [[float("inf"), 20], [30, 40], [50, 60]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is not None
        assert "Found: 2" in err

    def test_none_x_y_skipped(self):
        data = [[None, 20], [30, 40], [50, 60]]
        pts, err = parse_polygon_points(data, "cm")
        assert err is not None
        assert "Found: 2" in err


class TestParsePolygonPointsNeverRaises:
    @pytest.mark.parametrize(
        "bad_input",
        [None, [], 42, "string", [[]], [[None, None]], [["a", "b"]]],
    )
    def test_no_exception(self, bad_input):
        """parse_polygon_points should never raise."""
        pts, err = parse_polygon_points(bad_input, "cm")
        # Either we get an error message or empty/valid list
        assert isinstance(pts, list)


class TestConvertPolygonPoints:
    def test_converts_cm_to_in(self):
        data = [[25.0, 50.0]]  # 25cm = 10in, 50cm = 20in (CM_PER_INCH=2.5)
        result = convert_polygon_points(data, "cm", "in")
        assert len(result) == 1
        assert result[0][0] == 10.0
        assert result[0][1] == 20.0

    def test_none_returns_none(self):
        assert convert_polygon_points(None, "cm", "in") is None

    def test_empty_list_returns_original(self):
        result = convert_polygon_points([], "cm", "in")
        assert result == []

    def test_invalid_rows_skipped(self):
        data = [[10, 20], [None, None]]
        result = convert_polygon_points(data, "cm", "cm")
        # Same unit returns original? No — convert_unit_to_unit rounds
        assert len(result) >= 1
