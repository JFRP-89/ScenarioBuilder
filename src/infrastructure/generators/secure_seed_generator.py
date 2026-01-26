"""SecureSeedGenerator - Cryptographically secure seed generation.

A simple implementation of SeedGenerator using the secrets module.
"""

from __future__ import annotations

import secrets


class SecureSeedGenerator:
    """Secure seed generator using cryptographic randomness.

    Generates non-negative integer seeds with high variability.
    """

    def generate_seed(self) -> int:
        """Generate a random seed.

        Returns:
            A non-negative integer with 31 bits of randomness.
        """
        return secrets.randbits(31)
