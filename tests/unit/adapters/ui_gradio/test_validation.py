"""
Unit tests for Gradio UI validation functions.

Tests for _validate_required_fields to ensure all mandatory fields are checked
and appropriate error messages are generated.
"""

from __future__ import annotations


class TestValidateRequiredFields:
    """Test suite for _validate_required_fields function."""

    def test_all_mandatory_fields_valid_returns_none(self):
        """When all mandatory fields are valid, returns None."""
        # Import the function dynamically to avoid circular imports
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is None

    def test_missing_scenario_name_returns_error(self):
        """When Scenario Name is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="",  # Missing
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Scenario Name" in result

    def test_missing_game_mode_returns_error(self):
        """When Game Mode is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="",  # Missing
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Game Mode" in result

    def test_missing_armies_returns_error(self):
        """When Armies is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="",  # Missing
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Armies" in result

    def test_missing_deployment_returns_error(self):
        """When Deployment is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="",  # Missing
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Deployment" in result

    def test_missing_layout_returns_error(self):
        """When Layout is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="",  # Missing
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Layout" in result

    def test_missing_objectives_returns_error(self):
        """When Objectives is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="",  # Missing
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Objectives" in result

    def test_missing_initial_priority_returns_error(self):
        """When Initial Priority is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="",  # Missing
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Initial Priority" in result

    def test_special_rule_missing_name_returns_error(self):
        """When Special Rule name is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[
                {
                    "id": "r1",
                    "name": "",
                    "rule_type": "description",
                    "value": "Some value",
                }
            ],  # Missing name
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Special Rule #1" in result
        assert "Name and Value" in result

    def test_special_rule_missing_value_returns_error(self):
        """When Special Rule value is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[
                {
                    "id": "r1",
                    "name": "Rule Name",
                    "rule_type": "description",
                    "value": "",
                }
            ],  # Missing value
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Special Rule #1" in result
        assert "Name and Value" in result

    def test_victory_point_missing_description_returns_error(self):
        """When Victory Point description is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[{"id": "vp1", "description": ""}],  # Missing description
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Victory Point #1" in result
        assert "Description" in result

    def test_deployment_zone_missing_description_returns_error(self):
        """When Deployment Zone description is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[
                {
                    "id": "z1",
                    "label": "",  # Missing description
                    "data": {
                        "border": "north",
                        "width": 200,
                        "height": 100,
                        "sep_x": 50,
                        "sep_y": 50,
                    },
                }
            ],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Deployment Zone #1" in result
        assert "Description" in result

    def test_deployment_zone_missing_width_returns_error(self):
        """When Deployment Zone width is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[
                {
                    "id": "z1",
                    "label": "Zone Description",
                    "data": {
                        "border": "north",
                        "width": 0,  # Invalid
                        "height": 100,
                        "sep_x": 50,
                        "sep_y": 50,
                    },
                }
            ],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Deployment Zone #1" in result
        assert "Width" in result

    def test_objective_point_missing_description_returns_error(self):
        """When Objective Point description is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[
                {"id": "p1", "cx": 100, "cy": 100, "description": ""}
            ],  # Missing description
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Objective Point #1" in result
        assert "Description" in result

    def test_objective_point_missing_x_coordinate_returns_error(self):
        """When Objective Point X coordinate is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[
                {"id": "p1", "cy": 100, "description": "Point A"}
            ],  # Missing cx
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Objective Point #1" in result
        assert "X Coordinate" in result

    def test_scenography_element_missing_type_returns_error(self):
        """When Scenography Element type is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[
                {
                    "id": "e1",
                    "type": "",  # Missing
                    "label": "Forest",
                    "data": {},
                    "allow_overlap": False,
                }
            ],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Scenography Element #1" in result
        assert "Element Type" in result

    def test_scenography_circle_missing_radius_returns_error(self):
        """When Scenography Circle radius is missing, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[
                {
                    "id": "e1",
                    "type": "circle",
                    "label": "Forest (Circle e1a2b3)",
                    "data": {
                        "type": "circle",
                        "cx": 100,
                        "cy": 100,
                        "r": 0,
                    },  # Invalid r
                    "allow_overlap": False,
                }
            ],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Circle #1" in result
        assert "Radius" in result

    def test_scenography_polygon_less_than_3_points_returns_error(self):
        """When Scenography Polygon has < 3 points, returns error."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="Test Scenario",
            m="matched_play",
            armies_val="Warriors 500",
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="Deployment strategy",
            lay="Layout description",
            obj="Objectives here",
            init_priority="Player 1",
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[
                {
                    "id": "e1",
                    "type": "polygon",
                    "label": "Building (Polygon e1a2b3 - 2 pts)",
                    "data": {
                        "type": "polygon",
                        "points": [[0, 0], [100, 100]],
                    },  # Only 2 pts
                    "allow_overlap": False,
                }
            ],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Polygon #1" in result
        assert "3 points" in result

    def test_multiple_errors_all_included_in_message(self):
        """When multiple fields are missing, all errors are included."""
        from adapters.ui_gradio.builders.payload import validate_required_fields

        result = validate_required_fields(
            actor="test-actor",
            name="",  # Missing
            m="",  # Missing
            armies_val="",  # Missing
            preset="standard",
            width=120.0,
            height=120.0,
            unit="cm",
            depl="",  # Missing
            lay="",  # Missing
            obj="",  # Missing
            init_priority="",  # Missing
            rules_state=[],
            vp_state=[],
            deployment_zones_state_val=[],
            objective_points_state_val=[],
            scenography_state_val=[],
            default_actor_id="demo-user",
        )

        assert result is not None
        assert "Scenario Name" in result
        assert "Game Mode" in result
        assert "Armies" in result
        assert "Deployment" in result
        assert "Layout" in result
        assert "Objectives" in result
        assert "Initial Priority" in result
