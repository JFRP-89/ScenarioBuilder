"""RED tests for Flask app bootstrap contract.

These tests define the expected contract for create_app():
- Calls build_services() once and stores result in app.config["services"]
- Registers blueprints for all routes
- Exposes get_actor_id helper in app.config
- Centralizes error handlers: ValidationError -> 400, not found -> 404, forbidden -> 403
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

from adapters.http_flask.app import create_app
from domain.errors import ValidationError


# =============================================================================
# FIXTURES
# =============================================================================
@dataclass(frozen=True)
class FakeServices:
    """Fake services container for testing."""

    generate_scenario_card: MagicMock = None
    save_card: MagicMock = None
    get_card: MagicMock = None
    list_cards: MagicMock = None
    toggle_favorite: MagicMock = None
    list_favorites: MagicMock = None
    create_variant: MagicMock = None
    render_map_svg: MagicMock = None


# =============================================================================
# TEST: build_services is called once and stored in config
# =============================================================================
class TestCreateAppCallsBuildServicesOnce:
    """Test that create_app() calls build_services() exactly once."""

    def test_create_app_calls_build_services_once_and_stores_in_config(
        self, monkeypatch
    ):
        """create_app() should call build_services() once and store in config."""
        # Arrange: create sentinel and track calls
        sentinel_services = FakeServices()
        call_count = {"count": 0}

        def fake_build_services():
            call_count["count"] += 1
            return sentinel_services

        # Patch build_services at the module where it will be imported
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", fake_build_services
        )

        # Act
        app = create_app()

        # Assert: called exactly once
        assert (
            call_count["count"] == 1
        ), "build_services() should be called exactly once"

        # Assert: services stored in config
        assert "services" in app.config, "services should be stored in app.config"
        assert (
            app.config["services"] is sentinel_services
        ), "app.config['services'] should be the sentinel from build_services()"


# =============================================================================
# TEST: blueprints are registered
# =============================================================================
class TestCreateAppRegistersBlueprintsCorrectly:
    """Test that create_app() registers expected blueprints."""

    def test_create_app_registers_blueprints(self, monkeypatch):
        """create_app() should register health, cards, maps, presets blueprints."""
        # Arrange: patch build_services to avoid real infra
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )

        # Act
        app = create_app()

        # Assert: check registered blueprint names
        registered_bp_names = list(app.blueprints.keys())

        assert "health" in registered_bp_names, "health blueprint should be registered"
        assert "cards" in registered_bp_names, "cards blueprint should be registered"
        assert "maps" in registered_bp_names, "maps blueprint should be registered"
        assert (
            "presets" in registered_bp_names
        ), "presets blueprint should be registered"

    def test_health_endpoint_exists(self, monkeypatch):
        """Health endpoint should be accessible."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()
        client = app.test_client()

        # Act
        response = client.get("/health")

        # Assert: endpoint returns 200 OK
        assert response.status_code == 200, "/health endpoint should return 200"


# =============================================================================
# TEST: get_actor_id helper is exposed
# =============================================================================
class TestCreateAppExposesGetActorIdHelper:
    """Test that create_app() exposes get_actor_id helper in config."""

    def test_get_actor_id_is_in_config(self, monkeypatch):
        """app.config should contain a get_actor_id callable."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )

        # Act
        app = create_app()

        # Assert
        assert "get_actor_id" in app.config, "get_actor_id should be in app.config"
        assert callable(app.config["get_actor_id"]), "get_actor_id should be callable"


# =============================================================================
# TEST: ValidationError -> 400
# =============================================================================
class TestValidationErrorMappedTo400:
    """Test that ValidationError is mapped to HTTP 400."""

    def test_validation_error_is_mapped_to_400_json(self, monkeypatch):
        """ValidationError should be caught and returned as 400 JSON response."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        # Register a temporary endpoint that raises ValidationError
        @app.route("/__boom_validation")
        def boom_validation():
            raise ValidationError("test validation error")

        client = app.test_client()

        # Act
        response = client.get("/__boom_validation")

        # Assert
        assert response.status_code == 400, "ValidationError should map to 400"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"


# =============================================================================
# TEST: Not Found -> 404
# =============================================================================
class TestNotFoundExceptionMappedTo404:
    """Test that 'not found' exceptions are mapped to HTTP 404."""

    def test_not_found_exception_is_mapped_to_404(self, monkeypatch):
        """Exception with 'not found' message should map to 404."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__boom_not_found")
        def boom_not_found():
            raise Exception("Card not found: abc")

        client = app.test_client()

        # Act
        response = client.get("/__boom_not_found")

        # Assert
        assert response.status_code == 404, "'not found' exception should map to 404"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"


# =============================================================================
# TEST: Forbidden -> 403
# =============================================================================
class TestForbiddenExceptionMappedTo403:
    """Test that 'forbidden' exceptions are mapped to HTTP 403."""

    def test_forbidden_exception_is_mapped_to_403(self, monkeypatch):
        """Exception with 'Forbidden' message should map to 403."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__boom_forbidden")
        def boom_forbidden():
            raise Exception("Forbidden")

        client = app.test_client()

        # Act
        response = client.get("/__boom_forbidden")

        # Assert
        assert response.status_code == 403, "'Forbidden' exception should map to 403"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"

    def test_forbidden_access_denied_is_mapped_to_403(self, monkeypatch):
        """Exception with 'forbidden' (lowercase) should also map to 403."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__boom_access_denied")
        def boom_access_denied():
            raise Exception("Access forbidden for this resource")

        client = app.test_client()

        # Act
        response = client.get("/__boom_access_denied")

        # Assert
        assert response.status_code == 403, "'forbidden' in message should map to 403"


# =============================================================================
# TEST: Internal Server Error -> 500 with GENERIC message (no internal leak)
# =============================================================================
class TestInternalServerErrorReturnsGenericMessage:
    """Test that 500 errors always return generic message, never leak internals."""

    def test_generic_exception_is_mapped_to_500_with_generic_message(
        self, monkeypatch
    ):
        """Unexpected exception should map to 500 with generic 'internal error' message."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__boom_internal")
        def boom_internal():
            raise ValueError("Database connection failed: password=secret123")

        client = app.test_client()

        # Act
        response = client.get("/__boom_internal")

        # Assert: 500 status
        assert response.status_code == 500, "Unhandled exception should map to 500"

        # Assert: JSON response
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"

        # CRITICAL: Message must be GENERIC, not leak internal details
        assert (
            json_data["message"] == "An internal error occurred"
        ), f"Expected generic message, got: {json_data['message']}"
        assert (
            "Database" not in json_data["message"]
        ), "500 message should never leak internal error details"
        assert (
            "password" not in json_data["message"]
        ), "500 message should never leak credentials or secrets"
        assert (
            "secret" not in json_data["message"].lower()
        ), "500 message must not contain 'secret'"

    def test_500_error_code_is_internalerror(self, monkeypatch):
        """500 error response should use 'InternalError' code."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__boom_runtime")
        def boom_runtime():
            raise RuntimeError("Something went wrong internally")

        client = app.test_client()

        # Act
        response = client.get("/__boom_runtime")

        # Assert
        json_data = response.get_json()
        assert (
            json_data["error"] == "InternalError"
        ), "500 errors should use 'InternalError' code"


# =============================================================================
# TEST: Error Response JSON Structure
# =============================================================================
class TestErrorResponseJsonStructure:
    """Test that all error responses have consistent JSON structure."""

    def test_validation_error_json_structure(self, monkeypatch):
        """ValidationError response should have error, message keys."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__test_structure")
        def test_structure():
            raise ValidationError("Invalid field: age")

        client = app.test_client()

        # Act
        response = client.get("/__test_structure")

        # Assert: 400 status and proper structure
        assert response.status_code == 400
        json_data = response.get_json()
        assert set(json_data.keys()) >= {
            "error",
            "message",
        }, f"Expected at least 'error' and 'message' keys, got: {json_data.keys()}"

    def test_not_found_error_has_notfound_code(self, monkeypatch):
        """Not Found error response should use NotFound error code."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__test_notfound")
        def test_notfound():
            raise Exception("Item not found")

        client = app.test_client()

        # Act
        response = client.get("/__test_notfound")

        # Assert
        json_data = response.get_json()
        assert json_data["error"] == "NotFound", "Should use 'NotFound' error code"
        assert json_data["message"] == "Resource not found", (
            "404 should return standard 'Resource not found' message"
        )

    def test_forbidden_error_has_forbidden_code(self, monkeypatch):
        """Forbidden error response should use Forbidden error code."""
        # Arrange
        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", lambda: FakeServices()
        )
        app = create_app()

        @app.route("/__test_forbidden")
        def test_forbidden():
            raise Exception("forbidden action")

        client = app.test_client()

        # Act
        response = client.get("/__test_forbidden")

        # Assert
        json_data = response.get_json()
        assert json_data["error"] == "Forbidden", "Should use 'Forbidden' error code"
        assert json_data["message"] == "Access denied", (
            "403 should return standard 'Access denied' message"
        )

