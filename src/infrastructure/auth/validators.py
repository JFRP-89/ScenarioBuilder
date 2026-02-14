"""Input validators for authentication — allowlist-based, anti-injection.

All functions are **pure** (no I/O, no framework imports).
Shared across Flask and Gradio adapters.
"""

from __future__ import annotations

import re

# ── Allowlist regexes ────────────────────────────────────────────────────────
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,31}$")
PASSWORD_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Display name: printable ASCII, 1-64 chars, no control chars.
# Uses \Z (not $) to prevent bypass with trailing \n.
DISPLAY_NAME_RE = re.compile(r"^[\x20-\x7E]{1,64}\Z")


def validate_username(value: str) -> bool:
    """Return True if *value* matches the username allowlist."""
    return bool(USERNAME_RE.match(value))


def validate_password(value: str) -> bool:
    """Return True if *value* matches the password allowlist."""
    return bool(PASSWORD_RE.match(value))


def validate_email(value: str) -> bool:
    """Return True if *value* matches a minimal email pattern."""
    return bool(EMAIL_RE.match(value))


def validate_display_name(value: str) -> bool:
    """Return True if *value* is a valid display name."""
    return bool(DISPLAY_NAME_RE.match(value))
