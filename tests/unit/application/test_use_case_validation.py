"""Unit tests for application.use_cases._validation helpers.

Covers validate_actor_id, validate_card_id, load_card_for_read,
and load_card_for_write.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest
from application.use_cases._validation import (
    load_card_for_read,
    load_card_for_write,
    validate_actor_id,
    validate_card_id,
)
from domain.errors import ValidationError

# ── Fake card / repo ──────────────────────────────────────────────


@dataclass
class _FakeCard:
    card_id: str
    owner_id: str
    readable_by: Optional[set[str]] = None

    def can_user_read(self, actor_id: str) -> bool:
        if actor_id == self.owner_id:
            return True
        return actor_id in (self.readable_by or set())

    def can_user_write(self, actor_id: str) -> bool:
        return actor_id == self.owner_id


class _FakeRepo:
    def __init__(self, cards: dict[str, _FakeCard] | None = None) -> None:
        self._store: dict[str, _FakeCard] = cards or {}

    def get_by_id(self, card_id: str) -> _FakeCard | None:
        return self._store.get(card_id)

    def save(self, card: _FakeCard) -> None:
        self._store[card.card_id] = card

    def find_by_seed(self, seed: int) -> _FakeCard | None:
        return next(
            (c for c in self._store.values() if getattr(c, "seed", None) == seed), None
        )

    def delete(self, card_id: str) -> bool:
        return self._store.pop(card_id, None) is not None

    def list_all(self) -> list[_FakeCard]:
        return list(self._store.values())

    def list_for_owner(self, owner_id: str) -> list[_FakeCard]:
        return [c for c in self._store.values() if c.owner_id == owner_id]


# ── validate_actor_id / validate_card_id ──────────────────────────


class TestValidateActorId:
    """Delegates to domain.validate_non_empty_str('actor_id', ...)."""

    def test_valid_string(self):
        assert validate_actor_id("user-1") == "user-1"

    def test_strips_whitespace(self):
        assert validate_actor_id("  user-1  ") == "user-1"

    def test_none_raises(self):
        with pytest.raises(ValidationError, match="actor_id"):
            validate_actor_id(None)

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="actor_id"):
            validate_actor_id("")

    def test_non_string_raises(self):
        with pytest.raises(ValidationError, match="actor_id"):
            validate_actor_id(42)


class TestValidateCardId:
    def test_valid_string(self):
        assert validate_card_id("card-1") == "card-1"

    def test_none_raises(self):
        with pytest.raises(ValidationError, match="card_id"):
            validate_card_id(None)


# ── load_card_for_read ────────────────────────────────────────────


class TestLoadCardForRead:
    """Fetch + read-access check helper."""

    def test_owner_can_read(self):
        card = _FakeCard(card_id="c1", owner_id="user-a")
        repo = _FakeRepo({"c1": card})
        assert load_card_for_read(repo, "c1", "user-a") is card  # type: ignore[arg-type]

    def test_shared_user_can_read(self):
        card = _FakeCard(card_id="c1", owner_id="user-a", readable_by={"user-b"})
        repo = _FakeRepo({"c1": card})
        assert load_card_for_read(repo, "c1", "user-b") is card  # type: ignore[arg-type]

    def test_not_found_raises(self):
        repo = _FakeRepo()
        with pytest.raises(Exception, match="(?i)not found"):
            load_card_for_read(repo, "missing", "user-a")  # type: ignore[arg-type]

    def test_forbidden_raises(self):
        card = _FakeCard(card_id="c1", owner_id="user-a")
        repo = _FakeRepo({"c1": card})
        with pytest.raises(Exception, match="(?i)forbidden"):
            load_card_for_read(repo, "c1", "stranger")  # type: ignore[arg-type]


# ── load_card_for_write ───────────────────────────────────────────


class TestLoadCardForWrite:
    """Fetch + write-access (ownership) check helper."""

    def test_owner_can_write(self):
        card = _FakeCard(card_id="c1", owner_id="user-a")
        repo = _FakeRepo({"c1": card})
        assert load_card_for_write(repo, "c1", "user-a") is card  # type: ignore[arg-type]

    def test_non_owner_forbidden(self):
        card = _FakeCard(card_id="c1", owner_id="user-a")
        repo = _FakeRepo({"c1": card})
        with pytest.raises(Exception, match="(?i)forbidden"):
            load_card_for_write(repo, "c1", "user-b")  # type: ignore[arg-type]

    def test_not_found_raises(self):
        repo = _FakeRepo()
        with pytest.raises(Exception, match="(?i)not found"):
            load_card_for_write(repo, "missing", "user-a")  # type: ignore[arg-type]
