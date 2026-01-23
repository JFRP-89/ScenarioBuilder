from __future__ import annotations

from src.application.ports.repositories import CardRepository


def execute(repo: CardRepository, owner_id: str):
    return list(repo.list_for_owner(owner_id))
