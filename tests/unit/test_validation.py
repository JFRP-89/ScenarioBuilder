"""Unit tests for domain validation helpers."""

from __future__ import annotations

import pytest

from domain.errors import ValidationError
from domain.validation import validate_non_empty_str


class TestValidateNonEmptyStr:
    """Tests for validate_non_empty_str()."""

    def test_returns_stripped_string(self):
        assert validate_non_empty_str("name", "  value  ") == "value"

    def test_allows_none_when_flag_true(self):
        assert validate_non_empty_str("name", None, allow_none=True) is None

    def test_rejects_none_when_flag_false(self):
        with pytest.raises(ValidationError):
            validate_non_empty_str("name", None)

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError):
            validate_non_empty_str("name", 123)

    def test_rejects_empty_or_whitespace(self):
        with pytest.raises(ValidationError):
            validate_non_empty_str("name", "")
        with pytest.raises(ValidationError):
            validate_non_empty_str("name", "   ")
