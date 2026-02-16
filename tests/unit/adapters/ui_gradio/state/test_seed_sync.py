"""Tests for API → UI state conversion in _seed_sync module."""

from __future__ import annotations

from adapters.ui_gradio._state._seed_sync import (
    api_deployment_to_ui_state,
    api_objectives_to_ui_state,
    api_scenography_to_ui_state,
)

# ── Deployment zones ──────────────────────────────────────────────────


class TestApiDeploymentToUiState:
    """Test api_deployment_to_ui_state converter."""

    def test_empty_list_returns_empty(self):
        assert api_deployment_to_ui_state([]) == []

    def test_single_zone_has_required_keys(self):
        api_shape = {
            "type": "rect",
            "x": 0,
            "y": 0,
            "width": 200,
            "height": 1200,
            "border": "west",
            "description": "Western flank",
        }
        result = api_deployment_to_ui_state([api_shape])
        assert len(result) == 1
        zone = result[0]
        assert "id" in zone
        assert "label" in zone
        assert "data" in zone
        assert len(zone["id"]) == 8
        assert "Western flank" in zone["label"]
        assert zone["data"]["type"] == "rect"
        assert zone["data"]["width"] == 200

    def test_zone_without_description(self):
        api_shape = {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        result = api_deployment_to_ui_state([api_shape])
        zone = result[0]
        assert zone["label"].startswith("Zone ")

    def test_multiple_zones_get_unique_ids(self):
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "border": "north",
            },
            {
                "type": "rect",
                "x": 0,
                "y": 1100,
                "width": 100,
                "height": 100,
                "border": "south",
            },
        ]
        result = api_deployment_to_ui_state(shapes)
        assert len(result) == 2
        assert result[0]["id"] != result[1]["id"]

    def test_data_is_shallow_copy(self):
        api_shape = {"type": "rect", "x": 10, "y": 20}
        result = api_deployment_to_ui_state([api_shape])
        # Mutating original shouldn't affect state
        api_shape["x"] = 999
        assert result[0]["data"]["x"] == 10


# ── Objective points ─────────────────────────────────────────────────


class TestApiObjectivesToUiState:
    """Test api_objectives_to_ui_state converter."""

    def test_empty_list_returns_empty(self):
        assert api_objectives_to_ui_state([]) == []

    def test_single_point_has_required_keys(self):
        api_shape = {
            "type": "objective_point",
            "cx": 600.0,
            "cy": 600.0,
            "description": "Center objective",
        }
        result = api_objectives_to_ui_state([api_shape])
        assert len(result) == 1
        pt = result[0]
        assert "id" in pt
        assert pt["cx"] == 600.0
        assert pt["cy"] == 600.0
        assert pt["description"] == "Center objective"
        # Flat format: no "data" wrapper
        assert "data" not in pt

    def test_point_without_description(self):
        api_shape = {"type": "objective_point", "cx": 100, "cy": 200}
        result = api_objectives_to_ui_state([api_shape])
        pt = result[0]
        assert "description" not in pt
        assert pt["cx"] == 100
        assert pt["cy"] == 200

    def test_default_coordinates(self):
        api_shape = {"type": "objective_point"}
        result = api_objectives_to_ui_state([api_shape])
        assert result[0]["cx"] == 0
        assert result[0]["cy"] == 0

    def test_multiple_points_unique_ids(self):
        shapes = [
            {"cx": 100, "cy": 100},
            {"cx": 200, "cy": 200},
            {"cx": 300, "cy": 300},
        ]
        result = api_objectives_to_ui_state(shapes)
        ids = [p["id"] for p in result]
        assert len(set(ids)) == 3


# ── Scenography ──────────────────────────────────────────────────────


class TestApiScenographyToUiState:
    """Test api_scenography_to_ui_state converter."""

    def test_empty_list_returns_empty(self):
        assert api_scenography_to_ui_state([]) == []

    def test_circle_element(self):
        api_shape = {
            "type": "circle",
            "cx": 600,
            "cy": 600,
            "r": 50,
            "description": "Fountain",
            "allow_overlap": False,
        }
        result = api_scenography_to_ui_state([api_shape])
        elem = result[0]
        assert elem["type"] == "circle"
        assert "Fountain" in elem["label"]
        assert "Circle" in elem["label"]
        assert elem["allow_overlap"] is False
        assert "allow_overlap" not in elem["data"]
        assert elem["data"]["type"] == "circle"
        assert elem["data"]["cx"] == 600
        assert elem["data"]["r"] == 50

    def test_rect_element(self):
        api_shape = {
            "type": "rect",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 150,
            "description": "Building",
        }
        result = api_scenography_to_ui_state([api_shape])
        elem = result[0]
        assert elem["type"] == "rect"
        assert "Building" in elem["label"]
        assert "Rect" in elem["label"]
        assert elem["allow_overlap"] is False  # default
        assert elem["data"]["width"] == 200

    def test_polygon_element(self):
        pts = [[0, 0], [100, 0], [50, 80]]
        api_shape = {
            "type": "polygon",
            "points": pts,
            "allow_overlap": True,
            "description": "Forest",
        }
        result = api_scenography_to_ui_state([api_shape])
        elem = result[0]
        assert elem["type"] == "polygon"
        assert "Forest" in elem["label"]
        assert "3 pts" in elem["label"]
        assert elem["allow_overlap"] is True
        assert elem["data"]["points"] == pts

    def test_element_without_description(self):
        api_shape = {"type": "circle", "cx": 0, "cy": 0, "r": 10}
        result = api_scenography_to_ui_state([api_shape])
        elem = result[0]
        # Label should just be "Circle <id>" without description prefix
        assert elem["label"].startswith("Circle ")

    def test_unknown_type(self):
        api_shape = {"type": "custom_shape", "data": "anything"}
        result = api_scenography_to_ui_state([api_shape])
        assert result[0]["type"] == "custom_shape"
        assert "custom_shape" in result[0]["label"]

    def test_multiple_elements_unique_ids(self):
        shapes = [
            {"type": "circle", "cx": 100, "cy": 100, "r": 20},
            {"type": "rect", "x": 200, "y": 200, "width": 50, "height": 50},
            {"type": "polygon", "points": [[0, 0], [10, 0], [5, 8]]},
        ]
        result = api_scenography_to_ui_state(shapes)
        ids = [e["id"] for e in result]
        assert len(set(ids)) == 3


# ── Integration: round-trip shape data ────────────────────────────────


class TestConverterIntegration:
    """Test that converter output matches expected UI state format."""

    def test_deployment_state_matches_existing_format(self):
        """Deployment state should have same structure as add_deployment_zone output."""
        api_shape = {
            "type": "rect",
            "x": 0,
            "y": 0,
            "width": 200,
            "height": 1200,
            "border": "west",
            "description": "West deployment",
        }
        state = api_deployment_to_ui_state([api_shape])
        zone = state[0]
        # Required keys per _deployment_zones.py add_deployment_zone
        assert set(zone.keys()) == {"id", "label", "data"}
        assert isinstance(zone["id"], str)
        assert isinstance(zone["label"], str)
        assert isinstance(zone["data"], dict)

    def test_objective_state_matches_existing_format(self):
        """Objective state should be flat: {id, cx, cy, description?}."""
        api_shape = {"cx": 300, "cy": 400, "description": "Marker"}
        state = api_objectives_to_ui_state([api_shape])
        pt = state[0]
        assert set(pt.keys()) == {"id", "cx", "cy", "description"}

    def test_scenography_state_matches_existing_format(self):
        """Scenography state should have {id, type, label, data, allow_overlap}."""
        api_shape = {"type": "circle", "cx": 100, "cy": 200, "r": 30}
        state = api_scenography_to_ui_state([api_shape])
        elem = state[0]
        assert set(elem.keys()) == {"id", "type", "label", "data", "allow_overlap"}
