"""
RED tests for GenerateScenarioCard use case.

This use case generates a new ScenarioCard by:
1. Accepting request DTO with actor, mode, seed, table preset, visibility
2. Generating unique card_id via IdGenerator port
3. Generating seed via SeedGenerator if not provided
4. Building TableSize from preset
5. Generating shapes via ScenarioGenerator port
6. Returning response DTO with serialized data

MVP Contract (8 test cases):
1. Happy path: preset "standard" + explicit seed + mode enum + visibility None
2. Seed None uses SeedGenerator
3. Invalid preset → ValidationError
4. Invalid actor_id → ValidationError (parametrized: "", "   ", None)
5. Mode as string parsed with parse_game_mode
6. Visibility as string parsed with parse_visibility
7. Invalid visibility → ValidationError
8. ScenarioGenerator returns invalid shape → ValidationError
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest

# Application layer imports (will fail - RED phase)
from application.use_cases.generate_scenario_card import (
    GenerateScenarioCard,
    GenerateScenarioCardRequest,
)

# Domain imports
from domain.cards.card import GameMode
from domain.errors import ValidationError
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility


# =============================================================================
# TEST DOUBLES
# =============================================================================
class FakeIdGenerator:
    """Fake IdGenerator that returns predictable IDs."""

    def __init__(self, card_id: str = "card-001") -> None:
        self._card_id = card_id

    def generate_card_id(self) -> str:
        return self._card_id


class FakeSeedGenerator:
    """Fake SeedGenerator that returns predictable seeds."""

    def __init__(self, seed: int = 999) -> None:
        self._seed = seed
        self.calls = 0

    def generate_seed(self) -> int:
        self.calls += 1
        return self._seed


@dataclass
class SpyScenarioGenerator:
    """Spy ScenarioGenerator that records calls and returns configurable shapes."""

    shapes: list[dict]
    calls: list[tuple[int, TableSize, GameMode]] = field(default_factory=list)

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        self.calls.append((seed, table, mode))
        return self.shapes


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def fake_id_generator() -> FakeIdGenerator:
    return FakeIdGenerator(card_id="card-001")


@pytest.fixture
def fake_seed_generator() -> FakeSeedGenerator:
    return FakeSeedGenerator(seed=999)


@pytest.fixture
def valid_shapes() -> list[dict]:
    """Shapes that are valid for standard table (1200x1200 mm)."""
    return [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]


@pytest.fixture
def spy_scenario_generator(valid_shapes: list[dict]) -> SpyScenarioGenerator:
    return SpyScenarioGenerator(shapes=valid_shapes)


@pytest.fixture
def use_case(
    fake_id_generator: FakeIdGenerator,
    fake_seed_generator: FakeSeedGenerator,
    spy_scenario_generator: SpyScenarioGenerator,
) -> GenerateScenarioCard:
    return GenerateScenarioCard(
        id_generator=fake_id_generator,
        seed_generator=fake_seed_generator,
        scenario_generator=spy_scenario_generator,
    )


# =============================================================================
# 1) HAPPY PATH
# =============================================================================
class TestHappyPath:
    """Happy path: replicable scenario with deterministic seed."""

    def test_generates_card_with_explicit_seed_and_mode_enum(
        self,
        use_case: GenerateScenarioCard,
        spy_scenario_generator: SpyScenarioGenerator,
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=None,  # Irrelevant with is_replicable=True
            table_preset="standard",
            visibility=None,
            shared_with=None,
            armies="Rohan",
            deployment="Test Deployment",
            is_replicable=True,  # Use deterministic seed
        )

        response = use_case.execute(request)

        # Response shape
        assert response.card_id == "card-001"
        assert response.owner_id == "user-123"
        assert response.seed > 0  # Deterministic seed, not 0
        assert response.mode == "matched"
        assert response.visibility == "private"  # default when None
        assert response.table_mm == {"width_mm": 1200, "height_mm": 1200}
        assert response.name == "Battle with Test Deployment"
        assert response.initial_priority == "Check the rulebook rules for it"
        # shapes is a dict with deployment_shapes, objective_shapes, and scenography_specs
        assert isinstance(response.shapes, dict)
        assert "deployment_shapes" in response.shapes
        assert "objective_shapes" in response.shapes
        assert "scenography_specs" in response.shapes
        # scenography_specs contains generated shapes (seed > 0)
        scenography_specs = response.shapes["scenography_specs"]
        assert len(scenography_specs) == 0  # shapes no longer auto-generated

        # ScenarioGenerator is no longer called for shape generation
        assert len(spy_scenario_generator.calls) == 0


# =============================================================================
# 2) SEED RESOLUTION
# =============================================================================
class TestSeedResolution:
    """Test seed resolution logic: is_replicable determines seed strategy."""

    def test_is_replicable_false_gives_seed_zero(
        self,
        use_case: GenerateScenarioCard,
        spy_scenario_generator: SpyScenarioGenerator,
    ):
        """When is_replicable=False, seed=0 (manual scenario, no generation)."""
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.CASUAL,
            seed=None,  # Irrelevant when is_replicable=False
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=False,
        )

        response = use_case.execute(request)

        # Seed is always 0 for manual scenarios
        assert response.seed == 0
        # ScenarioGenerator was NOT called (manual scenario)
        assert len(spy_scenario_generator.calls) == 0

    def test_is_replicable_none_defaults_to_manual(
        self,
        use_case: GenerateScenarioCard,
        spy_scenario_generator: SpyScenarioGenerator,
    ):
        """When is_replicable=None (default), defaults to manual (seed=0)."""
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.CASUAL,
            seed=999,  # Irrelevant when is_replicable=None
            table_preset="standard",
            visibility=None,
            shared_with=None,
            # is_replicable not set → defaults to None → manual
        )

        response = use_case.execute(request)

        # Seed is 0 (manual)
        assert response.seed == 0
        # ScenarioGenerator was NOT called
        assert len(spy_scenario_generator.calls) == 0


# =============================================================================
# 3) INVALID PRESET
# =============================================================================
class TestInvalidPreset:
    """Invalid table preset raises ValidationError."""

    def test_invalid_preset_raises_validation_error(
        self, use_case: GenerateScenarioCard
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="nonexistent",
            visibility=None,
            shared_with=None,
        )

        with pytest.raises(ValidationError, match="(?i)preset|table"):
            use_case.execute(request)


# =============================================================================
# 4) INVALID ACTOR_ID
# =============================================================================
class TestInvalidActorId:
    """Invalid actor_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_actor_id",
        [
            "",
            "   ",
            None,
        ],
        ids=["empty", "whitespace", "none"],
    )
    def test_invalid_actor_id_raises_validation_error(
        self, use_case: GenerateScenarioCard, invalid_actor_id: Optional[str]
    ):
        request = GenerateScenarioCardRequest(
            actor_id=invalid_actor_id,
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)


# =============================================================================
# 5) MODE AS STRING
# =============================================================================
class TestModeAsString:
    """Mode as string is parsed with parse_game_mode."""

    @pytest.mark.parametrize(
        "mode_str,expected_mode",
        [
            ("matched", GameMode.MATCHED),
            ("MATCHED", GameMode.MATCHED),
            ("  Matched  ", GameMode.MATCHED),
            ("casual", GameMode.CASUAL),
            ("narrative", GameMode.NARRATIVE),
        ],
    )
    def test_mode_string_is_parsed(
        self,
        use_case: GenerateScenarioCard,
        spy_scenario_generator: SpyScenarioGenerator,
        mode_str: str,
        expected_mode: GameMode,
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=mode_str,
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,  # Use deterministic seed
            armies="Test",
        )

        response = use_case.execute(request)

        # Response mode is serialized
        assert response.mode == expected_mode.value


# =============================================================================
# 6) VISIBILITY AS STRING
# =============================================================================
class TestVisibilityAsString:
    """Visibility as string is parsed with parse_visibility."""

    @pytest.mark.parametrize(
        "visibility_str,expected_visibility",
        [
            ("private", Visibility.PRIVATE),
            ("PUBLIC", Visibility.PUBLIC),
            ("  Shared  ", Visibility.SHARED),
        ],
    )
    def test_visibility_string_is_parsed(
        self,
        use_case: GenerateScenarioCard,
        visibility_str: str,
        expected_visibility: Visibility,
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=visibility_str,
            shared_with=(
                ["user-456"] if expected_visibility == Visibility.SHARED else None
            ),
        )

        response = use_case.execute(request)

        assert response.visibility == expected_visibility.value


# =============================================================================
# 7) INVALID VISIBILITY
# =============================================================================
class TestInvalidVisibility:
    """Invalid visibility string raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_visibility",
        ["secret", "hidden", "unlisted", "", "   "],
    )
    def test_invalid_visibility_raises_validation_error(
        self, use_case: GenerateScenarioCard, invalid_visibility: str
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=invalid_visibility,
            shared_with=None,
        )

        with pytest.raises(ValidationError, match="(?i)visibility"):
            use_case.execute(request)


# =============================================================================
# 8) GENERATOR SHAPES USED WITH seed >= 1
# =============================================================================
class TestGeneratorShapesUsedWithSeedGreaterThanZero:
    """Generator shapes are used when seed >= 1 and user provides no scenography.

    NEW behavior with seed convention:
    - seed=0: manual scenario, generator not called, shapes empty
    - seed>=1: generated scenario, if user provides no scenography, use generator shapes
    """

    def test_generator_shapes_used_when_seed_greater_than_zero(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        # Valid shapes that fit the table
        spy_generator = SpyScenarioGenerator(shapes=valid_shapes)
        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=spy_generator,
        )

        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,  # seed > 0 → use generator shapes
            armies="Test",
        )

        response = use_case.execute(request)
        assert response.card_id == "card-001"
        # scenography no longer contains auto-generated shapes
        assert len(response.shapes["scenography_specs"]) == 0

    def test_user_scenography_takes_priority_over_generator(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        # Even with seed >= 1 and generator returning shapes,
        # if user provides scenography_specs, user shapes take priority
        spy_generator = SpyScenarioGenerator(shapes=valid_shapes)
        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=spy_generator,
        )

        user_shapes = [
            {"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}
        ]
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            scenography_specs=user_shapes,  # User provides shapes explicitly
        )

        response = use_case.execute(request)
        # User shapes should be used, not generator shapes
        assert len(response.shapes["scenography_specs"]) == 1
        assert response.shapes["scenography_specs"][0]["type"] == "rect"


# =============================================================================
# OBJECTIVE_SHAPES VALIDATION
# =============================================================================
class TestObjectiveShapesValidation:
    """Test that objective_shapes from request are validated."""

    def test_objective_shapes_out_of_bounds_raises_validation_error(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        """Use case rejects objective_shapes with coordinates outside table bounds."""
        # Generator returns valid shapes (list[dict])
        generator = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # Request includes objective_shapes out of bounds
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objective_shapes=[
                {"cx": 2000, "cy": 600},  # cx=2000 > standard table width (1200mm)
            ],
        )

        # Act & Assert - validation catches out-of-bounds objective_shapes
        with pytest.raises(ValidationError, match="(?i)out of bounds"):
            use_case.execute(request)

    def test_too_many_objective_shapes_raises_validation_error(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        """Use case rejects more than 10 objective_shapes."""
        # Generator returns valid shapes (list[dict])
        generator = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # Request includes 11 objective_shapes (exceeds max of 10)
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objective_shapes=[{"cx": 100 + i * 50, "cy": 100} for i in range(11)],
        )

        # Act & Assert - validation catches too many objective_shapes
        with pytest.raises(ValidationError, match="(?i)too many objective points"):
            use_case.execute(request)


# =============================================================================
# POST-MERGE SHAPES VALIDATION
# =============================================================================
class TestPostMergeShapesValidation:
    """Test that final merged shapes (user + generated) are validated."""

    def test_valid_user_map_specs_plus_generated_shapes_succeeds(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        """User-provided map_specs + generated shapes both valid => OK."""
        generator = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # Request with valid map_specs (scenography)
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            map_specs=[
                {
                    "type": "circle",
                    "cx": 300,
                    "cy": 300,
                    "r": 50,
                }
            ],  # Valid scenography
        )

        # Act - should succeed (both user + generated shapes are valid)
        response = use_case.execute(request)

        # Assert
        assert response.card_id == "card-001"
        assert "scenography_specs" in response.shapes
        assert len(response.shapes["scenography_specs"]) == 1

    def test_user_map_specs_out_of_bounds_fails_post_merge(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        """User map_specs out of bounds => FAIL in post-merge validation."""
        generator = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # Request with invalid map_specs (out of bounds)
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            map_specs=[
                {
                    "type": "circle",
                    "cx": 2000,  # cx=2000 > standard table width (1200mm)
                    "cy": 300,
                    "r": 50,
                }
            ],
        )

        # Act & Assert - validation catches out-of-bounds
        with pytest.raises(
            ValidationError,
            match="(?i)out of bounds",
        ):
            use_case.execute(request)

    def test_too_many_total_shapes_fails_post_merge(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
    ):
        """User scenography_specs exceed max (100) => FAIL."""
        # Generator returns valid shapes (not relevant as user provides scenography)
        valid_shape = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
        generator = SpyScenarioGenerator(shapes=valid_shape)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # User provides 101 scenography specs (exceeds max of 100)
        user_scenography = [
            {"type": "circle", "cx": 100 + i * 10, "cy": 600, "r": 5}
            for i in range(101)
        ]

        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            scenography_specs=user_scenography,
        )

        # Act & Assert - validation catches too many shapes
        with pytest.raises(ValidationError, match="(?i)too many"):
            use_case.execute(request)

    def test_valid_deployment_shapes_plus_generated_succeeds(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        """User-provided deployment_shapes + generated shapes both valid => OK."""
        generator = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # Request with valid deployment_shapes
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            deployment_shapes=[
                {
                    "type": "rect",
                    "border": "north",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 100,
                }
            ],
        )

        # Act - should succeed
        response = use_case.execute(request)

        # Assert
        assert response.card_id == "card-001"
        assert "deployment_shapes" in response.shapes

    def test_user_deployment_shapes_out_of_bounds_fails_post_merge(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
        valid_shapes: list[dict],
    ):
        """User deployment_shapes out of bounds => FAIL."""
        generator = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=generator,
        )

        # Request with invalid deployment_shapes (rect extends beyond table)
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            deployment_shapes=[
                {
                    "type": "rect",
                    "border": "north",
                    "x": 1100,
                    "y": 0,
                    "width": 200,  # x + width = 1300 > 1200mm
                    "height": 100,
                }
            ],
        )

        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="(?i)out of bounds",
        ):
            use_case.execute(request)


# =============================================================================
# REPLICABLE SEED TESTS
# =============================================================================
class TestReplicableSeed:
    """Test deterministic seed calculation for replicable scenarios."""

    def test_replicable_true_uses_deterministic_seed(self):
        """When is_replicable=True, seed is deterministic based on config."""
        id_gen = FakeIdGenerator("card-001")
        seed_gen = FakeSeedGenerator()
        valid_shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
        scenario_gen = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(id_gen, seed_gen, scenario_gen)

        request = GenerateScenarioCardRequest(
            actor_id="actor-001",
            mode=GameMode.MATCHED,
            seed=None,  # Irrelevant when is_replicable=True
            table_preset="standard",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            armies="Rohan",
            deployment="deployment-name",
            layout="layout-name",
            is_replicable=True,  # Use deterministic seed
        )

        response = use_case.execute(request)

        # Seed should be deterministically calculated (not 999 from SeedGenerator)
        assert response.seed > 0  # Deterministic seed is non-zero
        assert response.seed != 999  # Not from SeedGenerator

        # Run again with same config → same seed
        response2 = use_case.execute(request)
        assert response.seed == response2.seed

    def test_replicable_false_gives_seed_zero(self):
        """When is_replicable=False, seed is always 0 (manual scenario)."""
        id_gen = FakeIdGenerator("card-001")
        seed_gen = FakeSeedGenerator()
        valid_shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
        scenario_gen = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(id_gen, seed_gen, scenario_gen)

        request = GenerateScenarioCardRequest(
            actor_id="actor-001",
            mode=GameMode.MATCHED,
            seed=12345,  # Irrelevant when is_replicable=False
            table_preset="standard",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            is_replicable=False,
        )

        response = use_case.execute(request)
        # Seed is always 0 for manual scenarios
        assert response.seed == 0
        # No shapes generated
        assert len(scenario_gen.calls) == 0

    def test_replicable_true_same_config_same_seed(self):
        """Same config with is_replicable=True always produces same seed."""
        id_gen = FakeIdGenerator("card-001")
        seed_gen = FakeSeedGenerator()
        valid_shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
        scenario_gen = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(id_gen, seed_gen, scenario_gen)

        request = GenerateScenarioCardRequest(
            actor_id="actor-001",
            mode="MATCHED",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            armies="Rohan",
            deployment="deployment-name",
            layout="layout-name",
            objectives="objective-1",
            is_replicable=True,
        )

        response1 = use_case.execute(request)
        response2 = use_case.execute(request)

        assert response1.seed == response2.seed

    def test_replicable_true_different_config_different_seed(self):
        """Different config with is_replicable=True produces different seed."""
        id_gen = FakeIdGenerator("card-001")
        seed_gen = FakeSeedGenerator()
        valid_shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
        scenario_gen = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(id_gen, seed_gen, scenario_gen)

        request1 = GenerateScenarioCardRequest(
            actor_id="actor-001",
            mode="MATCHED",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            armies="Rohan",
            deployment="deployment-1",
            is_replicable=True,
        )

        request2 = GenerateScenarioCardRequest(
            actor_id="actor-001",
            mode="MATCHED",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            armies="Rohan",
            deployment="deployment-2",  # Different deployment
            is_replicable=True,
        )

        response1 = use_case.execute(request1)
        response2 = use_case.execute(request2)

        assert response1.seed != response2.seed  # Different config → different seed

    def test_replicable_none_defaults_to_manual(self):
        """When is_replicable is None, defaults to manual (seed=0)."""
        id_gen = FakeIdGenerator("card-001")
        seed_gen = FakeSeedGenerator(seed=999)
        valid_shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
        scenario_gen = SpyScenarioGenerator(shapes=valid_shapes)

        use_case = GenerateScenarioCard(id_gen, seed_gen, scenario_gen)

        request = GenerateScenarioCardRequest(
            actor_id="actor-001",
            mode=GameMode.MATCHED,
            seed=None,
            table_preset="standard",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            is_replicable=None,  # Default behavior
        )

        response = use_case.execute(request)
        # Should be 0 (manual), not SeedGenerator's 999
        assert response.seed == 0
        # No generation
        assert len(scenario_gen.calls) == 0


# =============================================================================
# - Test concurrent ID generation
# - Test response serialization edge cases
# =============================================================================
