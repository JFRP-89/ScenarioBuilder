"""Unit tests for domain.seed -- normalize_seed and derive_attempt_seed."""

from __future__ import annotations

import pytest
from domain.errors import ValidationError
from domain.seed import MAX_SEED, derive_attempt_seed, normalize_seed


# =============================================================================
# normalize_seed — happy paths
# =============================================================================
class TestNormalizeSeedHappy:
    """Tests for valid normalize_seed inputs."""

    def test_none_returns_zero(self) -> None:
        assert normalize_seed(None) == 0

    def test_zero_returns_zero(self) -> None:
        assert normalize_seed(0) == 0

    def test_positive_int_passthrough(self) -> None:
        assert normalize_seed(42) == 42

    def test_large_int_clamped_to_max(self) -> None:
        assert normalize_seed(2**32) == MAX_SEED

    def test_max_seed_passthrough(self) -> None:
        assert normalize_seed(MAX_SEED) == MAX_SEED

    def test_string_digits_parsed(self) -> None:
        assert normalize_seed("123") == 123

    def test_string_with_whitespace_stripped(self) -> None:
        assert normalize_seed("  456  ") == 456

    def test_float_whole_number_accepted(self) -> None:
        assert normalize_seed(7.0) == 7

    def test_float_zero_accepted(self) -> None:
        assert normalize_seed(0.0) == 0


# =============================================================================
# normalize_seed — rejection paths
# =============================================================================
class TestNormalizeSeedRejection:
    """Tests for invalid normalize_seed inputs."""

    def test_bool_true_rejected(self) -> None:
        with pytest.raises(ValidationError, match="boolean"):
            normalize_seed(True)

    def test_bool_false_rejected(self) -> None:
        with pytest.raises(ValidationError, match="boolean"):
            normalize_seed(False)

    def test_negative_int_rejected(self) -> None:
        with pytest.raises(ValidationError, match=">= 0"):
            normalize_seed(-1)

    def test_negative_float_rejected(self) -> None:
        with pytest.raises(ValidationError, match=">= 0"):
            normalize_seed(-1.0)

    def test_float_with_decimals_rejected(self) -> None:
        with pytest.raises(ValidationError, match="whole number"):
            normalize_seed(3.14)

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValidationError, match="NaN"):
            normalize_seed(float("nan"))

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            normalize_seed("")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            normalize_seed("   ")

    def test_non_numeric_string_rejected(self) -> None:
        with pytest.raises(ValidationError, match="numeric"):
            normalize_seed("abc")

    def test_negative_string_rejected(self) -> None:
        with pytest.raises(ValidationError, match=">= 0"):
            normalize_seed("-5")

    def test_list_rejected(self) -> None:
        with pytest.raises(ValidationError, match="list"):
            normalize_seed([1, 2])

    def test_dict_rejected(self) -> None:
        with pytest.raises(ValidationError, match="dict"):
            normalize_seed({"seed": 1})


# =============================================================================
# derive_attempt_seed — determinism
# =============================================================================
class TestDeriveAttemptSeed:
    """Tests for derive_attempt_seed."""

    def test_attempt_zero_returns_base_seed(self) -> None:
        assert derive_attempt_seed(42, 0) == 42

    def test_attempt_one_differs_from_base(self) -> None:
        base = 42
        derived = derive_attempt_seed(base, 1)
        assert derived != base

    def test_deterministic_for_same_inputs(self) -> None:
        a = derive_attempt_seed(123, 5)
        b = derive_attempt_seed(123, 5)
        assert a == b

    def test_different_attempt_indices_differ(self) -> None:
        results = {derive_attempt_seed(42, i) for i in range(10)}
        # At least 9 unique values (extremely unlikely to have collisions)
        assert len(results) >= 9

    def test_different_base_seeds_differ(self) -> None:
        a = derive_attempt_seed(100, 1)
        b = derive_attempt_seed(200, 1)
        assert a != b

    def test_result_within_valid_range(self) -> None:
        for i in range(20):
            result = derive_attempt_seed(999, i)
            assert 0 <= result <= MAX_SEED
