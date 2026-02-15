"""RED tests for Flask maps routes contract.

These tests define the expected contract for maps API endpoints:
- GET /cards/<card_id>/map.svg - render a card's map as SVG

All endpoints require X-Actor-Id header and use services from app.config["services"].
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from adapters.http_flask.app import create_app


# =============================================================================
# FAKE USE CASES (SPY PATTERN)
# =============================================================================
@dataclass
class FakeRenderMapSvgResponse:
    """Fake response from RenderMapSvg."""

    svg: str = "<svg xmlns='http://www.w3.org/2000/svg'></svg>"


class FakeRenderMapSvg:
    """Fake RenderMapSvg use case."""

    def __init__(
        self,
        response: FakeRenderMapSvgResponse | None = None,
        raise_not_found: bool = False,
        raise_forbidden: bool = False,
    ):
        self.last_request = None
        self.call_count = 0
        self._response = response or FakeRenderMapSvgResponse()
        self._raise_not_found = raise_not_found
        self._raise_forbidden = raise_forbidden

    def execute(self, request):
        self.last_request = request
        self.call_count += 1
        if self._raise_not_found:
            raise Exception(f"Card not found: {request.card_id}")
        if self._raise_forbidden:
            raise Exception("Forbidden")
        return self._response


@dataclass
class FakeServices:
    """Fake Services container for testing."""

    # Required for maps tests
    render_map_svg: FakeRenderMapSvg | None = None
    # Other use cases (stubs)
    generate_scenario_card: object | None = None
    save_card: object | None = None
    get_card: object | None = None
    list_cards: object | None = None
    toggle_favorite: object | None = None
    list_favorites: object | None = None
    create_variant: object | None = None


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def fake_render():
    return FakeRenderMapSvg()


@pytest.fixture
def fake_services(fake_render):
    return FakeServices(render_map_svg=fake_render)


@pytest.fixture
def client(fake_services, session_factory):
    """Create test client with fake services and session."""
    app = create_app()
    app.config["services"] = fake_services
    c = app.test_client()
    session_factory(c, "u1")
    return c


# =============================================================================
# TEST: GET /cards/<card_id>/map.svg - missing actor ID
# =============================================================================
class TestGetMapSvgMissingActorId:
    """Test GET /cards/<card_id>/map.svg without valid session (auth middleware)."""

    def test_get_map_svg_missing_auth_returns_401(self, fake_services):
        """GET /cards/<card_id>/map.svg without session cookie should return 401."""
        app = create_app()
        app.config["services"] = fake_services
        unauth_client = app.test_client()

        # Act
        response = unauth_client.get("/cards/card-001/map.svg")

        # Assert
        assert response.status_code == 401, "Missing auth should return 401"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert json_data.get("ok") is False
        assert json_data.get("message") == "Authentication required."


# =============================================================================
# TEST: GET /cards/<card_id>/map.svg - happy path
# =============================================================================
class TestGetMapSvgHappyPath:
    """Test GET /cards/<card_id>/map.svg with valid request."""

    def test_get_map_svg_happy_path_returns_200_and_svg_content_type(
        self, client, fake_render
    ):
        """GET /cards/<card_id>/map.svg should return 200 with SVG content."""
        # Act
        response = client.get("/cards/card-001/map.svg")

        # Assert: status code
        assert response.status_code == 200, "Valid GET should return 200"

        # Assert: Content-Type header
        content_type = response.headers.get("Content-Type", "")
        assert (
            "image/svg+xml" in content_type
        ), f"Content-Type should be image/svg+xml, got {content_type}"

        # Assert: body contains SVG
        body = response.data.decode("utf-8")
        assert "<svg" in body, "Response body should contain SVG markup"

        # Assert: use case was called
        assert (
            fake_render.call_count == 1
        ), "render_map_svg.execute() should be called once"
        assert fake_render.last_request is not None, "Request should be captured"
        assert fake_render.last_request.actor_id == "u1", "actor_id should be passed"
        assert (
            fake_render.last_request.card_id == "card-001"
        ), "card_id should be passed"


# =============================================================================
# TEST: GET /cards/<card_id>/map.svg - not found
# =============================================================================
class TestGetMapSvgNotFound:
    """Test GET /cards/<card_id>/map.svg when card doesn't exist."""

    def test_get_map_svg_not_found_returns_404(self, session_factory):
        """GET /cards/<card_id>/map.svg should return 404 if card not found."""
        # Arrange: create fake that raises not found
        fake_render_not_found = FakeRenderMapSvg(raise_not_found=True)
        fake_services = FakeServices(render_map_svg=fake_render_not_found)
        app = create_app()
        app.config["services"] = fake_services
        client = app.test_client()
        session_factory(client, "u1")

        # Act
        response = client.get("/cards/card-404/map.svg")

        # Assert
        assert response.status_code == 404, "Card not found should return 404"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"


# =============================================================================
# TEST: GET /cards/<card_id>/map.svg - forbidden
# =============================================================================
class TestGetMapSvgForbidden:
    """Test GET /cards/<card_id>/map.svg when user doesn't have access."""

    def test_get_map_svg_forbidden_returns_403(self, session_factory):
        """GET /cards/<card_id>/map.svg should return 403 if access forbidden."""
        # Arrange: create fake that raises forbidden
        fake_render_forbidden = FakeRenderMapSvg(raise_forbidden=True)
        fake_services = FakeServices(render_map_svg=fake_render_forbidden)
        app = create_app()
        app.config["services"] = fake_services
        client = app.test_client()
        session_factory(client, "u1")

        # Act
        response = client.get("/cards/card-private/map.svg")

        # Assert
        assert response.status_code == 403, "Forbidden should return 403"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"
