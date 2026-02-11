"""Infrastructure bootstrap / composition root.

Wires up all use cases with their infrastructure dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

# Use cases
from application.use_cases.create_variant import CreateVariant
from application.use_cases.delete_card import DeleteCard
from application.use_cases.generate_scenario_card import GenerateScenarioCard
from application.use_cases.get_card import GetCard
from application.use_cases.list_cards import ListCards
from application.use_cases.list_favorites import ListFavorites
from application.use_cases.render_map_svg import RenderMapSvg
from application.use_cases.save_card import SaveCard
from application.use_cases.toggle_favorite import ToggleFavorite

# Infrastructure generators
from infrastructure.generators.secure_seed_generator import SecureSeedGenerator
from infrastructure.generators.uuid_id_generator import UuidIdGenerator

# Infrastructure rendering
from infrastructure.maps.svg_map_renderer import SvgMapRenderer

# Infrastructure repositories
from infrastructure.repositories.in_memory_card_repository import InMemoryCardRepository
from infrastructure.repositories.in_memory_favorites_repository import (
    InMemoryFavoritesRepository,
)

# Infrastructure scenario generation
from infrastructure.scenario_generation.basic_scenario_generator import (
    BasicScenarioGenerator,
)


# =============================================================================
# SERVICES CONTAINER
# =============================================================================
@dataclass(frozen=True)
class Services:
    """Container for all application use cases."""

    # Core use cases
    generate_scenario_card: GenerateScenarioCard
    save_card: SaveCard
    get_card: GetCard

    # Optional use cases
    list_cards: ListCards
    toggle_favorite: ToggleFavorite
    list_favorites: ListFavorites
    create_variant: CreateVariant
    render_map_svg: RenderMapSvg
    delete_card: DeleteCard


# =============================================================================
# COMPOSITION ROOT
# =============================================================================
def build_services() -> Services:
    """Build and wire all use cases with their dependencies.

    Each call to build_services() creates independent instances
    with their own repository state.

    Returns:
        Services container with all use cases wired up.
    """
    # 1) Build infrastructure dependencies
    card_repo = InMemoryCardRepository()
    favorites_repo = InMemoryFavoritesRepository()
    id_gen = UuidIdGenerator()
    seed_gen = SecureSeedGenerator()
    scenario_gen = BasicScenarioGenerator()
    renderer = SvgMapRenderer()

    # 2) Build use cases with dependencies
    generate_scenario_card = GenerateScenarioCard(
        id_generator=id_gen,
        seed_generator=seed_gen,
        scenario_generator=scenario_gen,
    )

    save_card = SaveCard(repository=card_repo)

    get_card = GetCard(repository=card_repo)

    list_cards = ListCards(repository=card_repo)

    toggle_favorite = ToggleFavorite(
        card_repository=card_repo,
        favorites_repository=favorites_repo,
    )

    list_favorites = ListFavorites(
        card_repository=card_repo,
        favorites_repository=favorites_repo,
    )

    create_variant = CreateVariant(
        repository=card_repo,
        id_generator=id_gen,
        seed_generator=seed_gen,
        scenario_generator=scenario_gen,
    )

    render_map_svg = RenderMapSvg(
        repository=card_repo,
        renderer=renderer,
    )

    delete_card = DeleteCard(repository=card_repo)

    # 3) Return services container
    return Services(
        generate_scenario_card=generate_scenario_card,
        save_card=save_card,
        get_card=get_card,
        list_cards=list_cards,
        toggle_favorite=toggle_favorite,
        list_favorites=list_favorites,
        create_variant=create_variant,
        render_map_svg=render_map_svg,
        delete_card=delete_card,
    )
