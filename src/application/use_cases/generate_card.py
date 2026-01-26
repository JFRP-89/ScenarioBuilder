from __future__ import annotations

from application.ports.content_provider import ContentProvider
from domain.cards.generator import generate_card


def execute(mode: str, seed: int, content: ContentProvider):
    return generate_card(
        mode,
        seed,
        list(content.get_layouts()),
        list(content.get_deployments()),
        list(content.get_objectives()),
        list(content.get_twists()),
        list(content.get_story_hooks()),
        list(content.get_constraints()),
    )
