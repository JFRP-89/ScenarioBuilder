from __future__ import annotations

from typing import Iterable


def matched_score(risk_flags: Iterable[str]) -> int:
    """Simple heuristic: penalize each risk flag."""
    base = 100
    penalty = 10 * len(list(risk_flags))
    return max(0, base - penalty)
