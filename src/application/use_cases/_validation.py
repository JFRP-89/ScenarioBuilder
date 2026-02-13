"""Shared validation helpers for use cases.

Delegates to :mod:`domain.validation` for the core non-empty-string check
so that error messages and logic live in a single place.
"""

from __future__ import annotations

from typing import cast

from application.ports.repositories import CardRepository
from domain.cards.card import Card
from domain.errors import ForbiddenError, NotFoundError
from domain.validation import validate_non_empty_str


def validate_actor_id(actor_id: object) -> str:
    """Validate actor_id is non-empty string.

    Args:
        actor_id: The actor ID to validate (any type).

    Returns:
        The validated and stripped actor_id string.

    Raises:
        ValidationError: If actor_id is None, not a string, or empty/whitespace.
    """
    return cast(str, validate_non_empty_str("actor_id", actor_id))


def validate_card_id(card_id: object) -> str:
    """Validate card_id is non-empty string.

    Args:
        card_id: The card ID to validate (any type).

    Returns:
        The validated and stripped card_id string.

    Raises:
        ValidationError: If card_id is None, not a string, or empty/whitespace.
    """
    return cast(str, validate_non_empty_str("card_id", card_id))


def load_card_for_read(repository: CardRepository, card_id: str, actor_id: str) -> Card:
    """Fetch a card and enforce **read** access (anti-IDOR).

    Args:
        repository: Card repository with ``get_by_id``.
        card_id: Already-validated card ID.
        actor_id: Already-validated actor ID.

    Returns:
        The domain card object.

    Raises:
        NotFoundError: If card not found.
        ForbiddenError: If actor lacks read access.
    """
    card = repository.get_by_id(card_id)
    if card is None:
        raise NotFoundError(f"Card not found: {card_id}")
    if not card.can_user_read(actor_id):
        raise ForbiddenError("Forbidden: user does not have read access")
    return card


def load_card_for_write(
    repository: CardRepository, card_id: str, actor_id: str
) -> Card:
    """Fetch a card and enforce **write** access (anti-IDOR).

    Args:
        repository: Card repository with ``get_by_id``.
        card_id: Already-validated card ID.
        actor_id: Already-validated actor ID.

    Returns:
        The domain card object.

    Raises:
        NotFoundError: If card not found.
        ForbiddenError: If actor lacks write access.
    """
    card = repository.get_by_id(card_id)
    if card is None:
        raise NotFoundError(f"Card not found: {card_id}")
    if not card.can_user_write(actor_id):
        raise ForbiddenError("Forbidden: only the owner can modify this card")
    return card
