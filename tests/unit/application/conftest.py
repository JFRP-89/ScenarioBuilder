"""Shared fixtures for application use-case tests.

Test doubles and fixtures live here so that test methods can use
fixture injection without shadowing module-level names (Pylint W0621).
"""

from __future__ import annotations

from typing import Optional

import pytest

from application.use_cases.generate_scenario_card import GenerateScenarioCard
from domain.cards.card import Card, GameMode
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


# =============================================================================
# TEST DOUBLES (shared)
# =============================================================================
class FakeIdGenerator:
    """Fake IdGenerator that returns predictable IDs."""

    def __init__(self, card_id: str = "card-001") -> None:
        self._card_id = card_id

    def __repr__(self) -> str:
        return f"FakeIdGenerator(card_id={self._card_id!r})"

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

    def calculate_from_config(self, config: dict) -> int:
        """Delegate to the real deterministic implementation."""
        return calculate_seed_from_config(config)


class SpyScenarioGenerator:
    """Spy ScenarioGenerator that records calls and returns configurable shapes."""

    def __init__(self, shapes: Optional[list[dict]] = None) -> None:
        self._shapes: list[dict] = shapes if shapes is not None else []
        self.calls: list[tuple[int, TableSize, GameMode]] = []

    def __repr__(self) -> str:
        return (
            f"SpyScenarioGenerator(shapes={len(self._shapes)}, calls={len(self.calls)})"
        )

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        self.calls.append((seed, table, mode))
        return self._shapes


class FakeCardRepository:
    """In-memory card repository for testing."""

    def __init__(self, cards: Optional[list[Card]] = None) -> None:
        self.cards: dict[str, Card] = {c.card_id: c for c in (cards or [])}
        self.save_calls: list[Card] = []
        self.delete_calls: list[str] = []

    def add(self, card: Card) -> None:
        self.cards[card.card_id] = card

    def get_by_id(self, card_id: str) -> Optional[Card]:
        return self.cards.get(card_id)

    def save(self, card: Card) -> None:
        self.save_calls.append(card)
        self.cards[card.card_id] = card

    def find_by_seed(self, seed: int) -> Optional[Card]:
        return next((c for c in self.cards.values() if c.seed == seed), None)

    def delete(self, card_id: str) -> bool:
        self.delete_calls.append(card_id)
        return self.cards.pop(card_id, None) is not None

    def list_all(self) -> list[Card]:
        return list(self.cards.values())

    def list_for_owner(self, owner_id: str) -> list[Card]:
        return [c for c in self.cards.values() if c.owner_id == owner_id]


# =============================================================================
# FIXTURES — GenerateScenarioCard
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
def spy_scenario_generator(request: pytest.FixtureRequest) -> SpyScenarioGenerator:
    return SpyScenarioGenerator(shapes=request.getfixturevalue("valid_shapes"))


@pytest.fixture
def use_case(request: pytest.FixtureRequest) -> GenerateScenarioCard:
    return GenerateScenarioCard(
        id_generator=request.getfixturevalue("fake_id_generator"),
        seed_generator=request.getfixturevalue("fake_seed_generator"),
        scenario_generator=request.getfixturevalue("spy_scenario_generator"),
    )


@pytest.fixture
def schema_use_case() -> GenerateScenarioCard:
    """Use case configured with empty shapes for schema-validation tests."""
    return GenerateScenarioCard(
        id_generator=FakeIdGenerator(),
        seed_generator=FakeSeedGenerator(),
        scenario_generator=SpyScenarioGenerator(shapes=[]),
    )


# =============================================================================
# FIXTURES — CreateVariant
# =============================================================================
@pytest.fixture
def repo() -> FakeCardRepository:
    """Provide empty card repository."""
    return FakeCardRepository()


@pytest.fixture
def id_gen() -> FakeIdGenerator:
    """Provide fake id generator for variant tests."""
    return FakeIdGenerator("card-variant-001")


@pytest.fixture
def seed_gen() -> FakeSeedGenerator:
    """Provide fake seed generator."""
    return FakeSeedGenerator(999)


@pytest.fixture
def scenario_gen() -> SpyScenarioGenerator:
    """Provide spy scenario generator with valid shapes for standard table."""
    return SpyScenarioGenerator(
        shapes=[{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}],
    )


class FakeFavoritesRepository:
    """In-memory fake favorites repository for testing."""

    def __init__(self) -> None:
        self._favorites: set[tuple[str, str]] = set()
        self.remove_all_calls: list[str] = []

    def is_favorite(self, actor_id: str, card_id: str) -> bool:
        return (actor_id, card_id) in self._favorites

    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None:
        key = (actor_id, card_id)
        if value:
            self._favorites.add(key)
        else:
            self._favorites.discard(key)

    def list_favorites(self, actor_id: str) -> list[str]:
        return sorted(
            [card_id for (uid, card_id) in self._favorites if uid == actor_id]
        )

    def remove_all_for_card(self, card_id: str) -> None:
        self.remove_all_calls.append(card_id)
        self._favorites = {k for k in self._favorites if k[1] != card_id}


@pytest.fixture
def favorites_repo() -> FakeFavoritesRepository:
    """Provide empty favorites repository."""
    return FakeFavoritesRepository()


# =============================================================================
# FIXTURES — GetCard
# =============================================================================
@pytest.fixture
def private_card(request: pytest.FixtureRequest) -> Card:
    """A PRIVATE Card owned by 'owner-123'."""
    return Card(
        card_id="card-001",
        owner_id="owner-123",
        visibility=Visibility.PRIVATE,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=42,
        table=request.getfixturevalue("table"),
        map_spec=request.getfixturevalue("map_spec"),
    )


@pytest.fixture
def public_card(request: pytest.FixtureRequest) -> Card:
    """A PUBLIC Card owned by 'owner-123'."""
    return Card(
        card_id="card-002",
        owner_id="owner-123",
        visibility=Visibility.PUBLIC,
        shared_with=None,
        mode=GameMode.CASUAL,
        seed=99,
        table=request.getfixturevalue("table"),
        map_spec=request.getfixturevalue("map_spec"),
    )


@pytest.fixture
def empty_repository() -> FakeCardRepository:
    """Provide empty card repository for GetCard tests."""
    return FakeCardRepository()


@pytest.fixture
def repository_with_private_card(request: pytest.FixtureRequest) -> FakeCardRepository:
    """Repository pre-loaded with a private card."""
    card = request.getfixturevalue("private_card")
    return FakeCardRepository([card])


@pytest.fixture
def repository_with_public_card(request: pytest.FixtureRequest) -> FakeCardRepository:
    """Repository pre-loaded with a public card."""
    card = request.getfixturevalue("public_card")
    return FakeCardRepository([card])


# =============================================================================
# FIXTURES — SaveCard
# =============================================================================
@pytest.fixture
def valid_card(request: pytest.FixtureRequest) -> Card:
    """A valid Card owned by 'owner-123'."""
    return Card(
        card_id="card-001",
        owner_id="owner-123",
        visibility=Visibility.PRIVATE,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=42,
        table=request.getfixturevalue("table"),
        map_spec=request.getfixturevalue("map_spec"),
    )


@pytest.fixture
def fake_repository() -> FakeCardRepository:
    """Provide empty card repository for SaveCard tests."""
    return FakeCardRepository()


# =============================================================================
# TEST DOUBLES — RenderMapSvg
# =============================================================================
class SpySvgRenderer:
    """Spy SVG renderer that tracks calls and returns configurable SVG."""

    def __init__(
        self, svg: str = "<svg></svg>", should_raise: Optional[Exception] = None
    ) -> None:
        self._svg = svg
        self._should_raise = should_raise
        self.calls: list[tuple[dict, list[dict]]] = []

    def render(
        self,
        table_mm: dict,
        shapes: list[dict],
        render_mode: str = "full",
        display_units: str = "cm",
    ) -> str:
        """Render table and shapes to SVG, recording the call."""
        del render_mode, display_units  # Interface parity; spy tracks table+shapes
        self.calls.append((table_mm, shapes))
        if self._should_raise:
            raise self._should_raise
        return self._svg

    def render_svg(self, map_spec: dict) -> str:
        """Render map spec to SVG."""
        del map_spec  # Interface parity
        return self._svg


@pytest.fixture
def renderer() -> SpySvgRenderer:
    """Provide spy renderer."""
    return SpySvgRenderer("<svg></svg>")
