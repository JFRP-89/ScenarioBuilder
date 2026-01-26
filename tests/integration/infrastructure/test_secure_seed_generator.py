"""RED tests for SecureSeedGenerator.

Tests the secure implementation of SeedGenerator for the modern API.
This generator produces random seeds for scenario generation.
"""

from __future__ import annotations

import pytest


# =============================================================================
# BASIC CONTRACT TESTS
# =============================================================================
class TestSecureSeedGeneratorContract:
    """Tests for basic contract: returns int >= 0."""

    def test_generate_seed_returns_int(self) -> None:
        """generate_seed returns an int (not bool)."""
        from infrastructure.generators.secure_seed_generator import (
            SecureSeedGenerator,
        )

        # Arrange
        gen = SecureSeedGenerator()

        # Act
        seed = gen.generate_seed()

        # Assert - must be int but not bool (bool is subclass of int)
        assert isinstance(seed, int)
        assert not isinstance(seed, bool)

    def test_generate_seed_returns_non_negative(self) -> None:
        """generate_seed returns a value >= 0."""
        from infrastructure.generators.secure_seed_generator import (
            SecureSeedGenerator,
        )

        # Arrange
        gen = SecureSeedGenerator()

        # Act
        seed = gen.generate_seed()

        # Assert
        assert seed >= 0


# =============================================================================
# VARIABILITY TESTS
# =============================================================================
class TestSecureSeedGeneratorVariability:
    """Tests for randomness and variability."""

    def test_multiple_calls_produce_variety(self) -> None:
        """Multiple calls produce reasonably varied values."""
        from infrastructure.generators.secure_seed_generator import (
            SecureSeedGenerator,
        )

        # Arrange
        gen = SecureSeedGenerator()
        n = 50

        # Act
        seeds = [gen.generate_seed() for _ in range(n)]

        # Assert - at least half should be unique (reasonable variety)
        assert len(set(seeds)) > n // 2

    def test_all_generated_values_are_non_negative_ints(self) -> None:
        """All generated values satisfy the contract."""
        from infrastructure.generators.secure_seed_generator import (
            SecureSeedGenerator,
        )

        # Arrange
        gen = SecureSeedGenerator()

        # Act
        seeds = [gen.generate_seed() for _ in range(20)]

        # Assert
        for seed in seeds:
            assert isinstance(seed, int)
            assert not isinstance(seed, bool)
            assert seed >= 0


# =============================================================================
# ISOLATION TESTS
# =============================================================================
class TestSecureSeedGeneratorIsolation:
    """Tests for instance independence."""

    def test_two_instances_also_produce_variety(self) -> None:
        """Two separate instances produce varied values."""
        from infrastructure.generators.secure_seed_generator import (
            SecureSeedGenerator,
        )

        # Arrange
        gen1 = SecureSeedGenerator()
        gen2 = SecureSeedGenerator()

        # Act
        seeds = [gen1.generate_seed() for _ in range(25)]
        seeds += [gen2.generate_seed() for _ in range(25)]

        # Assert - combined should still have variety
        assert len(set(seeds)) > 25
