from __future__ import annotations

from typing import List

from domain.seed import get_rng
from domain.cards.models import CardItem, ScenarioCard


def _pick(rng, items: List[CardItem]) -> CardItem:
    if not items:
        raise ValueError("No items to pick from")
    return rng.choice(items)


def generate_card(mode: str, seed: int, layouts, deployments, objectives, twists, story_hooks, constraints) -> ScenarioCard:
    rng = get_rng(seed)
    return ScenarioCard(
        id=f"card-{seed}",
        mode=mode,
        seed=seed,
        layout=_pick(rng, layouts),
        deployment=_pick(rng, deployments),
        objective=_pick(rng, objectives),
        twist=_pick(rng, twists) if twists else None,
        story_hook=_pick(rng, story_hooks) if story_hooks else None,
        constraints=constraints[:2],
    )
