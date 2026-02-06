"""RED tests for RenderMapSvg use case.

RenderMapSvg renders a Card's map to SVG format:
- Delegates rendering to a renderer port (does NOT render directly)
- Security: actor must be able to read the card (anti-IDOR)
- Returns SVG string
"""

from __future__ import annotations

from typing import Optional

import pytest
from domain.cards.card import Card, GameMode
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility


# =============================================================================
# TEST HELPERS
# =============================================================================
def make_valid_shapes() -> list[dict]:
    """Return shapes valid for TableSize.standard()."""
    return [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]


def make_valid_card(
    card_id: str = "c1",
    owner_id: str = "u1",
    visibility: Visibility = Visibility.PUBLIC,
    shared_with: Optional[frozenset[str]] = None,
) -> Card:
    """Create a valid Card for testing."""
    table = TableSize.standard()
    shapes = make_valid_shapes()
    map_spec = MapSpec(table=table, shapes=shapes)
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=shared_with or frozenset(),
        mode=GameMode.MATCHED,
        seed=123,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# FAKE REPOSITORIES AND RENDERERS
# =============================================================================
class FakeCardRepository:
    """In-memory card repository for testing."""

    def __init__(self) -> None:
        self._cards: dict[str, Card] = {}

    def add(self, card: Card) -> None:
        """Pre-populate repository with a card."""
        self._cards[card.card_id] = card

    def get_by_id(self, card_id: str) -> Optional[Card]:
        """Get card by id."""
        return self._cards.get(card_id)


class SpySvgRenderer:
    """Spy SVG renderer that tracks calls and returns configurable SVG."""

    def __init__(
        self, svg: str = "<svg></svg>", should_raise: Optional[Exception] = None
    ) -> None:
        self._svg = svg
        self._should_raise = should_raise
        self.calls: list[tuple[dict, list[dict]]] = []

    def render(self, table_mm: dict, shapes: list[dict]) -> str:
        """Render table and shapes to SVG, recording the call."""
        self.calls.append((table_mm, shapes))
        if self._should_raise:
            raise self._should_raise
        return self._svg


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def repo() -> FakeCardRepository:
    """Provide empty card repository."""
    return FakeCardRepository()


@pytest.fixture
def renderer() -> SpySvgRenderer:
    """Provide spy renderer."""
    return SpySvgRenderer("<svg></svg>")


# =============================================================================
# HAPPY PATH TESTS
# =============================================================================
class TestRenderMapSvgHappyPath:
    """Tests for successful SVG rendering."""

    def test_owner_can_render_private_card(
        self,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """Owner can render their own PRIVATE card."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
        )
        repo.add(card)

        request = RenderMapSvgRequest(actor_id="u1", card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act
        response = use_case.execute(request)

        # Assert response contains SVG
        assert "<svg" in response.svg

        # Assert renderer was called once
        assert len(renderer.calls) == 1
        table_mm, shapes = renderer.calls[0]

        # Assert table_mm has expected keys
        assert "width_mm" in table_mm or "width" in table_mm
        assert "height_mm" in table_mm or "height" in table_mm

        # Assert shapes match the card's map_spec shapes
        assert shapes == card.map_spec.shapes

    def test_non_owner_can_render_public_card(
        self,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """Non-owner can render PUBLIC card."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PUBLIC,
        )
        repo.add(card)

        request = RenderMapSvgRequest(actor_id="u2", card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act
        response = use_case.execute(request)

        # Assert
        assert "<svg" in response.svg
        assert len(renderer.calls) == 1

    def test_shared_user_can_render_shared_card(
        self,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """User in shared_with list can render SHARED card."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u2", "u3"}),
        )
        repo.add(card)

        request = RenderMapSvgRequest(actor_id="u2", card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act
        response = use_case.execute(request)

        # Assert
        assert "<svg" in response.svg
        assert len(renderer.calls) == 1


# =============================================================================
# SECURITY / FORBIDDEN TESTS
# =============================================================================
class TestRenderMapSvgForbidden:
    """Tests for authorization failures."""

    def test_non_owner_cannot_render_private_card(
        self,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """Non-owner cannot render PRIVATE card."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.PRIVATE,
        )
        repo.add(card)

        request = RenderMapSvgRequest(actor_id="u2", card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act & Assert
        with pytest.raises(Exception, match=r"(?i)forbidden|permission|access"):
            use_case.execute(request)

        # Assert renderer was NOT called
        assert len(renderer.calls) == 0

    def test_non_shared_user_cannot_render_shared_card(
        self,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """User not in shared_with cannot render SHARED card."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u3"}),  # u2 not in list
        )
        repo.add(card)

        request = RenderMapSvgRequest(actor_id="u2", card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act & Assert
        with pytest.raises(Exception, match=r"(?i)forbidden|permission|access"):
            use_case.execute(request)

        assert len(renderer.calls) == 0


# =============================================================================
# NOT FOUND TESTS
# =============================================================================
class TestRenderMapSvgNotFound:
    """Tests for card not found."""

    def test_card_not_found_raises_error(
        self,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """Error when card does not exist."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange: repo is empty
        request = RenderMapSvgRequest(actor_id="u1", card_id="nonexistent")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act & Assert
        with pytest.raises(Exception, match=r"(?i)not found|does not exist"):
            use_case.execute(request)

        assert len(renderer.calls) == 0


# =============================================================================
# VALIDATION ERROR TESTS
# =============================================================================
class TestRenderMapSvgInvalidActorId:
    """Tests for invalid actor_id validation."""

    @pytest.mark.parametrize("invalid_actor_id", [None, "", "   "])
    def test_invalid_actor_id_raises_validation_error(
        self,
        invalid_actor_id,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """Invalid actor_id raises ValidationError."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        request = RenderMapSvgRequest(actor_id=invalid_actor_id, card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act & Assert
        with pytest.raises(ValidationError, match=r"(?i)actor"):
            use_case.execute(request)

        assert len(renderer.calls) == 0


class TestRenderMapSvgInvalidCardId:
    """Tests for invalid card_id validation."""

    @pytest.mark.parametrize("invalid_card_id", [None, "", "   "])
    def test_invalid_card_id_raises_validation_error(
        self,
        invalid_card_id,
        repo: FakeCardRepository,
        renderer: SpySvgRenderer,
    ) -> None:
        """Invalid card_id raises ValidationError."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        request = RenderMapSvgRequest(actor_id="u1", card_id=invalid_card_id)
        use_case = RenderMapSvg(repository=repo, renderer=renderer)

        # Act & Assert
        with pytest.raises(ValidationError, match=r"(?i)card"):
            use_case.execute(request)

        assert len(renderer.calls) == 0


# =============================================================================
# RENDERER ERROR PROPAGATION TESTS
# =============================================================================
class TestRenderMapSvgRendererError:
    """Tests for renderer error handling."""

    def test_renderer_error_propagates(
        self,
        repo: FakeCardRepository,
    ) -> None:
        """Renderer exceptions propagate to caller."""
        from application.use_cases.render_map_svg import (
            RenderMapSvg,
            RenderMapSvgRequest,
        )

        # Arrange
        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        failing_renderer = SpySvgRenderer(should_raise=Exception("boom"))

        request = RenderMapSvgRequest(actor_id="u1", card_id="c1")
        use_case = RenderMapSvg(repository=repo, renderer=failing_renderer)

        # Act & Assert
        with pytest.raises(Exception, match="boom"):
            use_case.execute(request)

        # Renderer was called (error happened during render)
        assert len(failing_renderer.calls) == 1
