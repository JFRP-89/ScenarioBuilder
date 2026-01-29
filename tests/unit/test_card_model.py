"""
MVP RED tests for Card domain model.

Card represents a generated scenario card that combines:
- Identity (card_id, owner_id)
- Visibility/AuthZ (visibility + shared_with)
- Game mode (casual/narrative/matched)
- Deterministic seed for reproducibility
- Table dimensions (TableSize) + shapes (MapSpec)

MVP contract:
- card_id/owner_id: non-empty strings
- seed: int >= 0 (reject bool/float/str)
- table: must be TableSize instance
- map_spec: must be MapSpec instance with matching table dimensions
- anti-IDOR: can_user_read/write delegation
"""

from __future__ import annotations

import pytest

from domain.maps.table_size import TableSize
from domain.maps.map_spec import MapSpec
from domain.security.authz import Visibility
from domain.cards.card import Card, GameMode, parse_game_mode
from domain.errors import ValidationError
from domain.cards.generator import _pick
from domain.seed import get_rng


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def table() -> TableSize:
    return TableSize.standard()


@pytest.fixture
def shapes() -> list[dict]:
    return [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]


@pytest.fixture
def map_spec(table: TableSize, shapes: list[dict]) -> MapSpec:
    return MapSpec(table=table, shapes=shapes)


@pytest.fixture
def owner() -> str:
    return "user_a"


@pytest.fixture
def other() -> str:
    return "user_b"


# =============================================================================
# 1) HAPPY PATH
# =============================================================================
def test_card_can_be_created_with_valid_data(
    table: TableSize, map_spec: MapSpec, owner: str
):
    card = Card(
        card_id="card-001",
        owner_id=owner,
        visibility=Visibility.PRIVATE,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=123,
        table=table,
        map_spec=map_spec,
    )
    assert card.card_id == "card-001"
    assert card.owner_id == owner
    assert card.visibility == Visibility.PRIVATE
    assert card.mode == GameMode.MATCHED
    assert card.seed == 123
    assert card.table == table
    assert card.map_spec == map_spec


# =============================================================================
# 2) INVALID IDS
# =============================================================================
@pytest.mark.parametrize("invalid_id", ["", "   "])
def test_card_rejects_invalid_ids(
    invalid_id: str, table: TableSize, map_spec: MapSpec, owner: str
):
    # Test invalid card_id
    with pytest.raises(ValidationError):
        Card(
            card_id=invalid_id,
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=table,
            map_spec=map_spec,
        )

    # Test invalid owner_id
    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=invalid_id,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=table,
            map_spec=map_spec,
        )


# =============================================================================
# 3) INVALID SEED
# =============================================================================
@pytest.mark.parametrize("invalid_seed", [-1, "123", 1.5, True])
def test_card_rejects_invalid_seed(
    invalid_seed, table: TableSize, map_spec: MapSpec, owner: str
):
    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=invalid_seed,
            table=table,
            map_spec=map_spec,
        )


# =============================================================================
# 4) TABLE AND MAPSPEC TYPE REQUIREMENTS
# =============================================================================
def test_card_requires_table_and_mapspec_types(map_spec: MapSpec, owner: str):
    # Reject table as non-TableSize
    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table={"width_mm": 1200, "height_mm": 1200},
            map_spec=map_spec,
        )

    # Reject map_spec as non-MapSpec
    table_valid = TableSize.standard()
    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=table_valid,
            map_spec={"shapes": []},
        )


# =============================================================================
# 5) MAPSPEC MUST MATCH TABLE
# =============================================================================
def test_card_requires_mapspec_matches_table(owner: str):
    standard = TableSize.standard()  # 1200x1200
    massive = TableSize.massive()  # 1800x1200
    shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]
    map_spec_massive = MapSpec(table=massive, shapes=shapes)

    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=standard,
            map_spec=map_spec_massive,
        )


# =============================================================================
# 6) ACCESS - PRIVATE
# =============================================================================
def test_card_access_private(
    table: TableSize, map_spec: MapSpec, owner: str, other: str
):
    card = Card(
        card_id="card-001",
        owner_id=owner,
        visibility=Visibility.PRIVATE,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=123,
        table=table,
        map_spec=map_spec,
    )
    assert card.can_user_read(owner) is True
    assert card.can_user_read(other) is False
    assert card.can_user_write(owner) is True
    assert card.can_user_write(other) is False


# =============================================================================
# 7) ACCESS - SHARED
# =============================================================================
def test_card_access_shared_allows_only_allowlisted_read(
    table: TableSize, map_spec: MapSpec, owner: str, other: str
):
    card = Card(
        card_id="card-001",
        owner_id=owner,
        visibility=Visibility.SHARED,
        shared_with=[other],
        mode=GameMode.MATCHED,
        seed=123,
        table=table,
        map_spec=map_spec,
    )
    assert card.can_user_read(other) is True
    assert card.can_user_write(other) is False


# =============================================================================
# 8) ACCESS - PUBLIC
# =============================================================================
def test_card_access_public_allows_anyone_read_but_not_write(
    table: TableSize, map_spec: MapSpec, owner: str, other: str
):
    card = Card(
        card_id="card-001",
        owner_id=owner,
        visibility=Visibility.PUBLIC,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=123,
        table=table,
        map_spec=map_spec,
    )
    assert card.can_user_read(other) is True
    assert card.can_user_write(other) is False


# =============================================================================
# 9) PARSE GAME MODE
# =============================================================================
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("matched", GameMode.MATCHED),
        ("MATCHED", GameMode.MATCHED),
        ("  casual ", GameMode.CASUAL),
        ("narrative", GameMode.NARRATIVE),
    ],
)
def test_parse_game_mode_accepts_valid_strings(raw: str, expected: GameMode):
    assert parse_game_mode(raw) == expected


@pytest.mark.parametrize("invalid", [None, 123, 1.5, True])
def test_parse_game_mode_rejects_non_string(invalid):
    with pytest.raises(ValidationError):
        parse_game_mode(invalid)


@pytest.mark.parametrize("invalid", ["", "   "])
def test_parse_game_mode_rejects_empty_or_whitespace(invalid: str):
    with pytest.raises(ValidationError):
        parse_game_mode(invalid)


def test_parse_game_mode_rejects_unknown_value():
    with pytest.raises(ValidationError):
        parse_game_mode("unknown")


# =============================================================================
# 10) INVALID TYPES - IDS, VISIBILITY, MODE
# =============================================================================
def test_card_rejects_non_string_ids(table: TableSize, map_spec: MapSpec):
    with pytest.raises(ValidationError):
        Card(
            card_id=123,
            owner_id="owner",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=table,
            map_spec=map_spec,
        )

    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=456,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=table,
            map_spec=map_spec,
        )


def test_card_rejects_invalid_visibility_type(
    table: TableSize, map_spec: MapSpec, owner: str
):
    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=owner,
            visibility="private",
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=123,
            table=table,
            map_spec=map_spec,
        )


def test_card_rejects_invalid_mode_type(
    table: TableSize, map_spec: MapSpec, owner: str
):
    with pytest.raises(ValidationError):
        Card(
            card_id="card-001",
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode="matched",
            seed=123,
            table=table,
            map_spec=map_spec,
        )


# =============================================================================
# TODO(hardening): Add parse_game_mode(), shared_with hardening, and advanced
# table coherence/relaxation tests in a separate hardening PR.
# =============================================================================


# =============================================================================
# 11) GENERATOR _PICK COVERAGE
# =============================================================================
def test_generator_pick_raises_when_items_empty():
    rng = get_rng(123)
    with pytest.raises(ValueError):
        _pick(rng, [])
