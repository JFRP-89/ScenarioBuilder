"""Tests for shape normalization helpers."""

from __future__ import annotations

from application.use_cases._shape_normalization import (
    extract_objective_shapes,
    flatten_map_shapes,
    normalize_shapes_for_map_spec,
)


class TestFlattenMapShapes:
    """Tests for flatten_map_shapes helper."""

    def test_flattens_dict_with_deployment_and_scenography(self):
        """Combines deployment_shapes and scenography_specs into flat list."""
        shapes_dict = {
            "deployment_shapes": [{"type": "rect", "x": 0, "y": 0}],
            "scenography_specs": [{"type": "circle", "cx": 100, "cy": 100}],
        }

        result = flatten_map_shapes(shapes_dict)

        assert result == [
            {"type": "rect", "x": 0, "y": 0},
            {"type": "circle", "cx": 100, "cy": 100},
        ]

    def test_handles_empty_deployment_shapes(self):
        """Works when deployment_shapes is missing or empty."""
        shapes_dict = {
            "scenography_specs": [{"type": "circle", "cx": 100, "cy": 100}],
        }

        result = flatten_map_shapes(shapes_dict)

        assert result == [{"type": "circle", "cx": 100, "cy": 100}]

    def test_handles_empty_scenography_specs(self):
        """Works when scenography_specs is missing or empty."""
        shapes_dict = {
            "deployment_shapes": [{"type": "rect", "x": 0, "y": 0}],
        }

        result = flatten_map_shapes(shapes_dict)

        assert result == [{"type": "rect", "x": 0, "y": 0}]

    def test_returns_empty_list_for_empty_dict(self):
        """Returns empty list when dict has no shapes."""
        result = flatten_map_shapes({})
        assert result == []

    def test_legacy_format_returns_list_unchanged(self):
        """Legacy format (already list) is returned as-is."""
        shapes_list = [{"type": "rect", "x": 0, "y": 0}]

        result = flatten_map_shapes(shapes_list)

        assert result is shapes_list


class TestExtractObjectiveShapes:
    """Tests for extract_objective_shapes helper."""

    def test_extracts_objective_shapes_from_dict(self):
        """Extracts objective_shapes from structured dict."""
        shapes_dict = {
            "deployment_shapes": [{"type": "rect"}],
            "objective_shapes": [{"type": "circle", "cx": 100, "cy": 100}],
        }

        result = extract_objective_shapes(shapes_dict)

        assert result == [{"type": "circle", "cx": 100, "cy": 100}]

    def test_returns_none_when_objective_shapes_missing(self):
        """Returns None when objective_shapes key not present."""
        shapes_dict = {
            "deployment_shapes": [{"type": "rect"}],
        }

        result = extract_objective_shapes(shapes_dict)

        assert result is None

    def test_returns_none_for_legacy_list_format(self):
        """Legacy format (list) has no objective_shapes."""
        shapes_list = [{"type": "rect"}]

        result = extract_objective_shapes(shapes_list)

        assert result is None


class TestNormalizeShapesForMapSpec:
    """Tests for normalize_shapes_for_map_spec convenience function."""

    def test_normalizes_full_shapes_dict(self):
        """Normalizes dict with all shape types."""
        shapes_dict = {
            "deployment_shapes": [{"type": "rect", "x": 0}],
            "scenography_specs": [{"type": "circle", "cx": 100}],
            "objective_shapes": [{"type": "circle", "cx": 200}],
        }

        flat_shapes, objective_shapes = normalize_shapes_for_map_spec(shapes_dict)

        assert flat_shapes == [
            {"type": "rect", "x": 0},
            {"type": "circle", "cx": 100},
        ]
        assert objective_shapes == [{"type": "circle", "cx": 200}]

    def test_normalizes_dict_without_objective_shapes(self):
        """Works when objective_shapes not present."""
        shapes_dict = {
            "deployment_shapes": [{"type": "rect"}],
            "scenography_specs": [],
        }

        flat_shapes, objective_shapes = normalize_shapes_for_map_spec(shapes_dict)

        assert flat_shapes == [{"type": "rect"}]
        assert objective_shapes is None

    def test_normalizes_legacy_list_format(self):
        """Handles legacy list format."""
        shapes_list = [{"type": "rect"}]

        flat_shapes, objective_shapes = normalize_shapes_for_map_spec(shapes_list)

        assert flat_shapes == [{"type": "rect"}]
        assert objective_shapes is None
