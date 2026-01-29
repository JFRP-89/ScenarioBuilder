from domain.cards.generator import generate_card
from src.infrastructure.content.file_content_provider import FileContentProvider


def test_seed_determinism():
    provider = FileContentProvider()
    card_a = generate_card(
        "casual",
        42,
        list(provider.get_layouts()),
        list(provider.get_deployments()),
        list(provider.get_objectives()),
        list(provider.get_twists()),
        list(provider.get_story_hooks()),
        list(provider.get_constraints()),
    )
    card_b = generate_card(
        "casual",
        42,
        list(provider.get_layouts()),
        list(provider.get_deployments()),
        list(provider.get_objectives()),
        list(provider.get_twists()),
        list(provider.get_story_hooks()),
        list(provider.get_constraints()),
    )
    assert card_a.layout.id == card_b.layout.id
