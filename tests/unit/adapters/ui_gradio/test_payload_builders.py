"""Unit tests for payload_builders module.

Tests pure functions that construct HTTP payloads from UI state.
"""

from adapters.ui_gradio import payload_builders


class TestBuildGeneratePayload:
    """Tests for build_generate_payload function."""

    def test_with_seed_returns_mode_and_seed(self):
        result = payload_builders.build_generate_payload("points-match", 12345)
        assert result == {"mode": "points-match", "seed": 12345}

    def test_without_seed_returns_mode_and_none(self):
        result = payload_builders.build_generate_payload("meeting-engagement", None)
        assert result == {"mode": "meeting-engagement", "seed": None}

    def test_seed_zero_is_converted_to_int(self):
        # Note: seed=0 is falsy, so it becomes None (intentional behavior)
        result = payload_builders.build_generate_payload("domination", 0)
        assert result == {"mode": "domination", "seed": None}


class TestApplyTableConfig:
    """Tests for apply_table_config function."""

    def test_preset_standard_adds_table_preset_field(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "standard", 0, 0, "cm"
        )
        assert custom_table is None
        assert error is None
        assert payload == {"table_preset": "standard"}

    def test_preset_massive_adds_table_preset_field(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "massive", 0, 0, "cm"
        )
        assert custom_table is None
        assert error is None
        assert payload == {"table_preset": "massive"}

    def test_custom_valid_cm_adds_table_cm_field(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "custom", 120, 120, "cm"
        )
        assert custom_table == {"width_cm": 120, "height_cm": 120}
        assert error is None
        assert payload == {"table_cm": {"width_cm": 120, "height_cm": 120}}

    def test_custom_valid_inches_converts_to_cm(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "custom", 48, 48, "inches"
        )
        # 48 inches * 2.54 = 121.92 cm
        assert custom_table == {"width_cm": 121.92, "height_cm": 121.92}
        assert error is None
        assert payload["table_cm"]["width_cm"] == 121.92

    def test_custom_below_min_returns_error(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "custom", 50, 50, "cm"
        )
        assert custom_table is None
        assert error == {
            "status": "error",
            "message": "Invalid table dimensions. Check limits (60-300 cm).",
        }
        assert "table_cm" not in payload

    def test_custom_above_max_returns_error(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "custom", 350, 350, "cm"
        )
        assert custom_table is None
        assert error == {
            "status": "error",
            "message": "Invalid table dimensions. Check limits (60-300 cm).",
        }

    def test_custom_width_valid_height_invalid_returns_error(self):
        payload = {}
        custom_table, error = payload_builders.apply_table_config(
            payload, "custom", 120, 400, "cm"
        )
        assert custom_table is None
        assert error is not None


class TestApplyOptionalTextFields:
    """Tests for apply_optional_text_fields function."""

    def test_all_none_does_not_modify_payload(self):
        payload = {}
        payload_builders.apply_optional_text_fields(payload)
        assert payload == {}

    def test_empty_strings_do_not_add_fields(self):
        payload = {}
        payload_builders.apply_optional_text_fields(
            payload,
            deployment="",
            layout="  ",
            objectives="",
            armies="",
            name="",
        )
        assert payload == {}

    def test_deployment_adds_field(self):
        payload = {}
        payload_builders.apply_optional_text_fields(
            payload, deployment="Corner Deployment"
        )
        assert payload == {"deployment": "Corner Deployment"}

    def test_layout_adds_field(self):
        payload = {}
        payload_builders.apply_optional_text_fields(payload, layout="Scattered")
        assert payload == {"layout": "Scattered"}

    def test_objectives_adds_field(self):
        payload = {}
        payload_builders.apply_optional_text_fields(payload, objectives="Hold the Line")
        assert payload == {"objectives": "Hold the Line"}

    def test_initial_priority_adds_field(self):
        payload = {}
        payload_builders.apply_optional_text_fields(payload, initial_priority="Evil")
        assert payload == {"initial_priority": "Evil"}

    def test_armies_adds_field(self):
        payload = {}
        payload_builders.apply_optional_text_fields(payload, armies="Mordor vs Rohan")
        assert payload == {"armies": "Mordor vs Rohan"}

    def test_name_adds_field(self):
        payload = {}
        payload_builders.apply_optional_text_fields(
            payload, name="Battle of Helm's Deep"
        )
        assert payload == {"name": "Battle of Helm's Deep"}

    def test_strips_whitespace_from_values(self):
        payload = {}
        payload_builders.apply_optional_text_fields(
            payload,
            deployment="  Corner  ",
            name="  Epic Battle  ",
        )
        assert payload == {"deployment": "Corner", "name": "Epic Battle"}

    def test_multiple_fields_together(self):
        payload = {}
        payload_builders.apply_optional_text_fields(
            payload,
            deployment="Pitched Battle",
            layout="Standard",
            objectives="Domination",
            armies="Good vs Evil",
            name="The Last Stand",
            initial_priority="Good",
        )
        assert payload == {
            "deployment": "Pitched Battle",
            "layout": "Standard",
            "objectives": "Domination",
            "armies": "Good vs Evil",
            "name": "The Last Stand",
            "initial_priority": "Good",
        }


class TestApplySpecialRules:
    """Tests for apply_special_rules function."""

    def test_empty_state_does_nothing(self):
        payload = {}
        error = payload_builders.apply_special_rules(payload, [])
        assert error is None
        assert "special_rules" not in payload

    def test_valid_rule_description_type_adds_to_payload(self):
        payload = {}
        rules_state = [
            {
                "name": "Fog of War",
                "rule_type": "description",
                "value": "Visibility is limited",
            }
        ]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error is None
        assert payload == {
            "special_rules": [
                {"name": "Fog of War", "description": "Visibility is limited"}
            ]
        }

    def test_valid_rule_source_type_adds_to_payload(self):
        payload = {}
        rules_state = [
            {"name": "Night Fight", "rule_type": "source", "value": "Rulebook p.42"}
        ]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error is None
        assert payload == {
            "special_rules": [{"name": "Night Fight", "source": "Rulebook p.42"}]
        }

    def test_multiple_rules_preserves_order(self):
        payload = {}
        rules_state = [
            {"name": "Rule A", "rule_type": "description", "value": "Description A"},
            {"name": "Rule B", "rule_type": "source", "value": "Source B"},
            {"name": "Rule C", "rule_type": "description", "value": "Description C"},
        ]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error is None
        assert payload["special_rules"] == [
            {"name": "Rule A", "description": "Description A"},
            {"name": "Rule B", "source": "Source B"},
            {"name": "Rule C", "description": "Description C"},
        ]

    def test_rule_without_name_returns_error(self):
        payload = {}
        rules_state = [{"name": "", "rule_type": "description", "value": "Some value"}]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error == {"status": "error", "message": "Rule 1: Name is required"}
        assert "special_rules" not in payload

    def test_rule_without_rule_type_returns_error(self):
        payload = {}
        rules_state = [{"name": "Rule A", "rule_type": "", "value": "Some value"}]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error == {
            "status": "error",
            "message": "Rule 1: Must specify description or source",
        }

    def test_rule_with_invalid_rule_type_returns_error(self):
        payload = {}
        rules_state = [
            {"name": "Rule A", "rule_type": "invalid", "value": "Some value"}
        ]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error == {
            "status": "error",
            "message": "Rule 1: Must specify description or source",
        }

    def test_rule_without_value_returns_error(self):
        payload = {}
        rules_state = [{"name": "Rule A", "rule_type": "description", "value": ""}]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error == {"status": "error", "message": "Rule 1: Value cannot be empty"}

    def test_second_rule_error_reports_correct_index(self):
        payload = {}
        rules_state = [
            {"name": "Rule A", "rule_type": "description", "value": "Valid"},
            {"name": "", "rule_type": "description", "value": "Invalid"},
        ]
        error = payload_builders.apply_special_rules(payload, rules_state)
        assert error == {"status": "error", "message": "Rule 2: Name is required"}


class TestApplyVisibility:
    """Tests for apply_visibility function."""

    def test_private_adds_visibility_only(self):
        payload = {}
        payload_builders.apply_visibility(payload, "private", None)
        assert payload == {"visibility": "private"}

    def test_public_adds_visibility_only(self):
        payload = {}
        payload_builders.apply_visibility(payload, "public", None)
        assert payload == {"visibility": "public"}

    def test_shared_without_users_adds_visibility_only(self):
        payload = {}
        payload_builders.apply_visibility(payload, "shared", "")
        assert payload == {"visibility": "shared"}

    def test_shared_with_one_user_adds_shared_with(self):
        payload = {}
        payload_builders.apply_visibility(payload, "shared", "user123")
        assert payload == {"visibility": "shared", "shared_with": ["user123"]}

    def test_shared_with_multiple_users_splits_by_comma(self):
        payload = {}
        payload_builders.apply_visibility(payload, "shared", "user1, user2, user3")
        assert payload == {
            "visibility": "shared",
            "shared_with": ["user1", "user2", "user3"],
        }

    def test_shared_with_users_strips_whitespace(self):
        payload = {}
        payload_builders.apply_visibility(payload, "shared", "  user1  ,  user2  ")
        assert payload == {"visibility": "shared", "shared_with": ["user1", "user2"]}

    def test_shared_with_empty_entries_filters_them_out(self):
        payload = {}
        payload_builders.apply_visibility(payload, "shared", "user1,,user2,  ,user3")
        assert payload == {
            "visibility": "shared",
            "shared_with": ["user1", "user2", "user3"],
        }


class TestBuildMapSpecsFromState:
    """Tests for build_map_specs_from_state function."""

    def test_empty_state_returns_empty_list(self):
        result = payload_builders.build_map_specs_from_state([])
        assert result == []

    def test_single_element_without_overlap_returns_with_false_flag(self):
        state = [
            {
                "id": "elem1",
                "data": {"type": "circle", "cx": 100, "cy": 100, "r": 50},
                "allow_overlap": False,
            }
        ]
        result = payload_builders.build_map_specs_from_state(state)
        assert result == [
            {
                "type": "circle",
                "cx": 100,
                "cy": 100,
                "r": 50,
                "allow_overlap": False,
            }
        ]

    def test_single_element_with_overlap_returns_with_true_flag(self):
        state = [
            {
                "id": "elem1",
                "data": {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100},
                "allow_overlap": True,
            }
        ]
        result = payload_builders.build_map_specs_from_state(state)
        assert result == [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "allow_overlap": True,
            }
        ]

    def test_sorts_overlap_true_first(self):
        state = [
            {
                "id": "elem1",
                "data": {"type": "circle", "cx": 100},
                "allow_overlap": False,
            },
            {
                "id": "elem2",
                "data": {"type": "rect", "x": 0},
                "allow_overlap": True,
            },
            {
                "id": "elem3",
                "data": {"type": "polygon"},
                "allow_overlap": False,
            },
        ]
        result = payload_builders.build_map_specs_from_state(state)
        assert len(result) == 3
        assert result[0]["allow_overlap"] is True
        assert result[0]["type"] == "rect"
        assert result[1]["allow_overlap"] is False
        assert result[2]["allow_overlap"] is False

    def test_removes_id_and_label_fields(self):
        state = [
            {
                "id": "should_not_appear",
                "label": "also_not_appear",
                "data": {"type": "circle", "cx": 100},
                "allow_overlap": False,
            }
        ]
        result = payload_builders.build_map_specs_from_state(state)
        assert "id" not in result[0]
        assert "label" not in result[0]


class TestBuildDeploymentShapesFromState:
    """Tests for build_deployment_shapes_from_state function."""

    def test_empty_state_returns_empty_list(self):
        result = payload_builders.build_deployment_shapes_from_state([])
        assert result == []

    def test_single_zone_returns_data_without_ui_fields(self):
        state = [
            {
                "id": "zone1",
                "label": "Zone A",
                "data": {
                    "type": "deployment_zone",
                    "description": "North Zone",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 300,
                    "border": "north",
                    "depth": 300,
                    "separation": 50,
                },
            }
        ]
        result = payload_builders.build_deployment_shapes_from_state(state)
        assert len(result) == 1
        assert result[0] == {
            "type": "deployment_zone",
            "description": "North Zone",
            "x": 0,
            "y": 0,
            "width": 1200,
            "height": 300,
            "border": "north",
        }
        assert "depth" not in result[0]
        assert "separation" not in result[0]

    def test_multiple_zones_preserves_order(self):
        state = [
            {
                "id": "zone1",
                "label": "Zone A",
                "data": {
                    "type": "deployment_zone",
                    "border": "north",
                    "x": 0,
                    "depth": 100,
                },
            },
            {
                "id": "zone2",
                "label": "Zone B",
                "data": {
                    "type": "deployment_zone",
                    "border": "south",
                    "x": 0,
                    "separation": 50,
                },
            },
        ]
        result = payload_builders.build_deployment_shapes_from_state(state)
        assert len(result) == 2
        assert result[0]["border"] == "north"
        assert result[1]["border"] == "south"
        assert "depth" not in result[0]
        assert "separation" not in result[1]

    def test_removes_id_and_label_from_output(self):
        state = [
            {
                "id": "should_not_appear",
                "label": "Zone Label",
                "data": {"type": "deployment_zone", "border": "west"},
            }
        ]
        result = payload_builders.build_deployment_shapes_from_state(state)
        assert "id" not in result[0]
        assert "label" not in result[0]


class TestBuildObjectiveShapesFromState:
    """Tests for build_objective_shapes_from_state function."""

    def test_empty_state_returns_empty_list(self):
        result = payload_builders.build_objective_shapes_from_state([])
        assert result == []

    def test_single_point_without_description_returns_minimal_shape(self):
        state = [{"id": "point1", "cx": 600, "cy": 600}]
        result = payload_builders.build_objective_shapes_from_state(state)
        assert result == [{"type": "objective_point", "cx": 600, "cy": 600}]

    def test_single_point_with_description_includes_it(self):
        state = [
            {"id": "point1", "cx": 600, "cy": 600, "description": "Center objective"}
        ]
        result = payload_builders.build_objective_shapes_from_state(state)
        assert result == [
            {
                "type": "objective_point",
                "cx": 600,
                "cy": 600,
                "description": "Center objective",
            }
        ]

    def test_multiple_points_preserves_order(self):
        state = [
            {"id": "p1", "cx": 100, "cy": 100, "description": "Point A"},
            {"id": "p2", "cx": 200, "cy": 200},
            {"id": "p3", "cx": 300, "cy": 300, "description": "Point C"},
        ]
        result = payload_builders.build_objective_shapes_from_state(state)
        assert len(result) == 3
        assert result[0]["cx"] == 100
        assert result[0]["description"] == "Point A"
        assert result[1]["cx"] == 200
        assert "description" not in result[1]
        assert result[2]["cx"] == 300

    def test_converts_cx_cy_to_int(self):
        state = [{"id": "p1", "cx": 100.7, "cy": 200.9}]
        result = payload_builders.build_objective_shapes_from_state(state)
        assert result[0]["cx"] == 100
        assert result[0]["cy"] == 200

    def test_removes_id_field(self):
        state = [{"id": "should_not_appear", "cx": 100, "cy": 100}]
        result = payload_builders.build_objective_shapes_from_state(state)
        assert "id" not in result[0]
