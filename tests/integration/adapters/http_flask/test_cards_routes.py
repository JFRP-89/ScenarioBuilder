"""RED tests for Flask cards routes contract.

These tests define the expected contract for cards API endpoints:
- POST /cards - create a new card
- GET /cards/<card_id> - retrieve a card by ID
- GET /cards?filter=... - list cards by filter

All endpoints require X-Actor-Id header and use services from app.config["services"].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

import pytest
from adapters.http_flask.app import create_app


# =============================================================================
# FAKE USE CASES (SPY PATTERN)
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
            # Create a minimal fake Card object
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


class FakeGenerateScenarioCard:
    """Fake GenerateScenarioCard use case."""

    def __init__(self, response: Optional[FakeGenerateResponse] = None):
        self.last_request = None
        self.call_count = 0
        self._response = response or FakeGenerateResponse()

    def execute(self, request):
        self.last_request = request
        self.call_count += 1
        return self._response


class FakeSaveCard:
    """Fake SaveCard use case."""

    def __init__(self):
        self.last_request = None
        self.call_count = 0

    def execute(self, request):
        self.last_request = request
        self.call_count += 1
        return type("SaveCardResponse", (), {"card_id": "card-001"})()


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


class FakeGetCard:
    """Fake GetCard use case."""

    def __init__(
        self,
        response: Optional[FakeGetCardResponse] = None,
        raise_not_found: bool = False,
    ):
        self.last_request = None
        self.call_count = 0
        self._response = response or FakeGetCardResponse()
        self._raise_not_found = raise_not_found

    def execute(self, request):
        self.last_request = request
        self.call_count += 1
        if self._raise_not_found:
            raise Exception(f"Card not found: {request.card_id}")
        return self._response


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


class FakeListCards:
    """Fake ListCards use case."""

    def __init__(self, cards: Optional[list] = None):
        self.last_request = None
        self.call_count = 0
        self._cards = cards or [
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

    def execute(self, request):
        self.last_request = request
        self.call_count += 1
        return FakeListCardsResponse(cards=self._cards)


@dataclass
class FakeServices:
    """Fake Services container for testing."""

    generate_scenario_card: Optional[FakeGenerateScenarioCard] = None
    save_card: Optional[FakeSaveCard] = None
    get_card: Optional[FakeGetCard] = None
    list_cards: Optional[FakeListCards] = None
    # Other use cases not needed for these tests
    toggle_favorite: object = None
    list_favorites: object = None
    create_variant: object = None
    render_map_svg: object = None


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def fake_generate():
    return FakeGenerateScenarioCard()


@pytest.fixture
def fake_save():
    return FakeSaveCard()


@pytest.fixture
def fake_get():
    return FakeGetCard()


@pytest.fixture
def fake_list():
    return FakeListCards()


@pytest.fixture
def fake_services(fake_generate, fake_save, fake_get, fake_list):
    return FakeServices(
        generate_scenario_card=fake_generate,
        save_card=fake_save,
        get_card=fake_get,
        list_cards=fake_list,
    )


@pytest.fixture
def client(fake_services, monkeypatch):
    """Create test client with fake services injected."""
    # Patch build_services to avoid real infra during app creation
    monkeypatch.setattr("adapters.http_flask.app.build_services", lambda: fake_services)
    app = create_app()
    # Override with our fake services (belt and suspenders)
    app.config["services"] = fake_services
    return app.test_client()


# =============================================================================
# TEST: POST /cards - missing actor ID
# =============================================================================
class TestPostCardsMissingActorId:
    """Test POST /cards without X-Actor-Id header."""

    def test_post_cards_missing_actor_id_returns_400(self, client):
        """POST /cards without X-Actor-Id should return 400."""
        # Act
        response = client.post(
            "/cards",
            json={"mode": "matched", "seed": 123, "table_preset": "standard"},
        )

        # Assert
        assert response.status_code == 400, "Missing X-Actor-Id should return 400"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"


# =============================================================================
# TEST: POST /cards - happy path
# =============================================================================
class TestPostCardsHappyPath:
    """Test POST /cards with valid request."""

    def test_post_cards_calls_generate_and_returns_201(
        self, client, fake_generate, fake_save
    ):
        """POST /cards should call generate use case and return 201."""
        # Act
        response = client.post(
            "/cards",
            json={
                "mode": "matched",
                "seed": 123,
                "table_preset": "standard",
                "visibility": "private",
            },
            headers={"X-Actor-Id": "u1"},
        )

        # Assert: status code
        assert response.status_code == 201, "Valid POST should return 201"

        # Assert: JSON structure
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "card_id" in json_data, "Response should contain card_id"
        assert "owner_id" in json_data, "Response should contain owner_id"
        assert "seed" in json_data, "Response should contain seed"
        assert "mode" in json_data, "Response should contain mode"
        assert "visibility" in json_data, "Response should contain visibility"

        # Assert: use case was called
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

    def test_post_cards_passes_request_fields_to_use_case(self, client, fake_generate):
        """POST /cards should pass all fields to the use case."""
        # Act
        response = client.post(
            "/cards",
            json={
                "mode": "narrative",
                "seed": 999,
                "table_preset": "massive",
                "visibility": "public",
            },
            headers={"X-Actor-Id": "actor-xyz"},
        )

        # Assert
        assert response.status_code == 201
        req = fake_generate.last_request
        assert req.mode == "narrative", "mode should be passed"
        assert req.seed == 999, "seed should be passed"
        assert req.table_preset == "massive", "table_preset should be passed"
        assert req.visibility == "public", "visibility should be passed"


# =============================================================================
# TEST: GET /cards/<card_id> - happy path
# =============================================================================
class TestGetCardHappyPath:
    """Test GET /cards/<card_id> with valid request."""

    def test_get_card_happy_path_200(self, client, fake_get):
        """GET /cards/<card_id> should return 200 with card data."""
        # Act
        response = client.get(
            "/cards/card-001",
            headers={"X-Actor-Id": "u1"},
        )

        # Assert: status code
        assert response.status_code == 200, "Valid GET should return 200"

        # Assert: JSON structure
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert json_data.get("card_id") == "card-001", "card_id should match"
        assert "owner_id" in json_data, "Response should contain owner_id"
        assert "seed" in json_data, "Response should contain seed"
        assert "mode" in json_data, "Response should contain mode"
        assert "visibility" in json_data, "Response should contain visibility"

        # Assert: use case was called with correct args
        assert fake_get.call_count == 1, "get_card.execute() should be called once"
        assert fake_get.last_request.card_id == "card-001", "card_id should be passed"
        assert fake_get.last_request.actor_id == "u1", "actor_id should be passed"


# =============================================================================
# TEST: GET /cards/<card_id> - not found
# =============================================================================
class TestGetCardNotFound:
    """Test GET /cards/<card_id> when card doesn't exist."""

    def test_get_card_not_found_returns_404(self, monkeypatch):
        """GET /cards/<card_id> should return 404 if card not found."""
        # Arrange: create fake that raises not found
        fake_get_not_found = FakeGetCard(raise_not_found=True)
        fake_services = FakeServices(
            generate_scenario_card=FakeGenerateScenarioCard(),
            save_card=FakeSaveCard(),
            get_card=fake_get_not_found,
            list_cards=FakeListCards(),
        )
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: fake_services
        )
        app = create_app()
        app.config["services"] = fake_services
        client = app.test_client()

        # Act
        response = client.get(
            "/cards/card-404",
            headers={"X-Actor-Id": "u1"},
        )

        # Assert
        assert response.status_code == 404, "Card not found should return 404"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"


# =============================================================================
# TEST: GET /cards/<card_id> - missing actor ID
# =============================================================================
class TestGetCardMissingActorId:
    """Test GET /cards/<card_id> without X-Actor-Id header."""

    def test_get_card_missing_actor_id_returns_400(self, client):
        """GET /cards/<card_id> without X-Actor-Id should return 400."""
        # Act
        response = client.get("/cards/card-001")

        # Assert
        assert response.status_code == 400, "Missing X-Actor-Id should return 400"
        json_data = response.get_json()
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"


# =============================================================================
# TEST: GET /cards?filter=... - happy path
# =============================================================================
class TestListCardsHappyPath:
    """Test GET /cards?filter=... with valid request."""

    def test_list_cards_returns_cards_array_200(self, client, fake_list):
        """GET /cards?filter=mine should return 200 with cards array."""
        # Act
        response = client.get(
            "/cards?filter=mine",
            headers={"X-Actor-Id": "u1"},
        )

        # Assert: status code
        assert response.status_code == 200, "Valid GET should return 200"

        # Assert: JSON structure
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "cards" in json_data, "Response should contain 'cards' key"
        assert isinstance(json_data["cards"], list), "cards should be a list"
        assert len(json_data["cards"]) == 2, "Should return 2 cards from fake"

        # Assert: use case was called
        assert fake_list.call_count == 1, "list_cards.execute() should be called once"
        assert fake_list.last_request.actor_id == "u1", "actor_id should be passed"
        assert fake_list.last_request.filter == "mine", "filter should be passed"

    def test_list_cards_public_filter(self, client, fake_list):
        """GET /cards?filter=public should pass correct filter to use case."""
        # Act
        response = client.get(
            "/cards?filter=public",
            headers={"X-Actor-Id": "u1"},
        )

        # Assert
        assert response.status_code == 200
        assert fake_list.last_request.filter == "public"

    def test_list_cards_shared_with_me_filter(self, client, fake_list):
        """GET /cards?filter=shared_with_me should pass correct filter."""
        # Act
        response = client.get(
            "/cards?filter=shared_with_me",
            headers={"X-Actor-Id": "u1"},
        )

        # Assert
        assert response.status_code == 200
        assert fake_list.last_request.filter == "shared_with_me"


# =============================================================================
# TEST: GET /cards?filter=... - missing actor ID
# =============================================================================
class TestListCardsMissingActorId:
    """Test GET /cards without X-Actor-Id header."""

    def test_list_cards_missing_actor_id_returns_400(self, client):
        """GET /cards without X-Actor-Id should return 400."""
        # Act
        response = client.get("/cards?filter=mine")

        # Assert
        assert response.status_code == 400, "Missing X-Actor-Id should return 400"
        json_data = response.get_json()
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"
