"""
Authorization helpers for anti-IDOR protection.

Visibility states:
- PRIVATE: only owner can read/write
- SHARED: owner + allowlist can read, only owner can write
- PUBLIC: anyone can read, only owner can write

All functions follow deny-by-default: invalid inputs raise ValidationError.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from domain.errors import ValidationError
from domain.validation import validate_non_empty_str


class Visibility(Enum):
    """Resource visibility levels."""

    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


_VALID_VISIBILITY_VALUES = {v.value for v in Visibility}


def _validate_shared_with(shared_with: object) -> set[str]:
    """Validate and normalize shared_with collection.

    Args:
        shared_with: Collection of user IDs or None.

    Returns:
        Set of validated user IDs (empty set if None).

    Raises:
        ValidationError: If shared_with is invalid type or contains invalid entries.
    """
    if shared_with is None:
        return set()

    # Reject string explicitly (would iterate chars - security bug)
    if isinstance(shared_with, str):
        raise ValidationError("shared_with cannot be a string (use a list or set)")

    # Reject dict (iterating dict yields keys only - confusing)
    if isinstance(shared_with, dict):
        raise ValidationError("shared_with cannot be a dict")

    # Reject non-iterables
    if not isinstance(shared_with, Iterable):
        raise ValidationError("shared_with must be an iterable collection")

    result: set[str] = set()
    for item in shared_with:
        if item is None:
            raise ValidationError("shared_with cannot contain None")
        if not isinstance(item, str):
            raise ValidationError("shared_with must contain only strings")
        stripped = item.strip()
        if not stripped:
            raise ValidationError(
                "shared_with cannot contain empty or whitespace-only strings"
            )
        result.add(stripped)

    return result


def parse_visibility(value: object) -> Visibility:
    """Parse a visibility string into a Visibility enum.

    Args:
        value: String value to parse (case-insensitive, whitespace-trimmed).

    Returns:
        Visibility enum member.

    Raises:
        ValidationError: If value is None, not a string, empty, or unknown.
    """
    if value is None:
        raise ValidationError("visibility cannot be None")
    if not isinstance(value, str):
        raise ValidationError("visibility must be a string")

    normalized = value.strip().lower()

    if not normalized:
        raise ValidationError("visibility cannot be empty or whitespace-only")

    if normalized not in _VALID_VISIBILITY_VALUES:
        raise ValidationError(
            f"unknown visibility '{normalized}', "
            f"must be one of: {', '.join(sorted(_VALID_VISIBILITY_VALUES))}"
        )

    return Visibility(normalized)


def can_read(
    *,
    owner_id: object,
    visibility: Visibility,
    current_user_id: object,
    shared_with: object = None,
) -> bool:
    """Check if current user can read a resource.

    Args:
        owner_id: The resource owner's user ID.
        visibility: The resource's visibility level.
        current_user_id: The user attempting to read.
        shared_with: Collection of user IDs allowed to read (for SHARED visibility).

    Returns:
        True if access is allowed, False otherwise.

    Raises:
        ValidationError: If any input is invalid.
    """
    if not isinstance(visibility, Visibility):
        raise ValidationError("visibility must be Visibility")

    owner = validate_non_empty_str("owner_id", owner_id)
    current = validate_non_empty_str("current_user_id", current_user_id)

    # Owner can always read their own resource
    if owner == current:
        return True

    if visibility == Visibility.PUBLIC:
        return True

    if visibility == Visibility.PRIVATE:
        return False

    # SHARED: validate and check shared_with
    if visibility == Visibility.SHARED:
        allowed_users = _validate_shared_with(shared_with)
        return current in allowed_users

    # Unknown visibility (shouldn't happen with enum, but deny by default)
    return False


def can_write(
    *,
    owner_id: object,
    current_user_id: object,
) -> bool:
    """Check if current user can write to a resource.

    Write access is always owner-only, regardless of visibility.

    Args:
        owner_id: The resource owner's user ID.
        current_user_id: The user attempting to write.

    Returns:
        True if access is allowed, False otherwise.

    Raises:
        ValidationError: If any input is invalid.
    """
    owner = validate_non_empty_str("owner_id", owner_id)
    current = validate_non_empty_str("current_user_id", current_user_id)

    return bool(owner == current)
