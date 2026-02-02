"""Centralized error response contract for Flask adapter.

This module defines:
1. Helper to construct consistent error JSON responses
2. Error codes and HTTP status mappings
3. Error messages (generic safe messages for external API, never leak internals)
"""

from __future__ import annotations

from typing import Any, Optional

# =============================================================================
# HTTP Status & Error Codes
# =============================================================================

# Error codes used in API responses (domain-independent)
ERROR_VALIDATION = "ValidationError"
ERROR_NOT_FOUND = "NotFound"
ERROR_FORBIDDEN = "Forbidden"
ERROR_INTERNAL = "InternalError"

# HTTP Status codes (as integers)
STATUS_BAD_REQUEST = 400
STATUS_FORBIDDEN = 403
STATUS_NOT_FOUND = 404
STATUS_INTERNAL_ERROR = 500

# =============================================================================
# Standard Error Messages (User-Safe)
# =============================================================================

MSG_VALIDATION_ERROR = "Invalid request data"
MSG_NOT_FOUND = "Resource not found"
MSG_FORBIDDEN = "Access denied"
MSG_INTERNAL_ERROR = "An internal error occurred"

# =============================================================================
# Error Response Helper
# =============================================================================


def error_response(
    code: str,
    message: str,
    status: int,
    details: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], int]:
    """Construct a standardized error JSON response.

    Args:
        code: Error code string (e.g., "ValidationError", "NotFound")
        message: User-friendly error message (should never leak internal details)
        status: HTTP status code
        details: Optional dict with additional error context (use carefully)

    Returns:
        Tuple of (JSON body dict, HTTP status code) suitable for Flask jsonify()

    Example:
        >>> error_response("ValidationError", "Email is invalid", 400)
        ({"error": "ValidationError", "message": "Email is invalid"}, 400)

        >>> error_response(
        ...     "NotFound",
        ...     "Card not found",
        ...     404,
        ...     details={"card_id": "abc123"}
        ... )
        ({"error": "NotFound", "message": "Card not found", "details": {...}}, 404)
    """
    body: dict[str, Any] = {
        "error": code,
        "message": message,
    }
    if details:
        body["details"] = details
    return body, status
