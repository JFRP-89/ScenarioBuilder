"""Domain-level exceptions."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain-level errors."""


class ValidationError(DomainError):
    """Raised when input validation fails."""


class NotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class ForbiddenError(DomainError):
    """Raised when the actor lacks permission to perform the operation."""
