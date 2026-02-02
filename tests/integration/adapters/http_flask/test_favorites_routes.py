"""RED tests for Flask favorites routes contract.

These tests define the expected contract for favorites API endpoints:
- POST /favorites/<card_id>/toggle - toggle favorite status for a card
- GET /favorites - list all favorite cards for the actor

All endpoints require X-Actor-Id header and use services from app.config["services"].

Expected error contract (handled by global error handlers in app.py):
- Missing X-Actor-Id header → 400 Bad Request (ValidationError)
- Exception with "forbidden" in message → 403 Forbidden
- Exception with "not found" in message → 404 Not Found

Blueprint registration expected:
- url_prefix="/favorites"
- Internal routes: "/<card_id>/toggle" (POST), "" (GET)

NOTE: These tests are RED (failing) because routes/favorites.py does not exist yet.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from adapters.http_flask.app import create_app
from application.use_cases.list_favorites import (
    ListFavoritesRequest,
    ListFavoritesResponse,
)
from application.use_cases.toggle_favorite import (
    ToggleFavoriteRequest,
    ToggleFavoriteResponse,
)


# =============================================================================
# FAKE USE CASES (SPY PATTERN)
# =============================================================================
class FakeToggleFavorite:
    """Fake ToggleFavorite use case for testing."""

    def __init__(
        self,
        response: ToggleFavoriteResponse | None = None,
        error: Exception | None = None,
    ):
        self.last_request: ToggleFavoriteRequest | None = None
        self.call_count = 0
        self._response = response or ToggleFavoriteResponse(
            card_id="card-001",
            is_favorite=True,
        )
        self._error = error

    def execute(self, request: ToggleFavoriteRequest) -> ToggleFavoriteResponse:
        self.last_request = request
        self.call_count += 1
        if self._error:
            raise self._error
        return self._response


class FakeListFavorites:
    """Fake ListFavorites use case for testing."""

    def __init__(
        self,
        response: ListFavoritesResponse | None = None,
        error: Exception | None = None,
    ):
        self.last_request: ListFavoritesRequest | None = None
        self.call_count = 0
        self._response = response or ListFavoritesResponse(
            card_ids=["card-001", "card-002"],
        )
        self._error = error

    def execute(self, request: ListFavoritesRequest) -> ListFavoritesResponse:
        self.last_request = request
        self.call_count += 1
        if self._error:
            raise self._error
        return self._response


@dataclass
class FakeServices:
    """Fake services object for testing favorites routes."""

    toggle_favorite: FakeToggleFavorite
    list_favorites: FakeListFavorites


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def fake_toggle():
    """Create a fake toggle_favorite use case."""
    return FakeToggleFavorite()


@pytest.fixture
def fake_list():
    """Create a fake list_favorites use case."""
    return FakeListFavorites()


@pytest.fixture
def client(fake_toggle, fake_list):
    """Create Flask test client with fake services."""
    app = create_app()

    # Inject fake services
    app.config["services"] = FakeServices(
        toggle_favorite=fake_toggle,
        list_favorites=fake_list,
    )

    with app.test_client() as test_client:
        yield test_client


# =============================================================================
# TESTS: POST /favorites/<card_id>/toggle - Missing Actor ID
# =============================================================================
class TestToggleFavoriteMissingActorId:
    """Tests for POST /favorites/<card_id>/toggle without X-Actor-Id header."""

    def test_post_toggle_missing_actor_id_returns_400(self, client):
        """POST /favorites/<card_id>/toggle without X-Actor-Id returns 400."""
        response = client.post("/favorites/card-001/toggle")

        assert response.status_code == 400, "Missing X-Actor-Id should return 400"


# =============================================================================
# TESTS: POST /favorites/<card_id>/toggle - Happy Path
# =============================================================================
class TestToggleFavoriteHappyPath:
    """Tests for POST /favorites/<card_id>/toggle happy path."""

    def test_post_toggle_returns_200_with_json(self, client, fake_toggle):
        """POST /favorites/<card_id>/toggle with valid header returns 200 + JSON."""
        response = client.post(
            "/favorites/card-001/toggle",
            headers={"X-Actor-Id": "u1"},
        )

        assert response.status_code == 200, "Valid POST should return 200"

        data = response.get_json()
        assert data is not None, "Response should be JSON"
        assert "card_id" in data, "Response should contain card_id"
        assert "is_favorite" in data, "Response should contain is_favorite"
        assert data["card_id"] == "card-001"
        assert isinstance(data["is_favorite"], bool)

    def test_post_toggle_calls_use_case_with_correct_request(self, client, fake_toggle):
        """POST /favorites/<card_id>/toggle passes correct data to use case."""
        response = client.post(
            "/favorites/card-001/toggle",
            headers={"X-Actor-Id": "u1"},
        )

        assert response.status_code == 200
        assert (
            fake_toggle.call_count == 1
        ), "toggle_favorite.execute() should be called once"
        assert fake_toggle.last_request is not None, "Request should be captured"

        # Validate request DTO fields
        assert fake_toggle.last_request.actor_id == "u1"
        assert fake_toggle.last_request.card_id == "card-001"


# =============================================================================
# TESTS: POST /favorites/<card_id>/toggle - Forbidden
# =============================================================================
class TestToggleFavoriteForbidden:
    """Tests for POST /favorites/<card_id>/toggle when use case raises forbidden."""

    @pytest.fixture
    def client_forbidden(self, fake_list):
        """Create client with toggle that raises forbidden error."""
        app = create_app()

        fake_toggle_error = FakeToggleFavorite(
            error=Exception("forbidden: cannot favorite private card")
        )

        app.config["services"] = FakeServices(
            toggle_favorite=fake_toggle_error,
            list_favorites=fake_list,
        )

        with app.test_client() as test_client:
            yield test_client

    def test_post_toggle_forbidden_returns_403(self, client_forbidden):
        """POST /favorites/<card_id>/toggle returns 403 when forbidden."""
        response = client_forbidden.post(
            "/favorites/card-001/toggle",
            headers={"X-Actor-Id": "u1"},
        )

        assert response.status_code == 403, "Forbidden should return 403"


# =============================================================================
# TESTS: GET /favorites - Missing Actor ID
# =============================================================================
class TestListFavoritesMissingActorId:
    """Tests for GET /favorites without X-Actor-Id header."""

    def test_get_favorites_missing_actor_id_returns_400(self, client):
        """GET /favorites without X-Actor-Id returns 400."""
        response = client.get("/favorites")

        assert response.status_code == 400, "Missing X-Actor-Id should return 400"


# =============================================================================
# TESTS: GET /favorites - Happy Path
# =============================================================================
class TestListFavoritesHappyPath:
    """Tests for GET /favorites happy path."""

    def test_get_favorites_returns_200_with_card_ids(self, client, fake_list):
        """GET /favorites with valid header returns 200 + JSON with card_ids."""
        response = client.get(
            "/favorites",
            headers={"X-Actor-Id": "u1"},
        )

        assert response.status_code == 200, "Valid GET should return 200"

        data = response.get_json()
        assert data is not None, "Response should be JSON"
        assert "card_ids" in data, "Response should contain card_ids"
        assert isinstance(data["card_ids"], list), "card_ids should be a list"
        assert data["card_ids"] == ["card-001", "card-002"]

    def test_get_favorites_calls_use_case_with_correct_request(self, client, fake_list):
        """GET /favorites passes correct data to use case."""
        response = client.get(
            "/favorites",
            headers={"X-Actor-Id": "u1"},
        )

        assert response.status_code == 200
        assert (
            fake_list.call_count == 1
        ), "list_favorites.execute() should be called once"
        assert fake_list.last_request is not None, "Request should be captured"

        # Validate request DTO fields
        assert fake_list.last_request.actor_id == "u1"


# =============================================================================
# TESTS: GET /favorites - Not Found
# =============================================================================
class TestListFavoritesNotFound:
    """Tests for GET /favorites when use case raises not found."""

    @pytest.fixture
    def client_not_found(self, fake_toggle):
        """Create client with list that raises not found error."""
        app = create_app()

        fake_list_error = FakeListFavorites(
            error=Exception("not found: card does not exist")
        )

        app.config["services"] = FakeServices(
            toggle_favorite=fake_toggle,
            list_favorites=fake_list_error,
        )

        with app.test_client() as test_client:
            yield test_client

    def test_get_favorites_not_found_returns_404(self, client_not_found):
        """GET /favorites returns 404 when not found."""
        response = client_not_found.get(
            "/favorites",
            headers={"X-Actor-Id": "u1"},
        )

        assert response.status_code == 404, "Not found should return 404"
