"""Domain-level exceptions."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    pass


class ValidationError(DomainError):
    """Raised when input validation fails."""

    pass


class NotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    pass


class ForbiddenError(DomainError):
    """Raised when the actor lacks permission to perform the operation."""

    pass
