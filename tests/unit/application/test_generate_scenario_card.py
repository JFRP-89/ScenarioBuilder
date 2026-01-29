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

from dataclasses import dataclass
from typing import Optional

import pytest

# Domain imports
from domain.cards.card import GameMode
from domain.errors import ValidationError
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility

# Application layer imports (will fail - RED phase)
from application.use_cases.generate_scenario_card import (
    GenerateScenarioCard,
    GenerateScenarioCardRequest,
)


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
    calls: list[tuple[int, TableSize, GameMode]] = None

    def __post_init__(self) -> None:
        self.calls = []

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
        assert len(response.shapes) == 1
        assert response.shapes[0]["type"] == "circle"

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
# 8) INVALID SHAPES FROM GENERATOR
# =============================================================================
class TestInvalidShapesFromGenerator:
    """ScenarioGenerator returns invalid shape → ValidationError."""

    def test_invalid_shape_raises_validation_error(
        self,
        fake_id_generator: FakeIdGenerator,
        fake_seed_generator: FakeSeedGenerator,
    ):
        # Shape outside table bounds (cx + r > 1200)
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

        with pytest.raises(ValidationError, match="(?i)shape|bounds|map"):
            use_case.execute(request)


# =============================================================================
# TODO(future): Additional tests for hardening phase:
# - Verify Card entity is correctly constructed internally
# - Test shared_with validation when visibility=SHARED
# - Test massive table preset
# - Test concurrent ID generation
# - Test response serialization edge cases
# =============================================================================
