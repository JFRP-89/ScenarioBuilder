"""Domain-level exceptions."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain validation errors."""

    pass


class ValidationError(DomainError):
    """Raised when input validation fails."""

    pass
