"""RED tests for CreateVariant use case.

CreateVariant creates a new card derived from an existing one:
- Only owner of base card can create variant (security)
- Variant inherits mode, table, visibility, shared_with from base
- New owner_id = actor_id
- Seed can be explicit or generated via SeedGenerator
"""

from __future__ import annotations

from typing import Optional

import pytest
from domain.cards.card import Card, GameMode, Visibility
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize


# =============================================================================
# TEST HELPERS
# =============================================================================
def make_valid_shapes() -> list[dict]:
    """Return shapes valid for TableSize.standard()."""
    return [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]


def make_valid_card(
    card_id: str = "card-base-001",
    owner_id: str = "u1",
    visibility: Visibility = Visibility.PRIVATE,
    shared_with: Optional[frozenset[str]] = None,
    mode: GameMode = GameMode.MATCHED,
    seed: int = 123,
) -> Card:
    """Create a valid Card for testing."""
    table = TableSize.standard()
    shapes = make_valid_shapes()
    map_spec = MapSpec(table=table, shapes=shapes)
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=shared_with or frozenset(),
        mode=mode,
        seed=seed,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# FAKE REPOSITORIES AND GENERATORS
# =============================================================================
class FakeCardRepository:
    """In-memory card repository for testing."""

    def __init__(self) -> None:
        self._cards: dict[str, Card] = {}
        self.save_calls: list[Card] = []

    def add(self, card: Card) -> None:
        """Pre-populate repository with a card."""
        self._cards[card.card_id] = card

    def get_by_id(self, card_id: str) -> Optional[Card]:
        """Get card by id."""
        return self._cards.get(card_id)

    def save(self, card: Card) -> None:
        """Save card to repository."""
        self.save_calls.append(card)
        self._cards[card.card_id] = card

    def find_by_seed(self, seed: int) -> Optional[Card]:
        return next((c for c in self._cards.values() if c.seed == seed), None)

    def delete(self, card_id: str) -> bool:
        return self._cards.pop(card_id, None) is not None

    def list_all(self) -> list[Card]:
        return list(self._cards.values())

    def list_for_owner(self, owner_id: str) -> list[Card]:
        return [c for c in self._cards.values() if c.owner_id == owner_id]


class FakeIdGenerator:
    """Fake id generator that returns predictable ids."""

    def __init__(self, card_id: str = "card-variant-001") -> None:
        self._card_id = card_id

    def generate_card_id(self) -> str:
        """Generate a card id."""
        return self._card_id


class FakeSeedGenerator:
    """Fake seed generator with call tracking."""

    def __init__(self, seed: int = 999) -> None:
        self._seed = seed
        self.calls = 0

    def generate_seed(self) -> int:
        """Generate a seed."""
        self.calls += 1
        return self._seed

    def calculate_from_config(self, config: dict) -> int:
        return self._seed


class SpyScenarioGenerator:
    """Spy scenario generator that tracks calls and returns configurable shapes."""

    def __init__(self, shapes: Optional[list[dict]] = None) -> None:
        self._shapes = shapes if shapes is not None else make_valid_shapes()
        self.calls: list[tuple[int, TableSize, GameMode]] = []

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        """Generate shapes and record the call."""
        self.calls.append((seed, table, mode))
        return self._shapes


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def repo() -> FakeCardRepository:
    """Provide empty card repository."""
    return FakeCardRepository()


@pytest.fixture
def id_gen() -> FakeIdGenerator:
    """Provide fake id generator."""
    return FakeIdGenerator("card-variant-001")


@pytest.fixture
def seed_gen() -> FakeSeedGenerator:
    """Provide fake seed generator."""
    return FakeSeedGenerator(999)


@pytest.fixture
def scenario_gen() -> SpyScenarioGenerator:
    """Provide spy scenario generator with valid shapes."""
    return SpyScenarioGenerator()


# =============================================================================
# HAPPY PATH TESTS
# =============================================================================
class TestCreateVariantHappyPath:
    """Tests for successful variant creation."""

    def test_owner_creates_variant_with_explicit_seed(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """Owner creates variant with explicit seed."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange
        base = make_valid_card(
            card_id="card-base-001",
            owner_id="u1",
            visibility=Visibility.PUBLIC,
            mode=GameMode.MATCHED,
            seed=123,
        )
        repo.add(base)

        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id="card-base-001",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act
        response = use_case.execute(request)

        # Assert response
        assert response.card_id == "card-variant-001"
        assert response.owner_id == "u1"
        assert response.seed == 555
        assert response.mode == base.mode.value
        assert response.visibility == base.visibility.value

        # Assert scenario_gen was called with correct params
        assert len(scenario_gen.calls) == 1
        call_seed, call_table, call_mode = scenario_gen.calls[0]
        assert call_seed == 555
        assert call_table == base.table
        assert call_mode == base.mode

        # Assert card was saved
        assert len(repo.save_calls) == 1
        saved_card = repo.save_calls[0]
        assert saved_card.card_id == "card-variant-001"
        assert repo.get_by_id("card-variant-001") is not None

    def test_variant_inherits_visibility_and_shared_with_from_base(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """Variant inherits visibility and shared_with from base card."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange
        base = make_valid_card(
            card_id="card-base-001",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u2", "u3"}),
        )
        repo.add(base)

        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id="card-base-001",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act
        response = use_case.execute(request)

        # Assert visibility inherited
        assert response.visibility == Visibility.SHARED.value

        # Assert shared_with inherited in saved card
        saved_card = repo.save_calls[0]
        assert saved_card.shared_with == frozenset({"u2", "u3"})


class TestCreateVariantSeedGeneration:
    """Tests for seed generation behavior."""

    def test_seed_none_uses_seed_generator(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """When seed is None, SeedGenerator is called."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange
        base = make_valid_card(card_id="card-base-001", owner_id="u1")
        repo.add(base)

        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id="card-base-001",
            seed=None,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act
        response = use_case.execute(request)

        # Assert seed_gen was called
        assert seed_gen.calls == 1
        assert response.seed == 999

        # Assert scenario_gen received the generated seed
        call_seed, _, _ = scenario_gen.calls[0]
        assert call_seed == 999

    def test_explicit_seed_does_not_call_seed_generator(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """When seed is explicit, SeedGenerator is NOT called."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange
        base = make_valid_card(card_id="card-base-001", owner_id="u1")
        repo.add(base)

        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id="card-base-001",
            seed=777,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act
        use_case.execute(request)

        # Assert seed_gen was NOT called
        assert seed_gen.calls == 0


# =============================================================================
# NOT FOUND TESTS
# =============================================================================
class TestCreateVariantNotFound:
    """Tests for base card not found."""

    def test_base_card_not_found_raises_error(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """Error when base card does not exist."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange: repo is empty
        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id="nonexistent-card",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act & Assert
        with pytest.raises(Exception, match=r"(?i)not found|does not exist"):
            use_case.execute(request)


# =============================================================================
# FORBIDDEN TESTS
# =============================================================================
class TestCreateVariantForbidden:
    """Tests for authorization failures."""

    def test_non_owner_cannot_create_variant(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """Actor who is not owner of base card gets forbidden error."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange: base owned by u1
        base = make_valid_card(card_id="card-base-001", owner_id="u1")
        repo.add(base)

        # Actor is u2 (not owner)
        request = CreateVariantRequest(
            actor_id="u2",
            base_card_id="card-base-001",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act & Assert
        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        # Assert repo.save was NOT called
        assert len(repo.save_calls) == 0

    def test_shared_user_cannot_create_variant(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """User with shared access (read-only) cannot create variant."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange: base owned by u1, shared with u2
        base = make_valid_card(
            card_id="card-base-001",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u2"}),
        )
        repo.add(base)

        # Actor is u2 (shared, but not owner)
        request = CreateVariantRequest(
            actor_id="u2",
            base_card_id="card-base-001",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act & Assert
        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        assert len(repo.save_calls) == 0


# =============================================================================
# VALIDATION ERROR TESTS
# =============================================================================
class TestCreateVariantInvalidActorId:
    """Tests for invalid actor_id validation."""

    @pytest.mark.parametrize("invalid_actor_id", [None, "", "   "])
    def test_invalid_actor_id_raises_validation_error(
        self,
        invalid_actor_id,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """Invalid actor_id raises ValidationError."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange
        base = make_valid_card(card_id="card-base-001", owner_id="u1")
        repo.add(base)

        request = CreateVariantRequest(
            actor_id=invalid_actor_id,
            base_card_id="card-base-001",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act & Assert
        with pytest.raises(ValidationError, match=r"(?i)actor"):
            use_case.execute(request)


class TestCreateVariantInvalidBaseCardId:
    """Tests for invalid base_card_id validation."""

    @pytest.mark.parametrize("invalid_card_id", [None, "", "   "])
    def test_invalid_base_card_id_raises_validation_error(
        self,
        invalid_card_id,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
        scenario_gen: SpyScenarioGenerator,
    ) -> None:
        """Invalid base_card_id raises ValidationError."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id=invalid_card_id,
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act & Assert
        with pytest.raises(ValidationError, match=r"(?i)card"):
            use_case.execute(request)


# =============================================================================
# SCENARIO GENERATOR VALIDATION TESTS
# =============================================================================
class TestCreateVariantInvalidShapes:
    """Tests for invalid shapes from ScenarioGenerator."""

    def test_invalid_shapes_raises_validation_error(
        self,
        repo: FakeCardRepository,
        id_gen: FakeIdGenerator,
        seed_gen: FakeSeedGenerator,
    ) -> None:
        """ScenarioGenerator returning invalid shapes raises ValidationError."""
        from application.use_cases.create_variant import (
            CreateVariant,
            CreateVariantRequest,
        )

        # Arrange: shapes outside bounds for standard table (1100x700)
        invalid_shapes = [
            {"type": "rect", "x": 2000, "y": 2000, "width": 200, "height": 200}
        ]
        scenario_gen = SpyScenarioGenerator(shapes=invalid_shapes)

        base = make_valid_card(card_id="card-base-001", owner_id="u1")
        repo.add(base)

        request = CreateVariantRequest(
            actor_id="u1",
            base_card_id="card-base-001",
            seed=555,
        )

        use_case = CreateVariant(
            repository=repo,
            id_generator=id_gen,
            seed_generator=seed_gen,
            scenario_generator=scenario_gen,
        )

        # Act & Assert
        with pytest.raises(ValidationError, match=r"(?i)shape|bounds|map"):
            use_case.execute(request)

        # Assert card was NOT saved
        assert len(repo.save_calls) == 0
