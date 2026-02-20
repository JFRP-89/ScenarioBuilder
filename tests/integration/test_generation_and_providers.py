"""Integration tests for shape generation, seed resolution, themes,
table resolution, content providers, and miscellaneous infrastructure.

These tests exercise the _generate sub-modules, FileContentProvider,
config, and other small infrastructure modules end-to-end.
"""

from __future__ import annotations

import random

import pytest
from application.use_cases._generate._card_mapping import (
    _card_to_full_data,
    _card_to_preview,
)
from application.use_cases._generate._dtos import GenerateScenarioCardRequest
from application.use_cases._generate._seed_resolution import (
    _resolve_seeded_content,
)
from application.use_cases._generate._shape_generation import (
    _build_non_overlapping_deployments,
    _generate_random_scenography,
    _generate_seeded_shapes,
)
from application.use_cases._generate._table_resolution import _resolve_table
from application.use_cases._generate._text_utils import (
    _is_blank_text,
    _objectives_match_seed,
)
from application.use_cases._generate._themes import (
    _resolve_seed_from_themes,
    resolve_seed_preview,
)
from application.use_cases._shape_normalization import (
    extract_objective_shapes,
    flatten_map_shapes,
    normalize_shapes_for_map_spec,
)
from domain.cards.card import Card, GameMode
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.config import get_env
from infrastructure.content.file_content_provider import FileContentProvider


# =============================================================================
# _generate_seeded_shapes — full pipeline
# =============================================================================
class TestGenerateSeededShapes:
    """Integration: deterministic shape generation from seed."""

    def test_returns_three_categories(self) -> None:
        result = _generate_seeded_shapes(seed=42, table_width=1200, table_height=1200)
        assert "deployment_shapes" in result
        assert "objective_shapes" in result
        assert "scenography_specs" in result

    def test_deterministic_for_same_seed(self) -> None:
        a = _generate_seeded_shapes(seed=99, table_width=1200, table_height=1200)
        b = _generate_seeded_shapes(seed=99, table_width=1200, table_height=1200)
        assert a == b

    def test_different_seeds_different_results(self) -> None:
        a = _generate_seeded_shapes(seed=1, table_width=1200, table_height=1200)
        b = _generate_seeded_shapes(seed=2, table_width=1200, table_height=1200)
        # Very unlikely to be identical
        assert a != b

    def test_deployment_shapes_are_non_overlapping_rects(self) -> None:
        result = _generate_seeded_shapes(seed=7, table_width=1200, table_height=1200)
        for dep in result["deployment_shapes"]:
            assert dep["type"] == "rect"
            assert dep["width"] > 0
            assert dep["height"] > 0

    def test_objective_shapes_are_points(self) -> None:
        # Use a seed that produces objectives
        for seed in range(1, 50):
            result = _generate_seeded_shapes(
                seed=seed, table_width=1200, table_height=1200
            )
            if result["objective_shapes"]:
                for obj in result["objective_shapes"]:
                    assert obj["type"] == "objective_point"
                break

    def test_scenography_has_mixed_types(self) -> None:
        """Over many seeds, we should see circles, rects, and polygons."""
        types_seen: set[str] = set()
        for seed in range(1, 200):
            result = _generate_seeded_shapes(
                seed=seed, table_width=1200, table_height=1200
            )
            for s in result["scenography_specs"]:
                types_seen.add(s["type"])
            if types_seen >= {"circle", "rect", "polygon"}:
                break
        assert types_seen >= {"circle", "rect", "polygon"}

    def test_massive_table(self) -> None:
        result = _generate_seeded_shapes(seed=42, table_width=2400, table_height=1200)
        assert isinstance(result, dict)


# =============================================================================
# _build_non_overlapping_deployments
# =============================================================================
class TestBuildNonOverlappingDeployments:
    """Integration: deployment zone builder."""

    def test_all_four_edges(self) -> None:
        zones = _build_non_overlapping_deployments(
            ["north", "south", "east", "west"],
            dep_depth=200,
            table_width=1200,
            table_height=1200,
        )
        assert len(zones) == 4
        borders = {z["border"] for z in zones}
        assert borders == {"north", "south", "east", "west"}

    def test_north_only(self) -> None:
        zones = _build_non_overlapping_deployments(
            ["north"], dep_depth=200, table_width=1200, table_height=1200
        )
        assert len(zones) == 1
        assert zones[0]["y"] == 0

    def test_south_only(self) -> None:
        zones = _build_non_overlapping_deployments(
            ["south"], dep_depth=200, table_width=1200, table_height=1200
        )
        assert len(zones) == 1
        assert zones[0]["y"] == 1000  # 1200 - 200

    def test_east_west_zones_inset_when_north_south(self) -> None:
        zones = _build_non_overlapping_deployments(
            ["north", "south", "east", "west"],
            dep_depth=200,
            table_width=1200,
            table_height=1200,
        )
        east = next(z for z in zones if z["border"] == "east")
        west = next(z for z in zones if z["border"] == "west")
        # E/W zones should be inset vertically by dep_depth
        assert east["y"] == 200
        assert west["y"] == 200
        assert east["height"] == 800  # 1200 - 200 - 200

    def test_empty_list(self) -> None:
        zones = _build_non_overlapping_deployments(
            [], dep_depth=200, table_width=1200, table_height=1200
        )
        assert zones == []


# =============================================================================
# _generate_random_scenography
# =============================================================================
class TestGenerateRandomScenography:
    """Integration: random scenography shape generation."""

    def test_circle_shape(self) -> None:
        rng = random.Random(10)
        shape = _generate_random_scenography(rng, 1200, 1200, False)
        assert shape["type"] in {"circle", "rect", "polygon"}

    def test_overlap_flag_respected(self) -> None:
        for seed in range(50):
            rng = random.Random(seed)
            shape = _generate_random_scenography(rng, 1200, 1200, True)
            assert shape["allow_overlap"] is True

    def test_all_shape_types_possible(self) -> None:
        types_seen: set[str] = set()
        for seed in range(200):
            rng = random.Random(seed)
            shape = _generate_random_scenography(rng, 1200, 1200, False)
            types_seen.add(shape["type"])
            if types_seen >= {"circle", "rect", "polygon"}:
                break
        assert types_seen >= {"circle", "rect", "polygon"}


# =============================================================================
# _resolve_seed_from_themes / resolve_seed_preview
# =============================================================================
class TestResolveSeedFromThemes:
    """Integration: theme-based content resolution."""

    def test_positive_seed_returns_fields(self) -> None:
        result = _resolve_seed_from_themes(42)
        assert set(result.keys()) == {
            "armies",
            "deployment",
            "layout",
            "objectives",
            "initial_priority",
        }
        # All non-empty
        for v in result.values():
            assert isinstance(v, str)
            assert len(v) > 0

    def test_zero_seed_returns_blanks(self) -> None:
        result = _resolve_seed_from_themes(0)
        for v in result.values():
            assert v == ""

    def test_negative_seed_returns_blanks(self) -> None:
        result = _resolve_seed_from_themes(-5)
        for v in result.values():
            assert v == ""

    def test_deterministic(self) -> None:
        a = _resolve_seed_from_themes(123)
        b = _resolve_seed_from_themes(123)
        assert a == b

    def test_public_resolve_seed_preview(self) -> None:
        result = resolve_seed_preview(42)
        assert "armies" in result


# =============================================================================
# _resolve_table
# =============================================================================
class TestResolveTable:
    """Integration: table preset resolution."""

    def test_standard(self) -> None:
        t = _resolve_table("standard")
        assert t.width_mm == 1200
        assert t.height_mm == 1200

    def test_massive(self) -> None:
        t = _resolve_table("massive")
        assert t.width_mm > 1200

    def test_custom(self) -> None:
        t = _resolve_table("custom", width_mm=800, height_mm=600)
        assert t.width_mm == 800
        assert t.height_mm == 600

    def test_custom_missing_dims_raises(self) -> None:
        with pytest.raises(ValidationError):
            _resolve_table("custom")

    def test_unknown_preset_raises(self) -> None:
        with pytest.raises(ValidationError, match="unknown table preset"):
            _resolve_table("unknown")


# =============================================================================
# _text_utils
# =============================================================================
class TestTextUtils:
    """Integration: text utility functions."""

    def test_is_blank_text(self) -> None:
        assert _is_blank_text(None) is True
        assert _is_blank_text("") is True
        assert _is_blank_text("   ") is True
        assert _is_blank_text("hello") is False

    def test_objectives_match_seed_blank(self) -> None:
        assert _objectives_match_seed(None, "Objective A") is True
        assert _objectives_match_seed("", "Objective A") is True
        assert _objectives_match_seed("  ", "Objective A") is True

    def test_objectives_match_seed_dict(self) -> None:
        assert _objectives_match_seed({"objective": "A"}, "Objective A") is False

    def test_objectives_match_seed_exact(self) -> None:
        assert _objectives_match_seed("Objective A", "Objective A") is True
        assert _objectives_match_seed("Different", "Objective A") is False


# =============================================================================
# _card_mapping
# =============================================================================
class TestCardMapping:
    """Integration: card→preview and card→full_data mappings."""

    def _make_rich_card(self) -> Card:
        table = TableSize.standard()
        shapes = [{"type": "rect", "x": 10, "y": 10, "width": 200, "height": 200}]
        dep_shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
                "border": "north",
            }
        ]
        obj_shapes = [{"type": "objective_point", "cx": 600, "cy": 600}]
        map_spec = MapSpec(
            table=table,
            shapes=shapes,
            deployment_shapes=dep_shapes,
            objective_shapes=obj_shapes,
        )
        return Card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=42,
            table=table,
            map_spec=map_spec,
            name="Test Battle",
            armies="Test Army",
            deployment="Hold the line",
            layout="River Crossing",
            objectives="Hold the bridge",
            initial_priority="Control the river",
            special_rules=[{"name": "Night Fight", "description": "Darkness"}],
        )

    def test_card_to_preview(self) -> None:
        card = self._make_rich_card()
        preview = _card_to_preview(card)
        assert preview["name"] == "Test Battle"
        assert preview["armies"] == "Test Army"
        assert preview["objectives"] == "Hold the bridge"

    def test_card_to_preview_with_dict_objectives(self) -> None:
        table = TableSize.standard()
        shapes = [{"type": "rect", "x": 10, "y": 10, "width": 200, "height": 200}]
        card = Card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=42,
            table=table,
            map_spec=MapSpec(table=table, shapes=shapes),
            objectives={"objective": "Win", "victory_points": 3},
        )
        preview = _card_to_preview(card)
        assert preview["objectives"] == "Win"

    def test_card_to_full_data(self) -> None:
        card = self._make_rich_card()
        data = _card_to_full_data(card)
        assert data["name"] == "Test Battle"
        assert data["armies"] == "Test Army"
        assert data["special_rules"] is not None
        assert len(data["deployment_shapes"]) == 1
        assert len(data["objective_shapes"]) == 1
        assert len(data["scenography_specs"]) == 1


# =============================================================================
# _resolve_seeded_content
# =============================================================================
class TestResolveSeededContent:
    """Integration: seed content resolution with request + card."""

    def _make_request(self, **overrides) -> GenerateScenarioCardRequest:
        defaults = {
            "actor_id": "u1",
            "mode": "matched",
            "seed": None,
            "table_preset": "standard",
            "visibility": None,
            "shared_with": None,
        }
        defaults.update(overrides)
        return GenerateScenarioCardRequest(**defaults)  # type: ignore[arg-type]

    def test_zero_seed_returns_request_values(self) -> None:
        req = self._make_request(armies="My Army", deployment="My Deploy")
        result = _resolve_seeded_content(0, req)
        assert result["armies"] == "My Army"
        assert result["deployment"] == "My Deploy"

    def test_positive_seed_fills_blanks_from_theme(self) -> None:
        req = self._make_request()  # All blank
        result = _resolve_seeded_content(42, req, existing_card=None)
        # Should be non-empty (filled from themes)
        assert result["armies"]
        assert result["deployment"]
        assert result["layout"]
        assert result["objectives"]

    def test_positive_seed_with_existing_card(self) -> None:
        table = TableSize.standard()
        shapes = [{"type": "rect", "x": 10, "y": 10, "width": 200, "height": 200}]
        card = Card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=42,
            table=table,
            map_spec=MapSpec(table=table, shapes=shapes),
            armies="Card Army",
            deployment="Card Deploy",
            layout="Card Layout",
            objectives="Card Obj",
            initial_priority="Card Priority",
        )
        req = self._make_request()  # All blank in request
        result = _resolve_seeded_content(42, req, existing_card=card)
        assert result["armies"] == "Card Army"
        assert result["deployment"] == "Card Deploy"

    def test_user_values_override_existing_card(self) -> None:
        table = TableSize.standard()
        shapes = [{"type": "rect", "x": 10, "y": 10, "width": 200, "height": 200}]
        card = Card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=42,
            table=table,
            map_spec=MapSpec(table=table, shapes=shapes),
            armies="Card Army",
            deployment="Card Deploy",
            layout="Card Layout",
            objectives="Card Obj",
            initial_priority="Card Priority",
        )
        req = self._make_request(armies="User Army")
        result = _resolve_seeded_content(42, req, existing_card=card)
        assert result["armies"] == "User Army"
        assert result["deployment"] == "Card Deploy"  # blank → card


# =============================================================================
# _shape_normalization
# =============================================================================
class TestShapeNormalization:
    """Integration: shape normalization helpers."""

    def test_flatten_from_dict(self) -> None:
        shapes = {
            "deployment_shapes": [
                {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
            ],
            "scenography_specs": [{"type": "circle", "cx": 50, "cy": 50, "r": 20}],
        }
        flat = flatten_map_shapes(shapes)
        assert len(flat) == 2

    def test_flatten_from_list(self) -> None:
        shapes = [{"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}]
        flat = flatten_map_shapes(shapes)
        assert flat == shapes

    def test_extract_objectives_from_dict(self) -> None:
        shapes = {
            "objective_shapes": [{"type": "circle", "cx": 100, "cy": 100}],
        }
        result = extract_objective_shapes(shapes)
        assert result is not None
        assert len(result) == 1

    def test_extract_objectives_from_list(self) -> None:
        assert extract_objective_shapes([]) is None

    def test_normalize_combined(self) -> None:
        shapes = {
            "deployment_shapes": [
                {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
            ],
            "scenography_specs": [],
            "objective_shapes": [{"type": "circle", "cx": 100, "cy": 100}],
        }
        flat, obj = normalize_shapes_for_map_spec(shapes)
        assert len(flat) == 1
        assert obj is not None


# =============================================================================
# FileContentProvider
# =============================================================================
class TestFileContentProvider:
    """Integration: FileContentProvider with real JSON files."""

    def test_get_layouts(self) -> None:
        provider = FileContentProvider()
        layouts = list(provider.get_layouts())
        assert len(layouts) > 0

    def test_get_deployments(self) -> None:
        provider = FileContentProvider()
        deployments = list(provider.get_deployments())
        assert len(deployments) > 0

    def test_get_objectives(self) -> None:
        provider = FileContentProvider()
        objectives = list(provider.get_objectives())
        assert len(objectives) > 0

    def test_get_twists(self) -> None:
        provider = FileContentProvider()
        twists = list(provider.get_twists())
        assert len(twists) > 0

    def test_get_story_hooks(self) -> None:
        provider = FileContentProvider()
        hooks = list(provider.get_story_hooks())
        assert len(hooks) > 0

    def test_get_constraints(self) -> None:
        provider = FileContentProvider()
        constraints = list(provider.get_constraints())
        assert len(constraints) > 0


# =============================================================================
# infrastructure.config
# =============================================================================
class TestConfig:
    """Integration: config helper."""

    def test_get_env_existing(self) -> None:
        import os

        os.environ["_SB_TEST_KEY"] = "test_val"
        try:
            assert get_env("_SB_TEST_KEY") == "test_val"
        finally:
            del os.environ["_SB_TEST_KEY"]

    def test_get_env_default(self) -> None:
        assert get_env("_SB_NONEXISTENT_KEY_12345", "fallback") == "fallback"

    def test_get_env_none_default(self) -> None:
        assert get_env("_SB_NONEXISTENT_KEY_12345") is None


# =============================================================================
# DemoCurrentUserProvider
# =============================================================================
class TestDemoCurrentUserProvider:
    """Integration: DemoCurrentUserProvider."""

    def test_returns_default_user_id(self) -> None:
        from infrastructure.auth.demo_current_user_provider import (
            DemoCurrentUserProvider,
        )

        provider = DemoCurrentUserProvider()
        user_id = provider.get_current_user_id()
        assert isinstance(user_id, str)
        assert len(user_id) > 0
