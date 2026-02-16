"""Seed utilities: normalization, RNG, and deterministic derivation."""

from __future__ import annotations

import hashlib
import random
import struct

from domain.errors import ValidationError

# Maximum seed value: 2^31 - 1 (fits in signed 32-bit int)
MAX_SEED = (1 << 31) - 1


def get_rng(seed: int | None) -> random.Random:
    """Return deterministic RNG for a given seed."""
    # deterministic RNG for reproducibility (not crypto)
    return random.Random(seed)  # nosec B311


def _normalize_int(raw: int) -> int:
    if raw < 0:
        raise ValidationError(f"seed must be >= 0, got {raw}")
    return min(raw, MAX_SEED)


def _normalize_float(raw: float) -> int:
    if raw != raw:  # NaN check
        raise ValidationError("seed cannot be NaN")
    if raw < 0:
        raise ValidationError(f"seed must be >= 0, got {raw}")
    if raw != int(raw):
        raise ValidationError(f"seed must be a whole number, got {raw}")
    return min(int(raw), MAX_SEED)


def _normalize_str(raw: str) -> int:
    stripped = raw.strip()
    if not stripped:
        raise ValidationError("seed cannot be an empty string")
    try:
        value = int(stripped)
    except ValueError as exc:
        raise ValidationError(
            f"seed must be a numeric string, got '{stripped}'"
        ) from exc
    if value < 0:
        raise ValidationError(f"seed must be >= 0, got {value}")
    return min(value, MAX_SEED)


def normalize_seed(raw: object) -> int:
    """Normalize a raw seed value to a valid int in [0, MAX_SEED].

    Accepted inputs:
    - int >= 0 (clamped to MAX_SEED)
    - str of digits (parsed, clamped)
    - float that is whole (converted, clamped)
    - None -> 0 (manual mode)

    Rejected:
    - bool, negative int, non-numeric string, float with decimals, empty string

    Args:
        raw: Seed input from any external source.

    Returns:
        Normalized seed integer in [0, MAX_SEED].

    Raises:
        ValidationError: If raw cannot be converted to a valid seed.
    """
    if raw is None:
        return 0

    if isinstance(raw, bool):
        raise ValidationError("seed cannot be a boolean")

    if isinstance(raw, int):
        return _normalize_int(raw)

    if isinstance(raw, float):
        return _normalize_float(raw)

    if isinstance(raw, str):
        return _normalize_str(raw)

    raise ValidationError(
        f"seed must be int, str, float, or None; got {type(raw).__name__}"
    )


def derive_attempt_seed(base_seed: int, attempt_index: int) -> int:
    """Derive a deterministic seed for a retry attempt using SHA-256.

    This produces a new seed that is:
    - Deterministic: same (base_seed, attempt_index) → same result
    - Uniformly distributed across [0, MAX_SEED]
    - Independent: no correlation between consecutive attempt indices

    Args:
        base_seed: Original seed value (>= 0).
        attempt_index: Retry attempt number (0-based). Index 0 returns base_seed.

    Returns:
        Derived seed integer in [0, MAX_SEED].
    """
    if attempt_index == 0:
        return base_seed

    # Pack seed and index into bytes and hash with SHA-256
    data = struct.pack(">QI", base_seed, attempt_index)
    digest = hashlib.sha256(data).digest()
    # Take first 4 bytes as unsigned int, mask to 31 bits
    derived = int(struct.unpack(">I", digest[:4])[0]) & MAX_SEED
    return derived
