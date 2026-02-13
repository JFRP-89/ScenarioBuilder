"""Tests for _scenography builder — validation + data construction."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._scenography._builder import (
    build_scenography_data,
)


def _base_args(**overrides: object) -> dict:
    """Return minimal valid kwargs for build_scenography_data."""
    defaults = {
        "description": "Element",
        "elem_type": "circle",
        "cx": 50.0,
        "cy": 50.0,
        "r": 15.0,
        "x": 30.0,
        "y": 30.0,
        "width": 40.0,
        "height": 30.0,
        "points_data": [],
        "allow_overlap": False,
        "table_width_val": 120.0,
        "table_height_val": 80.0,
        "table_unit_val": "cm",
        "scenography_unit_val": "cm",
    }
    defaults.update(overrides)
    return defaults


# ── Circle ───────────────────────────────────────────────────────────────────


class TestBuildCircle:
    def test_valid_circle(self):
        result = build_scenography_data(**_base_args())
        assert result["ok"] is True
        assert result["elem_type"] == "circle"
        assert result["data"]["cx"] == 500  # 50cm * 10
        assert result["data"]["cy"] == 500
        assert result["data"]["r"] == 150

    def test_negative_cx_returns_error(self):
        result = build_scenography_data(**_base_args(cx=-1))
        assert result["ok"] is False
        assert "Center X" in result["message"]

    def test_negative_cy_returns_error(self):
        result = build_scenography_data(**_base_args(cy=-1))
        assert result["ok"] is False
        assert "Center Y" in result["message"]

    def test_zero_radius_returns_error(self):
        result = build_scenography_data(**_base_args(r=0))
        assert result["ok"] is False
        assert "Radius" in result["message"]

    def test_negative_radius_returns_error(self):
        result = build_scenography_data(**_base_args(r=-5))
        assert result["ok"] is False
        assert "Radius" in result["message"]

    def test_none_cx_returns_error(self):
        result = build_scenography_data(**_base_args(cx=None))
        assert result["ok"] is False
        assert "Center X" in result["message"]


# ── Rect ─────────────────────────────────────────────────────────────────────


class TestBuildRect:
    def test_valid_rect(self):
        result = build_scenography_data(
            **_base_args(elem_type="rect", x=10, y=10, width=50, height=30)
        )
        assert result["ok"] is True
        assert result["elem_type"] == "rect"
        assert result["data"]["x"] == 100
        assert result["data"]["width"] == 500

    def test_negative_x_returns_error(self):
        result = build_scenography_data(**_base_args(elem_type="rect", x=-1))
        assert result["ok"] is False
        assert "X" in result["message"]

    def test_negative_y_returns_error(self):
        result = build_scenography_data(**_base_args(elem_type="rect", y=-1))
        assert result["ok"] is False
        assert "Y" in result["message"]

    def test_zero_width_returns_error(self):
        result = build_scenography_data(**_base_args(elem_type="rect", width=0))
        assert result["ok"] is False
        assert "Width" in result["message"]

    def test_zero_height_returns_error(self):
        result = build_scenography_data(**_base_args(elem_type="rect", height=0))
        assert result["ok"] is False
        assert "Height" in result["message"]


# ── Polygon ──────────────────────────────────────────────────────────────────


class TestBuildPolygon:
    def test_valid_polygon(self):
        pts = [[10, 20], [30, 40], [50, 60]]
        result = build_scenography_data(
            **_base_args(elem_type="polygon", points_data=pts)
        )
        assert result["ok"] is True
        assert result["elem_type"] == "polygon"
        assert len(result["data"]["points"]) == 3

    def test_too_few_points(self):
        pts = [[10, 20], [30, 40]]
        result = build_scenography_data(
            **_base_args(elem_type="polygon", points_data=pts)
        )
        assert result["ok"] is False
        assert "at least 3" in result["message"]

    def test_none_points(self):
        result = build_scenography_data(
            **_base_args(elem_type="polygon", points_data=None)
        )
        assert result["ok"] is False
        assert "polygon" in result["message"].lower()


# ── Common validation ────────────────────────────────────────────────────────


class TestBuildCommonValidation:
    def test_empty_description(self):
        result = build_scenography_data(**_base_args(description=""))
        assert result["ok"] is False
        assert "Description" in result["message"]

    def test_whitespace_description(self):
        result = build_scenography_data(**_base_args(description="   "))
        assert result["ok"] is False
        assert "Description" in result["message"]

    def test_empty_elem_type(self):
        result = build_scenography_data(**_base_args(elem_type=""))
        assert result["ok"] is False
        assert "Type" in result["message"]

    def test_table_dims_in_result(self):
        result = build_scenography_data(**_base_args())
        assert result["ok"] is True
        assert result["table_w_mm"] == 1200  # 120cm * 10
        assert result["table_h_mm"] == 800

    def test_allow_overlap_passed_through(self):
        result = build_scenography_data(**_base_args(allow_overlap=True))
        assert result["ok"] is True
        assert result["allow_overlap"] is True

    def test_description_stripped(self):
        result = build_scenography_data(**_base_args(description="  Tree  "))
        assert result["ok"] is True
        assert result["description"] == "Tree"


# ── Never-raises fuzz ────────────────────────────────────────────────────────


class TestBuildNeverRaises:
    @pytest.mark.parametrize(
        "overrides",
        [
            {"description": None},
            {"elem_type": None},
            {"cx": None, "cy": None, "r": None},
            {"points_data": None, "elem_type": "polygon"},
            {"description": "", "elem_type": ""},
        ],
    )
    def test_no_exception(self, overrides):
        result = build_scenography_data(**_base_args(**overrides))
        assert isinstance(result, dict)
        assert "ok" in result
