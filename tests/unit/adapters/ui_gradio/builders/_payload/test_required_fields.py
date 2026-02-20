"""Tests for _payload._required_fields — full form validation."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.builders._payload._required_fields import (
    ValidationInput,
    validate_required_fields,
)


def _valid_input(**overrides) -> ValidationInput:
    """Return a *ValidationInput* with minimal valid defaults, overriding with *overrides*."""
    defaults = {
        "actor": "actor-1",
        "name": "Scenario",
        "mode": "matched",
        "armies": "Good vs Evil",
        "preset": "standard",
        "width": 120.0,
        "height": 120.0,
        "unit": "cm",
        "deployment": "Deployment A",
        "layout": "Layout B",
        "objectives": "Objectives C",
        "initial_priority": "Priority D",
        "rules_state": [],
        "vp_state": [],
        "deployment_zones": [],
        "objective_points": [],
        "scenography": [],
        "default_actor_id": "default-actor",
    }
    defaults.update(overrides)
    return ValidationInput(**defaults)


class TestAllFieldsValid:
    def test_returns_none(self):
        assert validate_required_fields(_valid_input()) is None


class TestMissingBasicFields:
    @pytest.mark.parametrize(
        "field,label",
        [
            ("name", "Scenario Name"),
            ("mode", "Game Mode"),
            ("armies", "Armies"),
            ("preset", "Table Preset"),
            ("deployment", "Deployment"),
            ("layout", "Layout"),
            ("objectives", "Objectives"),
            ("initial_priority", "Initial Priority"),
        ],
    )
    def test_missing_field_reports_error(self, field, label):
        result = validate_required_fields(_valid_input(**{field: ""}))
        assert result is not None
        assert label in result


class TestActorFallback:
    def test_empty_actor_uses_default(self):
        assert (
            validate_required_fields(
                _valid_input(actor="", default_actor_id="fallback")
            )
            is None
        )

    def test_both_empty_reports_error(self):
        result = validate_required_fields(_valid_input(actor="", default_actor_id=""))
        assert "Actor ID" in result


class TestCustomTableDimensions:
    def test_zero_dimensions_reports_error(self):
        result = validate_required_fields(
            _valid_input(preset="custom", width=0, height=0)
        )
        assert "Table dimensions" in result

    def test_out_of_range_reports_error(self):
        result = validate_required_fields(
            _valid_input(preset="custom", width=10, height=10)
        )
        assert "Table dimensions" in result

    def test_valid_custom_passes(self):
        assert (
            validate_required_fields(
                _valid_input(preset="custom", width=120, height=120)
            )
            is None
        )


class TestSpecialRulesValidation:
    def test_empty_rule_name_reports_error(self):
        result = validate_required_fields(
            _valid_input(rules_state=[{"name": "", "value": ""}])
        )
        assert "Special Rule #1" in result


class TestVPValidation:
    def test_empty_vp_desc_reports_error(self):
        result = validate_required_fields(_valid_input(vp_state=[{"description": ""}]))
        assert "Victory Point #1" in result


class TestDeploymentZonesValidation:
    def test_rect_zone_missing_border(self):
        result = validate_required_fields(
            _valid_input(
                deployment_zones=[
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
                ],
            )
        )
        assert "Border" in result

    def test_polygon_zone_missing_points(self):
        result = validate_required_fields(
            _valid_input(
                deployment_zones=[
                    {
                        "label": "Tri",
                        "data": {"type": "polygon", "points": [], "corner": "NW"},
                    }
                ],
            )
        )
        assert "Points" in result


class TestObjectivePointsValidation:
    def test_missing_description(self):
        result = validate_required_fields(
            _valid_input(
                objective_points=[{"description": "", "cx": 10, "cy": 20}],
            )
        )
        assert "Objective Point #1" in result


class TestScenographyValidation:
    def test_circle_missing_radius(self):
        result = validate_required_fields(
            _valid_input(
                scenography=[
                    {
                        "label": "Tree",
                        "type": "circle",
                        "data": {"cx": 10, "cy": 10, "r": 0},
                    }
                ],
            )
        )
        assert "Radius" in result

    def test_rect_missing_width(self):
        result = validate_required_fields(
            _valid_input(
                scenography=[
                    {
                        "label": "Wall",
                        "type": "rect",
                        "data": {"x": 0, "y": 0, "width": 0, "height": 10},
                    }
                ],
            )
        )
        assert "Width" in result

    def test_polygon_too_few_points(self):
        result = validate_required_fields(
            _valid_input(
                scenography=[
                    {
                        "label": "Poly",
                        "type": "polygon",
                        "data": {"points": [(0, 0), (1, 1)]},
                    }
                ],
            )
        )
        assert "3 points" in result
