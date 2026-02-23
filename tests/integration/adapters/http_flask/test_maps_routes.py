"""Integration tests for Flask maps routes contract.

Tests cover GET /cards/<card_id>/map.svg — render a card's map as SVG.
All endpoints require a valid session.  Services come from app.config["services"].
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from adapters.http_flask.app import create_app
from helpers.fakes import FakeUseCase
from helpers.flask_helpers import assert_auth_required


# =============================================================================
# FAKES
# =============================================================================
@dataclass
class FakeRenderMapSvgResponse:
    """Fake response from RenderMapSvg."""

    svg: str = "<svg xmlns='http://www.w3.org/2000/svg'></svg>"


@dataclass
class FakeServices:
    """Fake Services container for testing."""

    render_map_svg: FakeUseCase | None = None
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
@pytest.fixture(name="fake_render")
def _provide_fake_render():
    return FakeUseCase(response=FakeRenderMapSvgResponse())


@pytest.fixture(name="fake_services")
def _provide_fake_services(fake_render):
    return FakeServices(render_map_svg=fake_render)


@pytest.fixture(name="client")
def _make_maps_client(fake_services, session_factory):
    """Create test client with fake services and session."""
    app = create_app()
    app.config["services"] = fake_services
    c = app.test_client()
    session_factory(c, "u1")
    return c


# =============================================================================
# TEST: GET /cards/<card_id>/map.svg
# =============================================================================
class TestGetMapSvg:
    """Full contract for the map SVG endpoint."""

    def test_missing_auth_returns_401(self, fake_services):
        """GET without session cookie should return 401."""
        app = create_app()
        app.config["services"] = fake_services
        unauth_client = app.test_client()

        response = unauth_client.get("/cards/card-001/map.svg")
        assert_auth_required(response)

    def test_happy_path_returns_200_and_svg_content_type(self, client, fake_render):
        """GET should return 200 with SVG content."""
        response = client.get("/cards/card-001/map.svg")

        assert response.status_code == 200, "Valid GET should return 200"

        content_type = response.headers.get("Content-Type", "")
        assert (
            "image/svg+xml" in content_type
        ), f"Content-Type should be image/svg+xml, got {content_type}"

        body = response.data.decode("utf-8")
        assert "<svg" in body, "Response body should contain SVG markup"

        assert (
            fake_render.call_count == 1
        ), "render_map_svg.execute() should be called once"
        assert fake_render.last_request is not None, "Request should be captured"
        assert fake_render.last_request.actor_id == "u1", "actor_id should be passed"
        assert (
            fake_render.last_request.card_id == "card-001"
        ), "card_id should be passed"

    def test_not_found_returns_404(self, session_factory):
        """GET should return 404 if card not found."""
        fake_render_nf = FakeUseCase(
            error=RuntimeError("Card not found"),
        )
        services = FakeServices(render_map_svg=fake_render_nf)
        app = create_app()
        app.config["services"] = services
        test_client = app.test_client()
        session_factory(test_client, "u1")

        response = test_client.get("/cards/card-404/map.svg")

        assert response.status_code == 404, "Card not found should return 404"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"

    def test_forbidden_returns_403(self, session_factory):
        """GET should return 403 if access forbidden."""
        fake_render_fb = FakeUseCase(
            error=RuntimeError("Forbidden"),
        )
        services = FakeServices(render_map_svg=fake_render_fb)
        app = create_app()
        app.config["services"] = services
        test_client = app.test_client()
        session_factory(test_client, "u1")

        response = test_client.get("/cards/card-private/map.svg")

        assert response.status_code == 403, "Forbidden should return 403"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"
