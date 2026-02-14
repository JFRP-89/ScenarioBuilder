"""Unit tests — input validators for auth (allowlist-based)."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.auth._validators import (
    validate_display_name,
    validate_email,
    validate_password,
    validate_username,
)


# =====================================================================
# Username validation
# =====================================================================
class TestValidateUsername:
    """Username must match ^[a-z0-9][a-z0-9_-]{2,31}$."""

    @pytest.mark.parametrize(
        "value",
        [
            "alice",
            "bob",
            "demo-user",
            "user_123",
            "abc",
            "a" * 32,
        ],
    )
    def test_valid_usernames(self, value: str):
        assert validate_username(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "",  # empty
            "ab",  # too short (2 chars)
            "a" * 33,  # too long (33 chars)
            "Alice",  # uppercase
            "_user",  # starts with underscore
            "-user",  # starts with dash
            "user name",  # space
            "user@name",  # special char
            "user<script>",  # injection attempt
            "admin'; DROP TABLE--",  # SQL injection
        ],
    )
    def test_invalid_usernames(self, value: str):
        assert validate_username(value) is False


# =====================================================================
# Password validation
# =====================================================================
class TestValidatePassword:
    """Password must match ^[A-Za-z0-9_-]{3,32}$."""

    @pytest.mark.parametrize(
        "value",
        [
            "abc",
            "Alice123",
            "my-pass_word",
            "A" * 32,
        ],
    )
    def test_valid_passwords(self, value: str):
        assert validate_password(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "",  # empty
            "ab",  # too short
            "A" * 33,  # too long
            "pass word",  # space
            "pass@word",  # special char
            "p<script>",  # injection
        ],
    )
    def test_invalid_passwords(self, value: str):
        assert validate_password(value) is False


# =====================================================================
# Email validation
# =====================================================================
class TestValidateEmail:
    """Email must match ^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$."""

    @pytest.mark.parametrize(
        "value",
        [
            "alice@example.com",
            "bob@test.org",
            "user+tag@domain.co.uk",
            "demo@example.com",
        ],
    )
    def test_valid_emails(self, value: str):
        assert validate_email(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "not-an-email",
            "@missing-local.com",
            "missing-domain@",
            "missing@dot",
            "has space@example.com",
            "two@@signs.com",
        ],
    )
    def test_invalid_emails(self, value: str):
        assert validate_email(value) is False


# =====================================================================
# Display name validation
# =====================================================================
class TestValidateDisplayName:
    """Display name: 1-64 printable ASCII characters."""

    @pytest.mark.parametrize(
        "value",
        [
            "Alice",
            "Bob Smith",
            "A",
            "x" * 64,
        ],
    )
    def test_valid_names(self, value: str):
        assert validate_display_name(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "",  # empty
            "x" * 65,  # too long
            "name\t",  # tab (control char)
            "name\n",  # newline
        ],
    )
    def test_invalid_names(self, value: str):
        assert validate_display_name(value) is False
