"""Shared validation helpers for use cases.

This module provides common validation functions used across multiple use cases
to avoid code duplication and maintain consistent error messages.
"""

from __future__ import annotations

from domain.errors import ValidationError


def validate_actor_id(actor_id: object) -> str:
    """Validate actor_id is non-empty string.

    Args:
        actor_id: The actor ID to validate (any type).

    Returns:
        The validated and stripped actor_id string.

    Raises:
        ValidationError: If actor_id is None, not a string, or empty/whitespace.
    """
    if actor_id is None:
        raise ValidationError("actor_id cannot be None")
    if not isinstance(actor_id, str):
        raise ValidationError("actor_id must be a string")
    stripped = actor_id.strip()
    if not stripped:
        raise ValidationError("actor_id cannot be empty or whitespace-only")
    return stripped


def validate_card_id(card_id: object) -> str:
    """Validate card_id is non-empty string.

    Args:
        card_id: The card ID to validate (any type).

    Returns:
        The validated and stripped card_id string.

    Raises:
        ValidationError: If card_id is None, not a string, or empty/whitespace.
    """
    if card_id is None:
        raise ValidationError("card_id cannot be None")
    if not isinstance(card_id, str):
        raise ValidationError("card_id must be a string")
    stripped = card_id.strip()
    if not stripped:
        raise ValidationError("card_id cannot be empty or whitespace-only")
    return stripped
