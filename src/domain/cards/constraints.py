from __future__ import annotations

from typing import Iterable, Tuple


def incompatible_pairs_ok(selected_ids: Iterable[str], pairs: Iterable[Tuple[str, str]]) -> bool:
    selected = set(selected_ids)
    return not any(a in selected and b in selected for a, b in pairs)
