from __future__ import annotations

from typing import Iterable, Tuple


def incompatible_pairs_ok(selected_ids: Iterable[str], pairs: Iterable[Tuple[str, str]]) -> bool:
    selected = set(selected_ids)
    for a, b in pairs:
        if a in selected and b in selected:
            return False
    return True
