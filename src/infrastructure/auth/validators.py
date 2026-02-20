"""Input validators for authentication — allowlist-based, anti-injection.

All functions are **pure** (no I/O, no framework imports).
Shared across Flask and Gradio adapters.
"""

from __future__ import annotations

import re

# ── Allowlist regexes ────────────────────────────────────────────────────────
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,31}$")
PASSWORD_RE = re.compile(r"^[\x20-\x7E]{3,64}\Z")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Display name: printable ASCII, 1-64 chars, no control chars.
# Uses \Z (not $) to prevent bypass with trailing \n.
DISPLAY_NAME_RE = re.compile(r"^[\x20-\x7E]{1,64}\Z")

# ── Strong password policy (for registration) ───────────────────────────────
# Printable ASCII 8-64 chars; must contain uppercase, lowercase, digit, and
# at least one special character.  Uses \Z to prevent \n bypass.
_STRONG_PW_CHAR_RE = re.compile(r"^[\x20-\x7E]{8,64}\Z")
_STRONG_PW_UPPER = re.compile(r"[A-Z]")
_STRONG_PW_LOWER = re.compile(r"[a-z]")
_STRONG_PW_DIGIT = re.compile(r"\d")
_STRONG_PW_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def validate_username(value: str) -> bool:
    """Return True if *value* matches the username allowlist."""
    return bool(USERNAME_RE.match(value))


def validate_password(value: str) -> bool:
    """Return True if *value* matches the password allowlist."""
    return bool(PASSWORD_RE.match(value))


def validate_registration_password(value: str) -> tuple[bool, list[str]]:
    """Validate a password against the strong registration policy.

    Returns ``(valid, errors)`` where *errors* is a list of human-readable
    failure reasons (empty when *valid* is True).
    """
    errors: list[str] = []
    if not _STRONG_PW_CHAR_RE.match(value):
        if len(value) < 8:
            errors.append("Must be at least 8 characters.")
        elif len(value) > 64:
            errors.append("Must be at most 64 characters.")
        else:
            errors.append("Contains invalid characters.")
    if not _STRONG_PW_UPPER.search(value):
        errors.append("Must include at least one uppercase letter.")
    if not _STRONG_PW_LOWER.search(value):
        errors.append("Must include at least one lowercase letter.")
    if not _STRONG_PW_DIGIT.search(value):
        errors.append("Must include at least one digit.")
    if not _STRONG_PW_SPECIAL.search(value):
        errors.append("Must include at least one special character.")
    return (len(errors) == 0, errors)


def validate_email(value: str) -> bool:
    """Return True if *value* matches a minimal email pattern."""
    return bool(EMAIL_RE.match(value))


def validate_display_name(value: str) -> bool:
    """Return True if *value* is a valid display name."""
    return bool(DISPLAY_NAME_RE.match(value))
