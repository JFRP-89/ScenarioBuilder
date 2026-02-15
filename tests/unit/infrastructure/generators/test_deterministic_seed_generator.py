"""Tests for deterministic seed generation."""

from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


class TestDeterministicSeedGenerator:
    """Test deterministic seed calculation from config."""

    def test_same_config_produces_same_seed(self):
        """Same config always produces same seed (reproducibility)."""
        config = {"deployments": 2, "objectives": 3, "scenography": "no-overlap"}

        seed1 = calculate_seed_from_config(config)
        seed2 = calculate_seed_from_config(config)

        assert seed1 == seed2

    def test_different_config_produces_different_seed(self):
        """Different config produces different seed."""
        config1 = {"deployments": 2, "objectives": 3}
        config2 = {"deployments": 2, "objectives": 4}  # Changed objectives

        seed1 = calculate_seed_from_config(config1)
        seed2 = calculate_seed_from_config(config2)

        assert seed1 != seed2

    def test_small_change_produces_different_seed(self):
        """Even a small change in config produces different seed."""
        config1 = {"name": "test"}
        config2 = {"name": "test2"}  # Added one character

        seed1 = calculate_seed_from_config(config1)
        seed2 = calculate_seed_from_config(config2)

        assert seed1 != seed2

    def test_revert_config_reverts_seed(self):
        """Reverting config to previous version reverts the seed (idempotency)."""
        config1 = {"deployments": 2, "objectives": 3}
        config2 = {"deployments": 2, "objectives": 4}

        seed1_initial = calculate_seed_from_config(config1)
        seed2 = calculate_seed_from_config(config2)
        seed1_reverted = calculate_seed_from_config(config1)  # Back to config1

        assert seed1_initial == seed1_reverted
        assert seed1_initial != seed2

    def test_seed_is_non_negative_int(self):
        """Seed is always a non-negative integer."""
        config = {"deployments": 2, "objectives": 10, "scenography": 3}

        seed = calculate_seed_from_config(config)

        assert isinstance(seed, int)
        assert seed >= 0

    def test_seed_fits_in_31_bits(self):
        """Seed fits in 31-bit signed integer range."""
        config = {"a": "b"}

        seed = calculate_seed_from_config(config)

        assert 0 <= seed < 2**31

    def test_order_of_keys_does_not_matter(self):
        """Order of keys in config dict doesn't affect seed (due to sort_keys)."""
        config1 = {"deployments": 2, "objectives": 3, "scenography": "no-overlap"}
        config2 = {"objectives": 3, "scenography": "no-overlap", "deployments": 2}

        seed1 = calculate_seed_from_config(config1)
        seed2 = calculate_seed_from_config(config2)

        assert seed1 == seed2  # Same content, different order → same seed

    def test_nested_config_is_supported(self):
        """Nested dictionaries/lists are handled correctly."""
        config = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": ["deployment", "objective", "scenography"],
        }

        seed = calculate_seed_from_config(config)

        assert isinstance(seed, int)
        assert seed >= 0

    def test_empty_config_produces_valid_seed(self):
        """Empty config still produces a valid seed."""
        config: dict = {}

        seed = calculate_seed_from_config(config)

        assert isinstance(seed, int)
        assert seed >= 0
