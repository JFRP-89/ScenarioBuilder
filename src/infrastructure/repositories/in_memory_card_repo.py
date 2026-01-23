from __future__ import annotations

from typing import Dict, List

from src.domain.cards.models import ScenarioCard


class InMemoryCardRepository:
    def __init__(self) -> None:
        self._store: Dict[str, List[ScenarioCard]] = {}

    def save(self, card: ScenarioCard, owner_id: str) -> None:
        self._store.setdefault(owner_id, []).append(card)

    def list_for_owner(self, owner_id: str):
        return self._store.get(owner_id, [])
