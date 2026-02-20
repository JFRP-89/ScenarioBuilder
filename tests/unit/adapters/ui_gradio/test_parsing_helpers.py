"""
Unit tests for parsing/building helpers in Gradio UI adapter.

After refactoring, raw JSON parsing (_parse_json_list, _parse_deployment_shapes,
_parse_map_specs) was replaced by state-based builders in builders.shapes.
_build_shared_with_list logic is now inline in builders.payload.apply_visibility.

These tests verify the equivalent behavior in the new modules.
"""

from __future__ import annotations


# =============================================================================
# Tests for build_map_specs_from_state (replaces _parse_map_specs)
# =============================================================================
class TestBuildMapSpecsFromState:
    """Tests for builders.shapes.build_map_specs_from_state()."""

    def test_empty_state_returns_empty_list(self):
        """Empty state returns []."""
        from adapters.ui_gradio.builders.shapes import build_map_specs_from_state

        assert build_map_specs_from_state([]) == []

    def test_single_element_returns_shape_dict(self):
        """Single element with data is returned as shape dict."""
        from adapters.ui_gradio.builders.shapes import build_map_specs_from_state

        state = [
            {
                "id": "e1",
                "type": "rect",
                "label": "Forest",
                "data": {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100},
                "allow_overlap": False,
            }
        ]
        result = build_map_specs_from_state(state)  # type: ignore[arg-type]

        assert len(result) == 1
        assert result[0]["type"] == "rect"
        assert result[0]["x"] == 0
        assert result[0]["allow_overlap"] is False

    def test_many_elements_are_returned(self):
        """Multiple elements are all included in result."""
        from adapters.ui_gradio.builders.shapes import build_map_specs_from_state

        state = [
            {
                "id": f"e{i}",
                "type": "circle",
                "label": f"Item {i}",
                "data": {"type": "circle", "cx": i * 10, "cy": i * 10, "r": 5},
                "allow_overlap": False,
            }
            for i in range(50)
        ]
        result = build_map_specs_from_state(state)  # type: ignore[arg-type]

        assert len(result) == 50

    def test_each_element_has_type_from_data(self):
        """Each result element preserves the 'type' field from data."""
        from adapters.ui_gradio.builders.shapes import build_map_specs_from_state

        state = [
            {
                "id": "e1",
                "type": "circle",
                "label": "Item",
                "data": {"type": "circle", "cx": 50, "cy": 50, "r": 10},
                "allow_overlap": False,
            }
        ]
        result = build_map_specs_from_state(state)  # type: ignore[arg-type]
        assert result[0]["type"] == "circle"

    def test_overlap_elements_sorted_first(self):
        """Elements with allow_overlap=True are sorted first."""
        from adapters.ui_gradio.builders.shapes import build_map_specs_from_state

        state = [
            {
                "id": "e1",
                "type": "rect",
                "label": "A",
                "data": {"type": "rect", "x": 0, "y": 0, "width": 10, "height": 10},
                "allow_overlap": False,
            },
            {
                "id": "e2",
                "type": "circle",
                "label": "B",
                "data": {"type": "circle", "cx": 50, "cy": 50, "r": 5},
                "allow_overlap": True,
            },
        ]
        result = build_map_specs_from_state(state)  # type: ignore[arg-type]

        assert result[0]["allow_overlap"] is True
        assert result[1]["allow_overlap"] is False


# =============================================================================
# Tests for build_deployment_shapes_from_state (replaces _parse_deployment_shapes)
# =============================================================================
class TestBuildDeploymentShapesFromState:
    """Tests for builders.shapes.build_deployment_shapes_from_state()."""

    def test_empty_state_returns_empty_list(self):
        """Empty state returns []."""
        from adapters.ui_gradio.builders.shapes import (
            build_deployment_shapes_from_state,
        )

        assert build_deployment_shapes_from_state([]) == []

    def test_valid_zones_return_shape_dicts(self):
        """Valid zones with data are returned as shape dicts (max 2)."""
        from adapters.ui_gradio.builders.shapes import (
            build_deployment_shapes_from_state,
        )

        state = [
            {
                "id": "z1",
                "label": "North",
                "data": {
                    "type": "deployment_zone",
                    "description": "North",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 300,
                    "border": "north",
                    "depth": 300,
                    "separation": 0,
                },
            },
            {
                "id": "z2",
                "label": "South",
                "data": {
                    "type": "deployment_zone",
                    "description": "South",
                    "x": 0,
                    "y": 900,
                    "width": 1200,
                    "height": 300,
                    "border": "south",
                    "depth": 300,
                    "separation": 0,
                },
            },
        ]
        result = build_deployment_shapes_from_state(state)  # type: ignore[arg-type]

        assert len(result) == 2
        assert result[0]["type"] == "deployment_zone"
        assert result[0]["border"] == "north"

    def test_removes_internal_fields_depth_and_separation(self):
        """Internal fields (depth, separation) are stripped from output."""
        from adapters.ui_gradio.builders.shapes import (
            build_deployment_shapes_from_state,
        )

        state = [
            {
                "id": "z1",
                "label": "North",
                "data": {
                    "type": "deployment_zone",
                    "description": "North",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 300,
                    "border": "north",
                    "depth": 300,
                    "separation": 0,
                },
            }
        ]
        result = build_deployment_shapes_from_state(state)  # type: ignore[arg-type]

        assert "depth" not in result[0]
        assert "separation" not in result[0]

    def test_zone_has_type_field_in_data(self):
        """Zone data includes a 'type' field in output."""
        from adapters.ui_gradio.builders.shapes import (
            build_deployment_shapes_from_state,
        )

        state = [
            {
                "id": "z1",
                "label": "North",
                "data": {
                    "type": "deployment_zone",
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 100,
                    "border": "north",
                },
            }
        ]
        result = build_deployment_shapes_from_state(state)  # type: ignore[arg-type]

        assert result[0]["type"] == "deployment_zone"


# =============================================================================
# Tests for apply_visibility shared_with parsing (replaces _build_shared_with_list)
# =============================================================================
class TestApplyVisibilitySharedWith:
    """Tests for shared_with parsing inside builders.payload.apply_visibility()."""

    def test_single_user_id(self):
        """Single user ID results in shared_with list with one element."""
        from adapters.ui_gradio.builders.payload import apply_visibility

        payload: dict = {}
        apply_visibility(payload, "shared", "user1")

        assert payload["shared_with"] == ["user1"]

    def test_comma_separated_user_ids(self):
        """Comma-separated user IDs produce a list."""
        from adapters.ui_gradio.builders.payload import apply_visibility

        payload: dict = {}
        apply_visibility(payload, "shared", "user1,user2,user3")

        assert payload["shared_with"] == ["user1", "user2", "user3"]

    def test_strips_whitespace_around_ids(self):
        """Whitespace around user IDs is stripped."""
        from adapters.ui_gradio.builders.payload import apply_visibility

        payload: dict = {}
        apply_visibility(payload, "shared", " user1 , user2 , user3 ")

        assert payload["shared_with"] == ["user1", "user2", "user3"]

    def test_empty_string_does_not_add_shared_with(self):
        """Empty or whitespace-only string does not add shared_with."""
        from adapters.ui_gradio.builders.payload import apply_visibility

        payload: dict = {}
        apply_visibility(payload, "shared", "")

        assert "shared_with" not in payload

    def test_only_commas_does_not_add_shared_with(self):
        """String with only commas (no IDs) does not add shared_with."""
        from adapters.ui_gradio.builders.payload import apply_visibility

        payload: dict = {}
        apply_visibility(payload, "shared", ",,,")

        assert "shared_with" not in payload

    def test_ignores_empty_entries_between_commas(self):
        """Empty entries between commas are ignored."""
        from adapters.ui_gradio.builders.payload import apply_visibility

        payload: dict = {}
        apply_visibility(payload, "shared", "user1,,user2,  ,user3")

        assert payload["shared_with"] == ["user1", "user2", "user3"]
