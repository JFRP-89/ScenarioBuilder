"""SecureSeedGenerator - Cryptographically secure seed generation.

A simple implementation of SeedGenerator using the secrets module.
Also provides deterministic seed calculation from configuration.
"""

from __future__ import annotations

import secrets
from typing import Any

from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


class SecureSeedGenerator:
    """Secure seed generator using cryptographic randomness.

    Generates non-negative integer seeds with high variability.
    Also calculates deterministic seeds from card configuration.
    """

    def generate_seed(self) -> int:
        """Generate a random seed.

        Returns:
            A non-negative integer with 31 bits of randomness.
        """
        return secrets.randbits(31)

    def calculate_from_config(self, config: dict[str, Any]) -> int:
        """Calculate a deterministic seed from card configuration.

        Delegates to the ``calculate_seed_from_config`` function.

        Args:
            config: Dictionary with card configuration fields.

        Returns:
            Integer seed in range ``[0, 2**31 - 1]``.
        """
        result: int = calculate_seed_from_config(config)
        return result
