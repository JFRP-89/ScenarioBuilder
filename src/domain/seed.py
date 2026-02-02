from __future__ import annotations

import random


def get_rng(seed: int | None) -> random.Random:
    """Return deterministic RNG for a given seed."""
    # deterministic RNG for reproducibility (not crypto)
    return random.Random(seed)  # nosec B311
