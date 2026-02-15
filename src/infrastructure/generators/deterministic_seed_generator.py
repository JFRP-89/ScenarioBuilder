"""Deterministic seed generation based on JSON content hash.

Seeds are calculated from card configuration so that:
- Same config → Same seed (reproducible)
- Change 1 char → Different seed (lightweight)
- Revert config → Seed reverts (idempotent)

This enables true reproducibility without storing random numbers.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def calculate_seed_from_config(config: dict[str, Any]) -> int:
    """Calculate a deterministic seed from card configuration.

    The seed is derived from a SHA256 hash of the JSON content.
    This ensures:
    - Reproducibility: same config always produces same seed
    - Sensitivity: small config changes produce different seeds
    - Idempotency: reverting config reverts the seed

    Args:
        config: Dictionary with card configuration fields.
               Typically: deployments, objectives, scenography, symmetry, etc.

    Returns:
        Integer seed in range [0, 2^31-1] suitable for random.Random().

    Example:
        >>> config1 = {"deployments": 2, "objectives": 3}
        >>> seed1 = calculate_seed_from_config(config1)
        >>> config1_again = {"deployments": 2, "objectives": 3}
        >>> seed1_again = calculate_seed_from_config(config1_again)
        >>> seed1 == seed1_again  # True

        >>> config2 = {"deployments": 2, "objectives": 4}  # Changed objectives
        >>> seed2 = calculate_seed_from_config(config2)
        >>> seed1 != seed2  # True
    """
    # Canonicalize JSON: sort keys, remove whitespace
    # This ensures same content always produces same string
    json_str = json.dumps(config, sort_keys=True, separators=(",", ":"))

    # Hash the content with SHA256
    hash_digest = hashlib.sha256(json_str.encode()).digest()

    # Convert first 4 bytes to integer (deterministic)
    # The & 0x7FFFFFFF ensures it fits in a signed 31-bit int for compatibility
    seed = int.from_bytes(hash_digest[:4], byteorder="big") & 0x7FFFFFFF

    return seed
