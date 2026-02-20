"""Integration tests for CreateVariant, DeleteCard, and RenderMapSvg use cases.

These tests exercise use cases with real repository wiring (InMemory)
and real domain validation end-to-end.
"""

from __future__ import annotations

import pytest
from application.use_cases.create_variant import (
    CreateVariant,
    CreateVariantRequest,
    CreateVariantResponse,
)
from application.use_cases.delete_card import (
    DeleteCard,
    DeleteCardRequest,
    DeleteCardResponse,
)
from application.use_cases.render_map_svg import (
    RenderMapSvg,
    RenderMapSvgRequest,
    RenderMapSvgResponse,
)
from domain.cards.card import Card, GameMode
from domain.errors import ForbiddenError, NotFoundError, ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.generators.secure_seed_generator import SecureSeedGenerator
from infrastructure.generators.uuid_id_generator import UuidIdGenerator
from infrastructure.maps.svg_map_renderer import SvgMapRenderer
from infrastructure.repositories.in_memory_card_repository import (
    InMemoryCardRepository,
)
from infrastructure.scenario_generation.basic_scenario_generator import (
    BasicScenarioGenerator,
)


# =============================================================================
# HELPERS
# =============================================================================
def _make_card(
    card_id: str,
    owner_id: str = "u1",
    visibility: Visibility = Visibility.PRIVATE,
    seed: int = 42,
) -> Card:
    table = TableSize.standard()
    shapes = [{"type": "rect", "x": 10, "y": 10, "width": 200, "height": 200}]
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=seed,
        table=table,
        map_spec=MapSpec(table=table, shapes=shapes),
    )


# =============================================================================
# CreateVariant USE CASE
# =============================================================================
class TestCreateVariantUseCase:
    """Integration: CreateVariant with real repos + generators."""

    def test_creates_variant_from_base(self) -> None:
        repo = InMemoryCardRepository()
        base = _make_card("base-1", owner_id="u1")
        repo.save(base)

        uc = CreateVariant(
            repository=repo,
            id_generator=UuidIdGenerator(),
            seed_generator=SecureSeedGenerator(),
            scenario_generator=BasicScenarioGenerator(),
        )
        resp = uc.execute(
            CreateVariantRequest(actor_id="u1", base_card_id="base-1", seed=999)
        )

        assert isinstance(resp, CreateVariantResponse)
        assert resp.owner_id == "u1"
        assert resp.seed == 999
        assert resp.card_id != "base-1"  # New ID
        # Variant is persisted
        assert repo.get_by_id(resp.card_id) is not None

    def test_variant_auto_generates_seed(self) -> None:
        repo = InMemoryCardRepository()
        base = _make_card("base-1", owner_id="u1")
        repo.save(base)

        uc = CreateVariant(
            repository=repo,
            id_generator=UuidIdGenerator(),
            seed_generator=SecureSeedGenerator(),
            scenario_generator=BasicScenarioGenerator(),
        )
        resp = uc.execute(
            CreateVariantRequest(actor_id="u1", base_card_id="base-1", seed=None)
        )

        assert resp.seed > 0

    def test_non_owner_cannot_create_variant(self) -> None:
        repo = InMemoryCardRepository()
        base = _make_card("base-1", owner_id="u1")
        repo.save(base)

        uc = CreateVariant(
            repository=repo,
            id_generator=UuidIdGenerator(),
            seed_generator=SecureSeedGenerator(),
            scenario_generator=BasicScenarioGenerator(),
        )
        with pytest.raises(ForbiddenError):
            uc.execute(
                CreateVariantRequest(actor_id="u2", base_card_id="base-1", seed=1)
            )

    def test_missing_base_card_raises(self) -> None:
        repo = InMemoryCardRepository()

        uc = CreateVariant(
            repository=repo,
            id_generator=UuidIdGenerator(),
            seed_generator=SecureSeedGenerator(),
            scenario_generator=BasicScenarioGenerator(),
        )
        with pytest.raises(NotFoundError):
            uc.execute(
                CreateVariantRequest(actor_id="u1", base_card_id="nonexist", seed=1)
            )

    def test_invalid_actor_id_raises(self) -> None:
        repo = InMemoryCardRepository()

        uc = CreateVariant(
            repository=repo,
            id_generator=UuidIdGenerator(),
            seed_generator=SecureSeedGenerator(),
            scenario_generator=BasicScenarioGenerator(),
        )
        with pytest.raises(ValidationError):
            uc.execute(CreateVariantRequest(actor_id="", base_card_id="base-1", seed=1))


# =============================================================================
# DeleteCard USE CASE
# =============================================================================
class TestDeleteCardUseCase:
    """Integration: DeleteCard with InMemoryCardRepository."""

    def test_owner_can_delete(self) -> None:
        repo = InMemoryCardRepository()
        card = _make_card("c1", owner_id="u1")
        repo.save(card)

        uc = DeleteCard(repo)
        resp = uc.execute(DeleteCardRequest(actor_id="u1", card_id="c1"))

        assert isinstance(resp, DeleteCardResponse)
        assert resp.deleted is True
        assert resp.card_id == "c1"
        assert repo.get_by_id("c1") is None

    def test_non_owner_cannot_delete(self) -> None:
        repo = InMemoryCardRepository()
        card = _make_card("c1", owner_id="u1")
        repo.save(card)

        uc = DeleteCard(repo)
        with pytest.raises(ForbiddenError):
            uc.execute(DeleteCardRequest(actor_id="u2", card_id="c1"))

    def test_delete_nonexistent_card_raises(self) -> None:
        repo = InMemoryCardRepository()

        uc = DeleteCard(repo)
        with pytest.raises(NotFoundError):
            uc.execute(DeleteCardRequest(actor_id="u1", card_id="nonexist"))


# =============================================================================
# RenderMapSvg USE CASE
# =============================================================================
class TestRenderMapSvgUseCase:
    """Integration: RenderMapSvg with real renderer."""

    def test_render_own_card(self) -> None:
        repo = InMemoryCardRepository()
        card = _make_card("c1", owner_id="u1")
        repo.save(card)

        uc = RenderMapSvg(repository=repo, renderer=SvgMapRenderer())
        resp = uc.execute(RenderMapSvgRequest(actor_id="u1", card_id="c1"))

        assert isinstance(resp, RenderMapSvgResponse)
        assert "<svg" in resp.svg
        assert "</svg>" in resp.svg

    def test_render_public_card_by_non_owner(self) -> None:
        repo = InMemoryCardRepository()
        card = _make_card("c1", owner_id="u1", visibility=Visibility.PUBLIC)
        repo.save(card)

        uc = RenderMapSvg(repository=repo, renderer=SvgMapRenderer())
        resp = uc.execute(RenderMapSvgRequest(actor_id="u2", card_id="c1"))
        assert "<svg" in resp.svg

    def test_render_card_with_all_shape_types(self) -> None:
        """Card with deployment, objective, and scenography shapes."""
        repo = InMemoryCardRepository()
        table = TableSize.standard()
        map_spec = MapSpec(
            table=table,
            shapes=[{"type": "rect", "x": 10, "y": 10, "width": 100, "height": 100}],
            deployment_shapes=[
                {
                    "type": "rect",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 200,
                    "border": "north",
                    "description": "Deploy A",
                }
            ],
            objective_shapes=[
                {
                    "type": "objective_point",
                    "cx": 600,
                    "cy": 600,
                    "description": "Objective",
                }
            ],
        )
        card = Card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
            shared_with=None,
            mode=GameMode.MATCHED,
            seed=42,
            table=table,
            map_spec=map_spec,
        )
        repo.save(card)

        uc = RenderMapSvg(repository=repo, renderer=SvgMapRenderer())
        resp = uc.execute(RenderMapSvgRequest(actor_id="u1", card_id="c1"))
        assert "<svg" in resp.svg

    def test_render_forbidden_private_card(self) -> None:
        repo = InMemoryCardRepository()
        card = _make_card("c1", owner_id="u1", visibility=Visibility.PRIVATE)
        repo.save(card)

        uc = RenderMapSvg(repository=repo, renderer=SvgMapRenderer())
        with pytest.raises(ForbiddenError):
            uc.execute(RenderMapSvgRequest(actor_id="u2", card_id="c1"))

    def test_render_missing_card_raises(self) -> None:
        repo = InMemoryCardRepository()
        uc = RenderMapSvg(repository=repo, renderer=SvgMapRenderer())
        with pytest.raises(NotFoundError):
            uc.execute(RenderMapSvgRequest(actor_id="u1", card_id="nonexist"))
