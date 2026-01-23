from __future__ import annotations

from src.application.ports.repositories import CardRepository


def execute(repo: CardRepository, card, owner_id: str) -> None:
    repo.save(card, owner_id)
