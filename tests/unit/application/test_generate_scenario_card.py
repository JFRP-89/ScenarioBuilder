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
    """Happy path: preset 'standard' + explicit seed + mode enum + visibility None."""

    def test_generates_card_with_explicit_seed_and_mode_enum(
        self,
        use_case: GenerateScenarioCard,
        spy_scenario_generator: SpyScenarioGenerator,
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        response = use_case.execute(request)

        # Response shape
        assert response.card_id == "card-001"
        assert response.owner_id == "user-123"
        assert response.seed == 42
        assert response.mode == "matched"
        assert response.visibility == "private"  # default when None
        assert response.table_mm == {"width_mm": 1200, "height_mm": 1200}
        assert response.name == "Battle Scenario"
        assert response.initial_priority == "Check the rulebook rules for it"
        # shapes is a dict with deployment_shapes, objective_shapes, and scenography_specs
        assert isinstance(response.shapes, dict)
        assert "deployment_shapes" in response.shapes
        assert "objective_shapes" in response.shapes
        assert "scenography_specs" in response.shapes
        # scenography_specs is empty when not provided by user
        scenography_specs = response.shapes["scenography_specs"]
        assert len(scenography_specs) == 0
        assert scenography_specs == []

        # ScenarioGenerator was called correctly
        assert len(spy_scenario_generator.calls) == 1
        call_seed, call_table, call_mode = spy_scenario_generator.calls[0]
        assert call_seed == 42
        assert call_table.width_mm == 1200
        assert call_table.height_mm == 1200
        assert call_mode == GameMode.MATCHED


# =============================================================================
# 2) SEED GENERATION
# =============================================================================
class TestSeedGeneration:
    """Seed None uses SeedGenerator port."""

    def test_uses_seed_generator_when_seed_is_none(
        self,
        use_case: GenerateScenarioCard,
        spy_scenario_generator: SpyScenarioGenerator,
        fake_seed_generator: FakeSeedGenerator,
    ):
        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.CASUAL,
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        response = use_case.execute(request)

        # Seed comes from FakeSeedGenerator
        assert response.seed == 999
        # SeedGenerator was called exactly once
        assert fake_seed_generator.calls == 1
        # ScenarioGenerator receives generated seed
        assert spy_scenario_generator.calls[0][0] == 999


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
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        response = use_case.execute(request)

        # Response mode is serialized
        assert response.mode == expected_mode.value
        # ScenarioGenerator receives parsed enum
        assert spy_scenario_generator.calls[0][2] == expected_mode


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
# 8) GENERATOR SHAPES ARE NOT USED AS FALLBACK
# =============================================================================
class TestGeneratorShapesNotUsedAsFallback:
    """Generator shapes are not injected into the card when user provides none.

    The use case no longer uses generator shapes as fallback for scenography.
    Even if the generator returns invalid shapes, the card is still created
    successfully with empty scenography.
    """

    def test_invalid_generator_shapes_ignored_when_user_provides_none(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
    ):
        # Shape outside table bounds — would fail if used
        invalid_shapes = [{"type": "circle", "cx": 1150, "cy": 600, "r": 100}]
        bad_generator = SpyScenarioGenerator(shapes=invalid_shapes)
        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=bad_generator,
        )

        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        # Should succeed — generator shapes are not used
        response = use_case.execute(request)
        assert response.card_id == "card-001"
        # scenography is empty (not from generator)
        assert response.shapes["scenography_specs"] == []


# =============================================================================
# 9) CONTRACT ENFORCEMENT
# =============================================================================
class TestScenarioGeneratorContractEnforcement:
    """Contract enforcement: Use case rejects dict return from generator."""

    def test_generator_returning_dict_raises_contract_violation(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
    ):
        """Generator returning dict instead of list[dict] raises ValidationError.

        This enforces the ScenarioGenerator contract at use case level.
        Even if a generator implementation incorrectly returns a dict
        (e.g., {"deployment_shapes": [...]}), the use case must reject it.
        """

        # Arrange - generator that violates contract by returning dict
        @dataclass
        class BadGenerator:
            """Generator that violates contract by returning dict."""

            def generate_shapes(
                self, seed: int, table: TableSize, mode: GameMode
            ) -> dict:
                # Contract violation: returning dict instead of list[dict]
                return {
                    "deployment_shapes": [
                        {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
                    ],
                    "scenography_specs": [],
                }

        bad_generator = BadGenerator()
        use_case = GenerateScenarioCard(
            id_generator=fake_id_generator,
            seed_generator=fake_seed_generator,
            scenario_generator=bad_generator,
        )

        request = GenerateScenarioCardRequest(
            actor_id="user-123",
            mode=GameMode.MATCHED,
            seed=42,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        # Act & Assert - contract violation detected
        with pytest.raises(ValidationError, match="(?i)contract.*violation.*list"):
            use_case.execute(request)


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
# TODO(future): Additional tests for hardening phase:
# - Verify Card entity is correctly constructed internally
# - Test shared_with validation when visibility=SHARED
# - Test massive table preset
# - Test concurrent ID generation
# - Test response serialization edge cases
# =============================================================================
