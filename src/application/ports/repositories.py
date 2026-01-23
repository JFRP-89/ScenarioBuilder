from __future__ import annotations

from typing import Iterable, Protocol

from src.domain.cards.models import ScenarioCard


class CardRepository(Protocol):
    def save(self, card: ScenarioCard, owner_id: str) -> None: ...

    def list_for_owner(self, owner_id: str) -> Iterable[ScenarioCard]: ...
