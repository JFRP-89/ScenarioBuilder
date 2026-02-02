"""Common validation utilities for domain models.

This module provides reusable validation helpers to eliminate duplication
across domain models.
"""

from __future__ import annotations

from typing import Any

from domain.errors import ValidationError


def validate_non_empty_str(
    name: str, value: Any, allow_none: bool = False
) -> str | None:
    """Validate that value is a non-empty string after strip.

    Args:
        name: Parameter name for error messages.
        value: The value to validate.
        allow_none: If True, None is accepted and returned as None.
                   If False (default), None raises ValidationError.

    Returns:
        Stripped string value, or None if allow_none=True and value is None.

    Raises:
        ValidationError: If value is None (and allow_none=False), not a string,
                        or empty after strip.
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{name} cannot be None")

    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")

    stripped = value.strip()
    if not stripped:
        raise ValidationError(f"{name} cannot be empty or whitespace-only")

    return stripped
