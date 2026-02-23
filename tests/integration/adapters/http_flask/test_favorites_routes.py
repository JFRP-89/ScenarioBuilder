"""Integration tests for Flask favorites routes contract.

Tests cover:
- POST /favorites/<card_id>/toggle — toggle favorite status for a card
- GET /favorites — list all favorite cards for the actor

All endpoints require a valid session.  Services come from app.config["services"].
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from adapters.http_flask.app import create_app
from application.use_cases.list_favorites import ListFavoritesResponse
from application.use_cases.toggle_favorite import ToggleFavoriteResponse
from helpers.fakes import FakeUseCase
from helpers.flask_helpers import csrf_token_of, store_csrf_token


# =============================================================================
# FAKES
# =============================================================================
@dataclass
class FakeServices:
    """Fake services object for testing favorites routes."""

    toggle_favorite: FakeUseCase
    list_favorites: FakeUseCase


def _default_toggle_response() -> ToggleFavoriteResponse:
    return ToggleFavoriteResponse(card_id="card-001", is_favorite=True)


def _default_list_response() -> ListFavoritesResponse:
    return ListFavoritesResponse(card_ids=["card-001", "card-002"])


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture(name="fake_toggle")
def _provide_fake_toggle():
    """Create a fake toggle_favorite use case."""
    return FakeUseCase(response=_default_toggle_response())


@pytest.fixture(name="fake_list")
def _provide_fake_list():
    """Create a fake list_favorites use case."""
    return FakeUseCase(response=_default_list_response())


@pytest.fixture(name="client")
def _make_favorites_client(fake_toggle, fake_list, session_factory):
    """Create Flask test client with fake services and session."""
    app = create_app()

    app.config["services"] = FakeServices(
        toggle_favorite=fake_toggle,
        list_favorites=fake_list,
    )

    with app.test_client() as test_client:
        auth = session_factory(test_client, "u1")
        store_csrf_token(test_client, auth["csrf_token"])
        yield test_client


# =============================================================================
# TESTS: POST /favorites/<card_id>/toggle
# =============================================================================
class TestToggleFavorite:
    """Tests for POST /favorites/<card_id>/toggle."""

    def test_missing_auth_returns_401(self, fake_toggle, fake_list):
        """POST without session returns 401."""
        app = create_app()
        app.config["services"] = FakeServices(
            toggle_favorite=fake_toggle,
            list_favorites=fake_list,
        )
        unauth_client = app.test_client()

        response = unauth_client.post("/favorites/card-001/toggle")

        assert response.status_code == 401, "Missing auth should return 401"

    def test_returns_200_with_json(self, client):
        """POST with valid session returns 200 + JSON."""
        response = client.post(
            "/favorites/card-001/toggle",
            headers={"X-CSRF-Token": csrf_token_of(client)},
        )

        assert response.status_code == 200, "Valid POST should return 200"

        data = response.get_json()
        assert data is not None, "Response should be JSON"
        assert "card_id" in data, "Response should contain card_id"
        assert "is_favorite" in data, "Response should contain is_favorite"
        assert data["card_id"] == "card-001"
        assert isinstance(data["is_favorite"], bool)

    def test_calls_use_case_with_correct_request(self, client, fake_toggle):
        """POST passes correct data to use case."""
        response = client.post(
            "/favorites/card-001/toggle",
            headers={"X-CSRF-Token": csrf_token_of(client)},
        )

        assert response.status_code == 200
        assert (
            fake_toggle.call_count == 1
        ), "toggle_favorite.execute() should be called once"
        assert fake_toggle.last_request is not None, "Request should be captured"

        assert fake_toggle.last_request.actor_id == "u1"
        assert fake_toggle.last_request.card_id == "card-001"

    @pytest.fixture(name="client_forbidden")
    def _make_forbidden_client(self, fake_list, session_factory):
        """Create client with toggle that raises forbidden error."""
        app = create_app()

        fake_toggle_error = FakeUseCase(
            error=RuntimeError("forbidden: cannot favorite private card"),
        )

        app.config["services"] = FakeServices(
            toggle_favorite=fake_toggle_error,
            list_favorites=fake_list,
        )

        with app.test_client() as test_client:
            auth = session_factory(test_client, "u1")
            store_csrf_token(test_client, auth["csrf_token"])
            yield test_client

    def test_forbidden_returns_403(self, client_forbidden):
        """POST returns 403 when forbidden."""
        response = client_forbidden.post(
            "/favorites/card-001/toggle",
            headers={"X-CSRF-Token": csrf_token_of(client_forbidden)},
        )

        assert response.status_code == 403, "Forbidden should return 403"


# =============================================================================
# TESTS: GET /favorites
# =============================================================================
class TestListFavorites:
    """Tests for GET /favorites."""

    def test_missing_auth_returns_401(self, fake_toggle, fake_list):
        """GET without session returns 401."""
        app = create_app()
        app.config["services"] = FakeServices(
            toggle_favorite=fake_toggle,
            list_favorites=fake_list,
        )
        unauth_client = app.test_client()

        response = unauth_client.get("/favorites")

        assert response.status_code == 401, "Missing auth should return 401"

    def test_returns_200_with_card_ids(self, client):
        """GET with valid session returns 200 + JSON with card_ids."""
        response = client.get("/favorites")

        assert response.status_code == 200, "Valid GET should return 200"

        data = response.get_json()
        assert data is not None, "Response should be JSON"
        assert "card_ids" in data, "Response should contain card_ids"
        assert isinstance(data["card_ids"], list), "card_ids should be a list"
        assert data["card_ids"] == ["card-001", "card-002"]

    def test_calls_use_case_with_correct_request(self, client, fake_list):
        """GET passes correct data to use case."""
        response = client.get("/favorites")

        assert response.status_code == 200
        assert (
            fake_list.call_count == 1
        ), "list_favorites.execute() should be called once"
        assert fake_list.last_request is not None, "Request should be captured"

        assert fake_list.last_request.actor_id == "u1"

    @pytest.fixture(name="client_not_found")
    def _make_not_found_client(self, fake_toggle, session_factory):
        """Create client with list that raises not found error."""
        app = create_app()

        fake_list_error = FakeUseCase(
            error=RuntimeError("not found: card does not exist"),
        )

        app.config["services"] = FakeServices(
            toggle_favorite=fake_toggle,
            list_favorites=fake_list_error,
        )

        with app.test_client() as test_client:
            session_factory(test_client, "u1")
            yield test_client

    def test_not_found_returns_404(self, client_not_found):
        """GET returns 404 when not found."""
        response = client_not_found.get("/favorites")

        assert response.status_code == 404, "Not found should return 404"
