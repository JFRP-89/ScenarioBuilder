"""Unit tests for registration-related validators."""

from __future__ import annotations

import pytest
from infrastructure.auth.validators import (
    validate_registration_password,
    validate_username,
)

# ── validate_registration_password ───────────────────────────────────────────


class TestValidateRegistrationPassword:
    """Strong password policy: >=8 chars, upper, lower, digit, special."""

    def test_valid_password(self):
        ok, errors = validate_registration_password("Str0ng!pw")
        assert ok is True
        assert errors == []

    def test_valid_password_complex(self):
        ok, errors = validate_registration_password("MyP@ssw0rd!2024")
        assert ok is True
        assert errors == []

    def test_too_short(self):
        ok, errors = validate_registration_password("Ab1!")
        assert ok is False
        assert any("8 characters" in e for e in errors)

    def test_no_uppercase(self):
        ok, errors = validate_registration_password("abcdefg1!")
        assert ok is False
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase(self):
        ok, errors = validate_registration_password("ABCDEFG1!")
        assert ok is False
        assert any("lowercase" in e for e in errors)

    def test_no_digit(self):
        ok, errors = validate_registration_password("Abcdefgh!")
        assert ok is False
        assert any("digit" in e for e in errors)

    def test_no_special_char(self):
        ok, errors = validate_registration_password("Abcdefg1")
        assert ok is False
        assert any("special" in e for e in errors)

    def test_empty(self):
        ok, errors = validate_registration_password("")
        assert ok is False
        assert len(errors) >= 1

    def test_all_requirements_missing(self):
        ok, errors = validate_registration_password("abc")
        assert ok is False
        # Should flag: too short, no uppercase, no digit, no special
        assert len(errors) >= 3

    def test_exactly_8_chars_valid(self):
        ok, errors = validate_registration_password("Abc1234!")
        assert ok is True
        assert errors == []

    def test_64_chars_valid(self):
        pw = "A" + "a" * 55 + "1234567!"
        ok, errors = validate_registration_password(pw)
        assert ok is True
        assert errors == []

    def test_65_chars_too_long(self):
        pw = "A" + "a" * 56 + "1234567!"
        ok, errors = validate_registration_password(pw)
        assert ok is False
        assert len(errors) >= 1

    @pytest.mark.parametrize(
        "pw",
        [
            "Passw0rd!",
            "H3llo-W0rld_",
            "Test@1234",
            "C0mpl3x#Pass",
        ],
    )
    def test_various_valid_passwords(self, pw):
        ok, errors = validate_registration_password(pw)
        assert ok is True
        assert errors == []

    @pytest.mark.parametrize(
        "pw",
        [
            "password",  # no upper, no digit, no special
            "PASSWORD1!",  # no lower
            "12345678!",  # no upper, no lower
        ],
    )
    def test_various_invalid_passwords(self, pw):
        ok, errors = validate_registration_password(pw)
        assert ok is False
        assert len(errors) >= 1


# ── validate_username (existing, but verify for registration context) ────────


class TestValidateUsernameForRegistration:
    def test_valid_username_min_length(self):
        assert validate_username("abc") is True

    def test_username_too_short(self):
        assert validate_username("ab") is False

    def test_username_starts_with_underscore(self):
        assert validate_username("_abc") is False

    def test_valid_with_allowed_chars(self):
        assert validate_username("user-name_01") is True

    def test_uppercase_rejected(self):
        assert validate_username("Alice") is False
