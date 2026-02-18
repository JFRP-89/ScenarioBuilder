"""Text utility functions for scenario card generation."""

from __future__ import annotations

from typing import Optional, Union


def _is_blank_text(value: Optional[str]) -> bool:
    """Return True when *value* is None or whitespace-only."""
    return value is None or not value.strip()


def _objectives_match_seed(
    request_objectives: Optional[Union[str, dict]],
    seed_objectives: str,
) -> bool:
    """Check if request objectives are unmodified relative to seed output.

    ``resolve_seed_preview`` always returns a plain string for objectives.
    Blank/None → will be auto-filled by seed → counts as unmodified.
    dict (VP-style) → user structured objectives → always modified.
    """
    if request_objectives is None or (
        isinstance(request_objectives, str) and not request_objectives.strip()
    ):
        return True  # blank → will be auto-filled by seed → unmodified
    if isinstance(request_objectives, dict):
        return False  # VP-style objectives never match a seed string
    return request_objectives.strip() == seed_objectives
