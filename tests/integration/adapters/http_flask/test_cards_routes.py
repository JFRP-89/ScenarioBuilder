"""Integration tests for Flask cards routes contract.

Tests cover:
- POST /cards — create a new card
- GET /cards/<card_id> — retrieve a card by ID
- GET /cards?filter=... — list cards by filter

All endpoints require a valid session.  Services come from app.config["services"].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Optional, Union

import pytest

from adapters.http_flask.app import create_app
from helpers.fakes import FakeUseCase
from helpers.flask_helpers import assert_auth_required, csrf_token_of, store_csrf_token


# =============================================================================
# RESPONSE DTOs
# =============================================================================
@dataclass
class FakeGenerateResponse:
    """Fake response from GenerateScenarioCard.

    Structure matches production schema with shapes as nested dict.
    """

    card_id: str = "card-001"
    owner_id: str = "u1"
    seed: int = 123
    mode: str = "matched"
    visibility: str = "private"
    table_mm: dict = field(
        default_factory=lambda: {"width_mm": 1200, "height_mm": 1200}
    )
    shapes: dict = field(
        default_factory=lambda: {
            "deployment_shapes": [],
            "objective_shapes": [],
            "scenography_specs": [],
        }
    )
    card: object = None  # Card domain entity (will be mocked)
    name: str = "Battle Scenario"
    initial_priority: str = "Check the rulebook rules for it"
    table_preset: Optional[str] = None
    armies: Optional[str] = None
    shared_with: Optional[list] = None
    deployment: Optional[str] = None
    layout: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    special_rules: Optional[list[dict]] = None

    def __post_init__(self):
        """Create fake Card if not provided."""
        if self.card is None:
            self.card = type(
                "FakeCard",
                (),
                {
                    "card_id": self.card_id,
                    "owner_id": self.owner_id,
                    "seed": self.seed,
                    "mode": self.mode,
                    "visibility": self.visibility,
                },
            )()


@dataclass
class FakeGetCardResponse:
    """Fake response from GetCard."""

    card_id: str = "card-001"
    owner_id: str = "u1"
    seed: int = 123
    mode: str = "matched"
    visibility: str = "private"
    table_mm: Optional[dict] = None
    name: str = "Test Scenario"
    table_preset: str = "standard"
    shared_with: Optional[list] = None
    armies: Optional[str] = None
    deployment: Optional[str] = None
    layout: Optional[str] = None
    objectives: Optional[str] = None
    initial_priority: Optional[str] = None
    special_rules: Optional[list] = None
    shapes: Optional[dict] = None

    def __post_init__(self):
        if self.table_mm is None:
            self.table_mm = {"width_mm": 1200, "height_mm": 1200}
        if self.shared_with is None:
            self.shared_with = []


@dataclass
class FakeCardSnapshot:
    """Fake card snapshot for list results."""

    card_id: str
    owner_id: str
    seed: int
    mode: str
    visibility: str
    name: str = ""
    table_preset: str = "standard"
    table_mm: Optional[dict] = None

    def __post_init__(self):
        if self.table_mm is None:
            self.table_mm = {"width_mm": 1200, "height_mm": 1200}


@dataclass
class FakeListCardsResponse:
    """Fake response from ListCards."""

    cards: list = field(default_factory=list)


@dataclass
class FakeServices:
    """Fake Services container for testing."""

    generate_scenario_card: object = None
    save_card: object = None
    get_card: object = None
    list_cards: object = None
    toggle_favorite: object = None
    list_favorites: object = None
    create_variant: object = None
    render_map_svg: object = None


def _default_card_snapshots() -> list[FakeCardSnapshot]:
    """Build default card snapshots for list responses."""
    return [
        FakeCardSnapshot(
            card_id="card-001",
            owner_id="u1",
            seed=123,
            mode="matched",
            visibility="private",
        ),
        FakeCardSnapshot(
            card_id="card-002",
            owner_id="u1",
            seed=456,
            mode="casual",
            visibility="public",
        ),
    ]


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture(name="fake_generate")
def _provide_fake_generate():
    """Fake GenerateScenarioCard use case."""
    return FakeUseCase(response=FakeGenerateResponse())


@pytest.fixture(name="fake_save")
def _provide_fake_save():
    """Fake SaveCard use case."""
    return FakeUseCase(response=SimpleNamespace(card_id="card-001"))


@pytest.fixture(name="fake_get")
def _provide_fake_get():
    """Fake GetCard use case."""
    return FakeUseCase(response=FakeGetCardResponse())


@pytest.fixture(name="fake_list")
def _provide_fake_list():
    """Fake ListCards use case."""
    return FakeUseCase(
        response=FakeListCardsResponse(cards=_default_card_snapshots()),
    )


@pytest.fixture(name="fake_services")
def _provide_fake_services(fake_generate, fake_save, fake_get, fake_list):
    """Assemble all fakes into a FakeServices container."""
    return FakeServices(
        generate_scenario_card=fake_generate,
        save_card=fake_save,
        get_card=fake_get,
        list_cards=fake_list,
    )


@pytest.fixture(name="client")
def _make_cards_client(fake_services, monkeypatch, session_factory):
    """Create test client with fake services injected."""
    monkeypatch.setattr(
        "adapters.http_flask.app.build_services",
        lambda: fake_services,
    )
    app = create_app()
    app.config["services"] = fake_services
    c = app.test_client()
    auth = session_factory(c, "u1")
    store_csrf_token(c, auth["csrf_token"])
    return c


# =============================================================================
# TEST: POST /cards
# =============================================================================
class TestPostCards:
    """Tests for POST /cards endpoint."""

    def test_missing_auth_returns_401(self, fake_services, monkeypatch):
        """POST /cards without session cookie should return 401."""
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services",
            lambda: fake_services,
        )
        app = create_app()
        app.config["services"] = fake_services
        unauth_client = app.test_client()

        response = unauth_client.post(
            "/cards",
            json={"mode": "matched", "seed": 123, "table_preset": "standard"},
        )

        assert_auth_required(response)

    def test_calls_generate_and_returns_201(
        self,
        client,
        fake_generate,
        fake_save,
    ):
        """POST /cards should call generate use case and return 201."""
        response = client.post(
            "/cards",
            json={
                "mode": "matched",
                "seed": 123,
                "table_preset": "standard",
                "visibility": "private",
            },
            headers={"X-CSRF-Token": csrf_token_of(client)},
        )

        assert response.status_code == 201, "Valid POST should return 201"

        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "card_id" in json_data, "Response should contain card_id"
        assert "owner_id" in json_data, "Response should contain owner_id"
        assert "seed" in json_data, "Response should contain seed"
        assert "mode" in json_data, "Response should contain mode"
        assert "visibility" in json_data, "Response should contain visibility"

        assert (
            fake_generate.call_count == 1
        ), "generate_scenario_card.execute() should be called once"
        assert fake_generate.last_request is not None, "Request should be captured"
        assert (
            fake_generate.last_request.actor_id == "u1"
        ), "actor_id should be passed from header"
        assert fake_save.call_count == 1
        assert fake_save.last_request is not None
        assert fake_save.last_request.actor_id == "u1"
        assert fake_save.last_request.card is not None
        assert fake_save.last_request.card.card_id == json_data["card_id"]

    def test_passes_request_fields_to_use_case(self, client, fake_generate):
        """POST /cards should pass all fields to the use case.

        Note: seed is NOT passed from the client payload.
        It's calculated internally based on is_replicable flag.
        """
        response = client.post(
            "/cards",
            json={
                "mode": "narrative",
                "is_replicable": True,
                "table_preset": "massive",
                "visibility": "public",
            },
            headers={"X-CSRF-Token": csrf_token_of(client)},
        )

        assert response.status_code == 201
        req = fake_generate.last_request
        assert req.mode == "narrative", "mode should be passed"
        assert req.is_replicable is True, "is_replicable should be passed"
        assert (
            req.seed is None
        ), "seed should be None for new cards (calculated internally)"
        assert req.table_preset == "massive", "table_preset should be passed"
        assert req.visibility == "public", "visibility should be passed"


# =============================================================================
# TEST: GET /cards/<card_id>
# =============================================================================
class TestGetCard:
    """Tests for GET /cards/<card_id> endpoint."""

    def test_happy_path_returns_200(self, client, fake_get):
        """GET /cards/<card_id> should return 200 with card data."""
        response = client.get("/cards/card-001")

        assert response.status_code == 200, "Valid GET should return 200"

        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert json_data.get("card_id") == "card-001", "card_id should match"
        assert "owner_id" in json_data, "Response should contain owner_id"
        assert "seed" in json_data, "Response should contain seed"
        assert "mode" in json_data, "Response should contain mode"
        assert "visibility" in json_data, "Response should contain visibility"

        assert fake_get.call_count == 1, "get_card.execute() should be called once"
        assert fake_get.last_request.card_id == "card-001"
        assert fake_get.last_request.actor_id == "u1"

    def test_not_found_returns_404(self, monkeypatch, session_factory):
        """GET /cards/<card_id> should return 404 if card not found."""
        fake_get_not_found = FakeUseCase(
            error=RuntimeError("Card not found"),
        )
        services = FakeServices(
            generate_scenario_card=FakeUseCase(response=FakeGenerateResponse()),
            save_card=FakeUseCase(
                response=SimpleNamespace(card_id="card-001"),
            ),
            get_card=fake_get_not_found,
            list_cards=FakeUseCase(
                response=FakeListCardsResponse(
                    cards=_default_card_snapshots(),
                ),
            ),
        )
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services",
            lambda: services,
        )
        app = create_app()
        app.config["services"] = services
        test_client = app.test_client()
        session_factory(test_client, "u1")

        response = test_client.get("/cards/card-404")

        assert response.status_code == 404, "Card not found should return 404"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"

    def test_missing_auth_returns_401(self, fake_services, monkeypatch):
        """GET /cards/<card_id> without session cookie should return 401."""
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services",
            lambda: fake_services,
        )
        app = create_app()
        app.config["services"] = fake_services
        unauth_client = app.test_client()

        response = unauth_client.get("/cards/card-001")

        assert_auth_required(response)


# =============================================================================
# TEST: GET /cards?filter=...
# =============================================================================
class TestListCards:
    """Tests for GET /cards?filter=... endpoint."""

    def test_returns_cards_array_200(self, client, fake_list):
        """GET /cards?filter=mine should return 200 with cards array."""
        response = client.get("/cards?filter=mine")

        assert response.status_code == 200, "Valid GET should return 200"

        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "cards" in json_data, "Response should contain 'cards' key"
        assert isinstance(json_data["cards"], list), "cards should be a list"
        assert len(json_data["cards"]) == 2, "Should return 2 cards from fake"

        assert fake_list.call_count == 1
        assert fake_list.last_request.actor_id == "u1"
        assert fake_list.last_request.filter == "mine"

    def test_public_filter(self, client, fake_list):
        """GET /cards?filter=public should pass correct filter to use case."""
        response = client.get("/cards?filter=public")

        assert response.status_code == 200
        assert fake_list.last_request.filter == "public"

    def test_shared_with_me_filter(self, client, fake_list):
        """GET /cards?filter=shared_with_me should pass correct filter."""
        response = client.get("/cards?filter=shared_with_me")

        assert response.status_code == 200
        assert fake_list.last_request.filter == "shared_with_me"

    def test_missing_auth_returns_401(self, fake_services, monkeypatch):
        """GET /cards without session cookie should return 401."""
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services",
            lambda: fake_services,
        )
        app = create_app()
        app.config["services"] = fake_services
        unauth_client = app.test_client()

        response = unauth_client.get("/cards?filter=mine")

        assert_auth_required(response)
