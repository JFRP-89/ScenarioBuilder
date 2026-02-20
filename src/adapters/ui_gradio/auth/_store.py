"""In-memory user store — delegates to infrastructure layer.

Re-exports all store functions from the shared infrastructure module.
This ensures Gradio and Flask use the **same** user data and lockout state.
"""

from __future__ import annotations

from infrastructure.auth.user_store import (
    LOCKOUT_DURATION,
    MAX_FAILED_ATTEMPTS,
    LockoutRecord,
    UserRecord,
    clear_failed_attempts,
    get_user_profile,
    is_locked,
    record_failed_attempt,
    reset_stores,
    update_user_profile,
    user_exists,
    verify_credentials,
)

__all__ = [
    "LOCKOUT_DURATION",
    "MAX_FAILED_ATTEMPTS",
    "LockoutRecord",
    "UserRecord",
    "clear_failed_attempts",
    "get_user_profile",
    "is_locked",
    "record_failed_attempt",
    "reset_stores",
    "update_user_profile",
    "user_exists",
    "verify_credentials",
]
