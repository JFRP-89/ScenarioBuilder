"""Tests for _payload._required_fields — full form validation."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.builders._payload._required_fields import (
    validate_required_fields,
)


def _valid_args() -> dict:
    """Return minimal valid kwargs for validate_required_fields."""
    return {
        "actor": "actor-1",
        "name": "Scenario",
        "m": "matched",
        "armies_val": "Good vs Evil",
        "preset": "standard",
        "width": 120.0,
        "height": 120.0,
        "unit": "cm",
        "depl": "Deployment A",
        "lay": "Layout B",
        "obj": "Objectives C",
        "init_priority": "Priority D",
        "rules_state": [],
        "vp_state": [],
        "deployment_zones_state_val": [],
        "objective_points_state_val": [],
        "scenography_state_val": [],
        "default_actor_id": "default-actor",
    }


class TestAllFieldsValid:
    def test_returns_none(self):
        assert validate_required_fields(**_valid_args()) is None


class TestMissingBasicFields:
    @pytest.mark.parametrize(
        "field,label",
        [
            ("name", "Scenario Name"),
            ("m", "Game Mode"),
            ("armies_val", "Armies"),
            ("preset", "Table Preset"),
            ("depl", "Deployment"),
            ("lay", "Layout"),
            ("obj", "Objectives"),
            ("init_priority", "Initial Priority"),
        ],
    )
    def test_missing_field_reports_error(self, field, label):
        args = _valid_args()
        args[field] = ""
        result = validate_required_fields(**args)
        assert result is not None
        assert label in result


class TestActorFallback:
    def test_empty_actor_uses_default(self):
        args = _valid_args()
        args["actor"] = ""
        args["default_actor_id"] = "fallback"
        assert validate_required_fields(**args) is None

    def test_both_empty_reports_error(self):
        args = _valid_args()
        args["actor"] = ""
        args["default_actor_id"] = ""
        result = validate_required_fields(**args)
        assert "Actor ID" in result


class TestCustomTableDimensions:
    def test_zero_dimensions_reports_error(self):
        args = _valid_args()
        args["preset"] = "custom"
        args["width"] = 0
        args["height"] = 0
        result = validate_required_fields(**args)
        assert "Table dimensions" in result

    def test_out_of_range_reports_error(self):
        args = _valid_args()
        args["preset"] = "custom"
        args["width"] = 10
        args["height"] = 10
        result = validate_required_fields(**args)
        assert "Table dimensions" in result

    def test_valid_custom_passes(self):
        args = _valid_args()
        args["preset"] = "custom"
        args["width"] = 120
        args["height"] = 120
        assert validate_required_fields(**args) is None


class TestSpecialRulesValidation:
    def test_empty_rule_name_reports_error(self):
        args = _valid_args()
        args["rules_state"] = [{"name": "", "value": ""}]
        result = validate_required_fields(**args)
        assert "Special Rule #1" in result


class TestVPValidation:
    def test_empty_vp_desc_reports_error(self):
        args = _valid_args()
        args["vp_state"] = [{"description": ""}]
        result = validate_required_fields(**args)
        assert "Victory Point #1" in result


class TestDeploymentZonesValidation:
    def test_rect_zone_missing_border(self):
        args = _valid_args()
        args["deployment_zones_state_val"] = [
            {
                "label": "Zone1",
                "data": {
                    "type": "rect",
                    "border": "",
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 100,
                },
            }
        ]
        result = validate_required_fields(**args)
        assert "Border" in result

    def test_polygon_zone_missing_points(self):
        args = _valid_args()
        args["deployment_zones_state_val"] = [
            {
                "label": "Tri",
                "data": {"type": "polygon", "points": [], "corner": "NW"},
            }
        ]
        result = validate_required_fields(**args)
        assert "Points" in result


class TestObjectivePointsValidation:
    def test_missing_description(self):
        args = _valid_args()
        args["objective_points_state_val"] = [{"description": "", "cx": 10, "cy": 20}]
        result = validate_required_fields(**args)
        assert "Objective Point #1" in result


class TestScenographyValidation:
    def test_circle_missing_radius(self):
        args = _valid_args()
        args["scenography_state_val"] = [
            {
                "label": "Tree",
                "type": "circle",
                "data": {"cx": 10, "cy": 10, "r": 0},
            }
        ]
        result = validate_required_fields(**args)
        assert "Radius" in result

    def test_rect_missing_width(self):
        args = _valid_args()
        args["scenography_state_val"] = [
            {
                "label": "Wall",
                "type": "rect",
                "data": {"x": 0, "y": 0, "width": 0, "height": 10},
            }
        ]
        result = validate_required_fields(**args)
        assert "Width" in result

    def test_polygon_too_few_points(self):
        args = _valid_args()
        args["scenography_state_val"] = [
            {
                "label": "Poly",
                "type": "polygon",
                "data": {"points": [(0, 0), (1, 1)]},
            }
        ]
        result = validate_required_fields(**args)
        assert "3 points" in result
