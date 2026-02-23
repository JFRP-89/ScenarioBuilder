"""Integration tests for Flask app bootstrap contract.

Tests verify that ``create_app()`` wires the application correctly:

- Calls ``build_services()`` once and stores result in ``app.config["services"]``
- Registers blueprints for all routes
- Exposes ``get_actor_id`` helper in ``app.config``
- Centralises error handlers:
  ``ValidationError`` → 400, "not found" → 404, "forbidden" → 403, generic → 500
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

from adapters.http_flask.app import create_app
from domain.errors import ValidationError


# =============================================================================
# FAKES
# =============================================================================
@dataclass(frozen=True)
class FakeServices:
    """Fake services container for testing."""

    generate_scenario_card: MagicMock | None = None
    save_card: MagicMock | None = None
    get_card: MagicMock | None = None
    list_cards: MagicMock | None = None
    toggle_favorite: MagicMock | None = None
    list_favorites: MagicMock | None = None
    create_variant: MagicMock | None = None
    render_map_svg: MagicMock | None = None


# =============================================================================
# TEST: create_app contract (build_services, blueprints, get_actor_id)
# =============================================================================
class TestCreateAppContract:
    """Verify create_app() wiring: services, blueprints, helpers."""

    def test_calls_build_services_once_and_stores_in_config(self, monkeypatch):
        """create_app() should call build_services() once and store in config."""
        sentinel_services = FakeServices()
        call_count = {"count": 0}

        def fake_build_services():
            call_count["count"] += 1
            return sentinel_services

        monkeypatch.setattr(
            "adapters.http_flask.app.build_services", fake_build_services
        )

        app = create_app()

        assert (
            call_count["count"] == 1
        ), "build_services() should be called exactly once"
        assert "services" in app.config, "services should be stored in app.config"
        assert (
            app.config["services"] is sentinel_services
        ), "app.config['services'] should be the sentinel from build_services()"

    def test_registers_blueprints(self, monkeypatch):
        """create_app() should register health, cards, maps, presets blueprints."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)

        app = create_app()

        registered_bp_names = list(app.blueprints.keys())
        assert "health" in registered_bp_names, "health blueprint should be registered"
        assert "cards" in registered_bp_names, "cards blueprint should be registered"
        assert "maps" in registered_bp_names, "maps blueprint should be registered"
        assert (
            "presets" in registered_bp_names
        ), "presets blueprint should be registered"

    def test_health_endpoint_exists(self, monkeypatch):
        """Health endpoint should be accessible."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()
        test_client = app.test_client()

        response = test_client.get("/health")
        assert response.status_code == 200, "/health endpoint should return 200"

    def test_get_actor_id_is_in_config(self, monkeypatch):
        """app.config should contain a get_actor_id callable."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)

        app = create_app()

        assert "get_actor_id" in app.config, "get_actor_id should be in app.config"
        assert callable(app.config["get_actor_id"]), "get_actor_id should be callable"


# =============================================================================
# TEST: Error status-code mapping (400, 404, 403)
# =============================================================================
class TestErrorStatusCodeMapping:
    """Verify that domain/app exceptions map to the right HTTP status codes."""

    def test_validation_error_is_mapped_to_400(self, monkeypatch):
        """ValidationError should be caught and returned as 400 JSON response."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__boom_validation")
        def boom_validation():
            raise ValidationError("test validation error")

        test_client = app.test_client()
        response = test_client.get("/__boom_validation")

        assert response.status_code == 400, "ValidationError should map to 400"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"
        assert "error" in json_data, "JSON should contain 'error' key"
        assert "message" in json_data, "JSON should contain 'message' key"

    def test_not_found_exception_is_mapped_to_404(self, monkeypatch):
        """Exception with 'not found' message should map to 404."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__boom_not_found")
        def boom_not_found():
            raise RuntimeError("Card not found: abc")

        test_client = app.test_client()
        response = test_client.get("/__boom_not_found")

        assert response.status_code == 404, "'not found' exception should map to 404"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"

    def test_forbidden_exception_is_mapped_to_403(self, monkeypatch):
        """Exception with 'Forbidden' message should map to 403."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__boom_forbidden")
        def boom_forbidden():
            raise RuntimeError("Forbidden")

        test_client = app.test_client()
        response = test_client.get("/__boom_forbidden")

        assert response.status_code == 403, "'Forbidden' exception should map to 403"
        json_data = response.get_json()
        assert json_data is not None, "Response should be JSON"

    def test_forbidden_access_denied_is_mapped_to_403(self, monkeypatch):
        """Exception with 'forbidden' (lowercase) should also map to 403."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__boom_access_denied")
        def boom_access_denied():
            raise RuntimeError("Access forbidden for this resource")

        test_client = app.test_client()
        response = test_client.get("/__boom_access_denied")

        assert response.status_code == 403, "'forbidden' in message should map to 403"


# =============================================================================
# TEST: 500 with GENERIC message (no internal leak)
# =============================================================================
class TestInternalServerErrorReturnsGenericMessage:
    """Test that 500 errors always return generic message, never leak internals."""

    def test_generic_exception_is_mapped_to_500_with_generic_message(self, monkeypatch):
        """Unexpected exception should map to 500 with generic message."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__boom_internal")
        def boom_internal():
            raise ValueError("Database connection failed: host=db01 timeout=30")

        test_client = app.test_client()
        response = test_client.get("/__boom_internal")

        assert response.status_code == 500, "Unhandled exception should map to 500"
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

    def test_500_error_code_is_internalerror(self, monkeypatch):
        """500 error response should use 'InternalError' code."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__boom_runtime")
        def boom_runtime():
            raise RuntimeError("Something went wrong internally")

        test_client = app.test_client()
        response = test_client.get("/__boom_runtime")

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
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__test_structure")
        def test_structure():
            raise ValidationError("Invalid field: age")

        test_client = app.test_client()
        response = test_client.get("/__test_structure")

        assert response.status_code == 400
        json_data = response.get_json()
        assert set(json_data.keys()) >= {
            "error",
            "message",
        }, f"Expected at least 'error' and 'message' keys, got: {json_data.keys()}"

    def test_not_found_error_has_notfound_code(self, monkeypatch):
        """Not Found error response should use NotFound error code."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__test_notfound")
        def test_notfound():
            raise RuntimeError("Item not found")

        test_client = app.test_client()
        response = test_client.get("/__test_notfound")

        json_data = response.get_json()
        assert json_data["error"] == "NotFound", "Should use 'NotFound' error code"
        assert (
            json_data["message"] == "Resource not found"
        ), "404 should return standard 'Resource not found' message"

    def test_forbidden_error_has_forbidden_code(self, monkeypatch):
        """Forbidden error response should use Forbidden error code."""
        monkeypatch.setattr("adapters.http_flask.app.build_services", FakeServices)
        app = create_app()

        @app.route("/__test_forbidden")
        def test_forbidden():
            raise RuntimeError("forbidden action")

        test_client = app.test_client()
        response = test_client.get("/__test_forbidden")

        json_data = response.get_json()
        assert json_data["error"] == "Forbidden", "Should use 'Forbidden' error code"
        assert (
            json_data["message"] == "Access denied"
        ), "403 should return standard 'Access denied' message"
