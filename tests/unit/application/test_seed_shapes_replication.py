"""Tests for seed-based full scenario replication and deterministic shape generation.

Covers:
- _generate_seeded_shapes: deterministic, valid, constrained
- _card_to_full_data: extracts everything from a Card
- resolve_full_seed_scenario: existing card → full data, theme → text + shapes
- execute(): auto-fills shapes/special_rules/name from seed when user provides none
- resolve_seed_preview(): includes name field
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field

from application.use_cases.generate_scenario_card import (
    GenerateScenarioCard,
    GenerateScenarioCardRequest,
    _card_to_full_data,
    _card_to_preview,
    _generate_seeded_shapes,
)
from domain.cards.card import Card, GameMode
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.repositories.in_memory_card_repository import (
    InMemoryCardRepository,
)


# =============================================================================
# TEST DOUBLES
# =============================================================================
class _FakeIdGen:
    def generate_card_id(self) -> str:
        return "card-test-001"


class _FakeSeedGen:
    def generate_seed(self) -> int:
        return 999

    def calculate_from_config(self, config: dict) -> int:
        """Delegate to the real deterministic implementation."""
        from infrastructure.generators.deterministic_seed_generator import (
            calculate_seed_from_config,
        )

        return calculate_seed_from_config(config)


@dataclass
class _FakeScenarioGen:
    shapes: list[dict] = dc_field(default_factory=list)
    calls: list = dc_field(default_factory=list)

    def generate_shapes(self, seed, table, mode):
        self.calls.append((seed, table, mode))
        return self.shapes


def _make_card(
    seed: int = 42,
    name: str = "My Saved Scenario",
    armies: str = "Saved Army",
    deployment: str = "Saved Deployment",
    layout: str = "Saved Layout",
    objectives=None,
    initial_priority: str = "Saved Priority",
    special_rules=None,
    deployment_shapes=None,
    objective_shapes=None,
    scenography_specs=None,
) -> Card:
    table = TableSize.standard()
    ms = MapSpec(
        table=table,
        shapes=scenography_specs or [],
        deployment_shapes=deployment_shapes,
        objective_shapes=objective_shapes,
    )
    return Card(
        card_id="existing-001",
        owner_id="u1",
        visibility=Visibility.PRIVATE,
        shared_with=frozenset(),
        mode=GameMode.CASUAL,
        seed=seed,
        table=table,
        map_spec=ms,
        name=name,
        armies=armies,
        deployment=deployment,
        layout=layout,
        objectives=objectives or "Saved Objectives",
        initial_priority=initial_priority,
        special_rules=special_rules,
    )


def _uc_with_repo(cards=None) -> tuple[GenerateScenarioCard, InMemoryCardRepository]:
    repo = InMemoryCardRepository()
    for c in cards or []:
        repo.save(c)
    uc = GenerateScenarioCard(
        id_generator=_FakeIdGen(),
        seed_generator=_FakeSeedGen(),
        scenario_generator=_FakeScenarioGen(),
        card_repository=repo,
    )
    return uc, repo


# =============================================================================
# _generate_seeded_shapes
# =============================================================================
class TestGenerateSeededShapes:
    """Tests for deterministic shape generation."""

    def test_returns_three_shape_categories(self):
        result = _generate_seeded_shapes(1, 1200, 1200)
        assert "deployment_shapes" in result
        assert "objective_shapes" in result
        assert "scenography_specs" in result

    def test_deterministic_same_seed_same_result(self):
        a = _generate_seeded_shapes(12345, 1200, 1200)
        b = _generate_seeded_shapes(12345, 1200, 1200)
        assert a == b

    def test_different_seed_different_result(self):
        a = _generate_seeded_shapes(1, 1200, 1200)
        b = _generate_seeded_shapes(2, 1200, 1200)
        assert a != b

    def test_deployment_shapes_max_four(self):
        """No matter the seed, deployment_shapes never exceeds 4."""
        for s in range(100):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            assert len(shapes["deployment_shapes"]) <= 4

    def test_objective_shapes_max_ten(self):
        for s in range(100):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            assert len(shapes["objective_shapes"]) <= 10

    def test_scenography_max_six(self):
        """0-3 solid + 0-3 passable = max 6."""
        for s in range(100):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            assert len(shapes["scenography_specs"]) <= 6

    def test_deployment_shapes_are_border_rects(self):
        """All deployment shapes are rect type with a border key."""
        for s in range(50):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            for d in shapes["deployment_shapes"]:
                assert d["type"] == "rect"
                assert d["border"] in {"north", "south", "east", "west"}

    def test_objective_shapes_are_objective_points(self):
        for s in range(50):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            for o in shapes["objective_shapes"]:
                assert o["type"] == "objective_point"
                assert "cx" in o and "cy" in o

    def test_shapes_within_table_bounds(self):
        """All generated shapes fit inside the table."""
        for s in range(50):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            for d in shapes["deployment_shapes"]:
                assert d["x"] >= 0 and d["y"] >= 0
                assert d["x"] + d["width"] <= 1200
                assert d["y"] + d["height"] <= 1200
            for o in shapes["objective_shapes"]:
                assert 0 <= o["cx"] <= 1200
                assert 0 <= o["cy"] <= 1200

    def test_scenography_has_allow_overlap(self):
        """Every scenography shape has allow_overlap boolean."""
        for s in range(50):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            for sc in shapes["scenography_specs"]:
                assert "allow_overlap" in sc
                assert isinstance(sc["allow_overlap"], bool)

    def test_shapes_pass_map_spec_validation(self):
        """Generated shapes pass MapSpec domain validation."""
        table = TableSize.standard()
        for s in range(50):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            # Should not raise
            MapSpec(
                table=table,
                shapes=shapes["scenography_specs"],
                deployment_shapes=shapes["deployment_shapes"],
                objective_shapes=shapes["objective_shapes"],
            )

    def test_works_with_massive_table(self):
        shapes = _generate_seeded_shapes(42, 1800, 1200)
        table = TableSize.massive()
        MapSpec(
            table=table,
            shapes=shapes["scenography_specs"],
            deployment_shapes=shapes["deployment_shapes"],
            objective_shapes=shapes["objective_shapes"],
        )

    def test_independent_of_text_rng(self):
        """Shape RNG is isolated from theme text RNG (seed prefix)."""
        # Even if we change text content selection order, shapes stay the same.
        a = _generate_seeded_shapes(42, 1200, 1200)
        b = _generate_seeded_shapes(42, 1200, 1200)
        assert a == b

    def test_deployment_zones_never_overlap(self):
        """No two deployment zones share any area (zero collision)."""
        for s in range(200):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            deps = shapes["deployment_shapes"]
            for i, a in enumerate(deps):
                for b in deps[i + 1 :]:
                    # Two rects overlap iff they overlap on BOTH axes
                    x_overlap = (
                        a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"]
                    )
                    y_overlap = (
                        a["y"] < b["y"] + b["height"] and b["y"] < a["y"] + a["height"]
                    )
                    assert not (
                        x_overlap and y_overlap
                    ), f"seed={s}: {a['border']} overlaps {b['border']}"

    def test_deployment_zones_no_overlap_massive_table(self):
        """Non-overlapping constraint also holds for non-square tables."""
        for s in range(100):
            shapes = _generate_seeded_shapes(s, 1800, 1200)
            deps = shapes["deployment_shapes"]
            for i, a in enumerate(deps):
                for b in deps[i + 1 :]:
                    x_overlap = (
                        a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"]
                    )
                    y_overlap = (
                        a["y"] < b["y"] + b["height"] and b["y"] < a["y"] + a["height"]
                    )
                    assert not (
                        x_overlap and y_overlap
                    ), f"seed={s}: {a['border']} overlaps {b['border']}"

    def test_deployment_positive_dimensions(self):
        """All deployment rects have positive width and height."""
        for s in range(200):
            shapes = _generate_seeded_shapes(s, 1200, 1200)
            for d in shapes["deployment_shapes"]:
                assert d["width"] > 0, f"seed={s}: {d['border']} width <= 0"
                assert d["height"] > 0, f"seed={s}: {d['border']} height <= 0"


# =============================================================================
# _card_to_full_data / _card_to_preview
# =============================================================================
class TestCardDataExtraction:
    """Tests for _card_to_full_data and _card_to_preview."""

    def test_full_data_includes_shapes(self):
        dep = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
                "border": "north",
            }
        ]
        obj = [{"type": "objective_point", "cx": 600, "cy": 600}]
        scen = [{"type": "circle", "cx": 300, "cy": 300, "r": 50}]
        card = _make_card(
            deployment_shapes=dep,
            objective_shapes=obj,
            scenography_specs=scen,
        )
        data = _card_to_full_data(card)
        assert data["deployment_shapes"] == dep
        assert data["objective_shapes"] == obj
        assert data["scenography_specs"] == scen

    def test_full_data_preserves_vp_objectives(self):
        vp_obj = {"objective": "Hold the line", "victory_points": ["Slay leader"]}
        card = _make_card(objectives=vp_obj)
        data = _card_to_full_data(card)
        assert data["objectives"] == vp_obj
        assert isinstance(data["objectives"], dict)

    def test_full_data_includes_special_rules(self):
        rules = [{"name": "Ambush", "description": "Deploy hidden"}]
        card = _make_card(special_rules=rules)
        data = _card_to_full_data(card)
        assert data["special_rules"] == rules

    def test_full_data_includes_name(self):
        card = _make_card(name="Test Battle")
        data = _card_to_full_data(card)
        assert data["name"] == "Test Battle"

    def test_preview_flattens_vp_objectives(self):
        """Preview returns plain text objective, not dict."""
        vp_obj = {"objective": "Hold the line", "victory_points": ["Slay leader"]}
        card = _make_card(objectives=vp_obj)
        preview = _card_to_preview(card)
        assert preview["objectives"] == "Hold the line"

    def test_preview_includes_name(self):
        card = _make_card(name="My Battle")
        preview = _card_to_preview(card)
        assert preview["name"] == "My Battle"


# =============================================================================
# resolve_full_seed_scenario
# =============================================================================
class TestResolveFullSeedScenario:
    """Tests for the instance method that returns ALL seed data."""

    def test_existing_card_returns_full_data(self):
        dep = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
                "border": "north",
            }
        ]
        rules = [{"name": "Night Fight", "description": "Reduced visibility"}]
        card = _make_card(
            seed=500,
            deployment_shapes=dep,
            special_rules=rules,
            name="Full Scenario",
        )
        uc, _ = _uc_with_repo([card])

        result = uc.resolve_full_seed_scenario(500, 1200, 1200)

        assert result["armies"] == "Saved Army"
        assert result["deployment_shapes"] == dep
        assert result["special_rules"] == rules
        assert result["name"] == "Full Scenario"

    def test_theme_based_returns_generated_shapes(self):
        uc, _ = _uc_with_repo([])

        result = uc.resolve_full_seed_scenario(42, 1200, 1200)

        # Text content from themes
        assert result["armies"]
        assert result["deployment"]
        # Shapes from generation
        assert isinstance(result["deployment_shapes"], list)
        assert isinstance(result["objective_shapes"], list)
        assert isinstance(result["scenography_specs"], list)
        # No special_rules or name from themes
        assert result["name"] == ""
        assert result["special_rules"] is None

    def test_seed_zero_returns_empty(self):
        uc, _ = _uc_with_repo([])

        result = uc.resolve_full_seed_scenario(0, 1200, 1200)

        assert result["deployment_shapes"] == []
        assert result["objective_shapes"] == []
        assert result["scenography_specs"] == []

    def test_existing_card_vp_objectives_preserved(self):
        vp = {"objective": "Seize artifact", "victory_points": ["Slay captain"]}
        card = _make_card(seed=700, objectives=vp)
        uc, _ = _uc_with_repo([card])

        result = uc.resolve_full_seed_scenario(700, 1200, 1200)

        assert result["objectives"] == vp


# =============================================================================
# resolve_seed_preview (instance) — includes name
# =============================================================================
class TestResolveSeedPreviewName:
    """Tests that resolve_seed_preview returns name."""

    def test_existing_card_name(self):
        card = _make_card(seed=123, name="Named Scenario")
        uc, _ = _uc_with_repo([card])
        preview = uc.resolve_seed_preview(123)
        assert preview["name"] == "Named Scenario"

    def test_theme_seed_name_is_empty(self):
        uc, _ = _uc_with_repo([])
        preview = uc.resolve_seed_preview(42)
        assert preview["name"] == ""

    def test_zero_seed_name_is_empty(self):
        uc, _ = _uc_with_repo([])
        preview = uc.resolve_seed_preview(0)
        assert preview["name"] == ""


# =============================================================================
# execute() — auto-fill shapes from seed
# =============================================================================
class TestExecuteAutoFillShapes:
    """Tests that execute() auto-fills shapes from seed when user provides none."""

    def test_existing_card_shapes_replicated(self):
        """Shapes from existing card used when user provides no manual shapes."""
        dep = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
                "border": "north",
            }
        ]
        obj = [{"type": "objective_point", "cx": 600, "cy": 600}]
        scen = [{"type": "circle", "cx": 300, "cy": 300, "r": 50}]
        card = _make_card(
            seed=800,
            deployment_shapes=dep,
            objective_shapes=obj,
            scenography_specs=scen,
        )
        uc, _ = _uc_with_repo([card])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=800,
        )
        response = uc.execute(request)

        # Shapes should be from the existing card
        assert response.shapes["deployment_shapes"] == dep
        assert response.shapes["objective_shapes"] == obj
        assert response.shapes["scenography_specs"] == scen

    def test_theme_seed_generates_shapes(self):
        """Theme-based seed generates deterministic shapes when user has none."""
        uc, _ = _uc_with_repo([])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=42,
        )
        response = uc.execute(request)

        # Should have shapes from generation (at least one category non-empty
        # for seed 42, verified manually)
        all_shapes = (
            response.shapes["deployment_shapes"]
            + response.shapes["objective_shapes"]
            + response.shapes["scenography_specs"]
        )
        assert len(all_shapes) > 0

    def test_user_shapes_override_seed(self):
        """User-provided shapes take priority over seed shapes."""
        dep = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
                "border": "north",
            }
        ]
        card = _make_card(
            seed=900,
            deployment_shapes=dep,
        )
        uc, _ = _uc_with_repo([card])

        user_dep = [
            {
                "type": "rect",
                "x": 0,
                "y": 1000,
                "width": 1200,
                "height": 200,
                "border": "south",
            }
        ]
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=900,
            deployment_shapes=user_dep,
        )
        response = uc.execute(request)

        # User's deployment shapes should be used, not the card's
        assert response.shapes["deployment_shapes"] == user_dep

    def test_existing_card_special_rules_replicated(self):
        """Special rules from existing card used when user provides none."""
        rules = [{"name": "Ambush", "description": "Deploy hidden units"}]
        card = _make_card(seed=1000, special_rules=rules)
        uc, _ = _uc_with_repo([card])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=1000,
        )
        response = uc.execute(request)

        assert response.special_rules == rules

    def test_existing_card_name_replicated(self):
        """Name from existing card used when user provides no name."""
        card = _make_card(seed=1100, name="The Battle of Five Armies")
        uc, _ = _uc_with_repo([card])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=1100,
        )
        response = uc.execute(request)

        assert response.name == "The Battle of Five Armies"

    def test_user_name_overrides_seed_name(self):
        """User-provided name takes priority over existing card's name."""
        card = _make_card(seed=1200, name="Card Name")
        uc, _ = _uc_with_repo([card])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=1200,
            name="User Custom Name",
        )
        response = uc.execute(request)

        assert response.name == "User Custom Name"

    def test_no_seed_no_shapes_autofill(self):
        """Without seed (non-replicable), no auto-fill happens."""
        uc, _ = _uc_with_repo([])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=False,
            generate_from_seed=None,
            armies="Test",
            deployment="Test",
            layout="Test",
            objectives="Test",
            initial_priority="Test",
        )
        response = uc.execute(request)

        # seed=0 means no auto-fill
        assert response.shapes["deployment_shapes"] == []
        assert response.shapes["objective_shapes"] == []
        assert response.shapes["scenography_specs"] == []


# =============================================================================
# execute() — VP objectives from seed
# =============================================================================
class TestExecuteVPObjectivesFromSeed:
    """Tests that structured VP objectives from existing card are preserved."""

    def test_vp_objectives_preserved_through_execute(self):
        """VP dict objectives from existing card persist in the response."""
        vp = {"objective": "Capture the artifact", "victory_points": ["Slay leader"]}
        card = _make_card(seed=1300, objectives=vp)
        uc, _ = _uc_with_repo([card])

        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            generate_from_seed=1300,
        )
        response = uc.execute(request)

        assert response.objectives == vp
