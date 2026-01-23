from __future__ import annotations

import random
from typing import Optional


def get_rng(seed: Optional[int]) -> random.Random:
    """Return deterministic RNG for a given seed."""
    return random.Random(seed)
