"""
Smoke tests for Gradio UI adapter.

Contract to verify:
- build_app() returns a gradio.Blocks without making HTTP calls
- _get_api_base_url() reads API_BASE_URL env var and normalizes (no trailing slash)
- _build_headers(actor_id) returns dict with X-Actor-Id header

All tests should be RED until the adapter is properly implemented.
"""
from __future__ import annotations

import sys

import pytest

try:
    import requests
except ModuleNotFoundError:
    pytest.skip("requests not installed", allow_module_level=True)


# =============================================================================
# Test: Import does not trigger HTTP calls
# =============================================================================
class TestImportDoesNotCallRequests:
    """Verify that importing the module does not make HTTP requests."""

    def test_import_gradio_app_does_not_call_requests(self, monkeypatch):
        """Importing adapters.ui_gradio.app should not call requests."""
        call_log: list[str] = []

        def fail_on_request(*args, **kwargs):
            call_log.append("request called")
            raise AssertionError("HTTP request made during import!")

        # Patch all request methods on the imported module
        monkeypatch.setattr(requests, "request", fail_on_request)
        monkeypatch.setattr(requests, "get", fail_on_request)
        monkeypatch.setattr(requests, "post", fail_on_request)

        # Remove from cache to force re-import (including parent module)
        sys.modules.pop("adapters.ui_gradio.app", None)
        sys.modules.pop("adapters.ui_gradio", None)

        # Import should not trigger requests
        import adapters.ui_gradio.app  # noqa: F401

        assert call_log == [], "HTTP request was made during import"


# =============================================================================
# Test: build_app() returns Blocks without HTTP calls
# =============================================================================
class TestBuildAppReturnsBlocks:
    """Verify build_app() returns gradio.Blocks and makes no HTTP calls."""

    def test_build_app_returns_gradio_blocks_and_no_http_calls(self, monkeypatch):
        """build_app() should return a gradio.Blocks instance without HTTP calls."""
        call_log: list[str] = []

        def fail_on_request(*args, **kwargs):
            call_log.append("request called")
            raise AssertionError("HTTP request made during build_app()!")

        monkeypatch.setattr(requests, "request", fail_on_request)
        monkeypatch.setattr(requests, "get", fail_on_request)
        monkeypatch.setattr(requests, "post", fail_on_request)

        from adapters.ui_gradio.app import build_app

        ui = build_app()

        assert ui is not None, "build_app() returned None"
        assert ui.__class__.__name__ == "Blocks", (
            f"Expected gradio.Blocks, got {ui.__class__.__name__}"
        )
        assert call_log == [], "HTTP request was made during build_app()"


# =============================================================================
# Test: _get_api_base_url() reads env var and normalizes
# =============================================================================
class TestGetApiBaseUrl:
    """Verify _get_api_base_url() reads env and normalizes URL."""

    def test_get_api_base_url_uses_env_var(self, monkeypatch):
        """_get_api_base_url() should read API_BASE_URL from environment."""
        monkeypatch.setenv("API_BASE_URL", "http://example.test:9999/")

        # Force re-import to pick up new env (clean parent module too)
        sys.modules.pop("adapters.ui_gradio.app", None)
        sys.modules.pop("adapters.ui_gradio", None)

        from adapters.ui_gradio.app import _get_api_base_url

        result = _get_api_base_url()

        # Should normalize: no trailing slash
        assert result == "http://example.test:9999", (
            f"Expected 'http://example.test:9999', got '{result}'"
        )

    def test_get_api_base_url_uses_default_when_missing(self, monkeypatch):
        """_get_api_base_url() should return a default when env var is missing."""
        monkeypatch.delenv("API_BASE_URL", raising=False)

        # Force re-import (clean parent module too)
        sys.modules.pop("adapters.ui_gradio.app", None)
        sys.modules.pop("adapters.ui_gradio", None)

        from adapters.ui_gradio.app import _get_api_base_url

        result = _get_api_base_url()

        assert result, "_get_api_base_url() returned empty string"
        assert result.startswith("http"), (
            f"Expected URL starting with 'http', got '{result}'"
        )
        assert not result.endswith("/"), (
            f"URL should not have trailing slash: '{result}'"
        )


# =============================================================================
# Test: _build_headers() includes actor ID
# =============================================================================
class TestBuildHeaders:
    """Verify _build_headers() returns dict with X-Actor-Id."""

    def test_build_headers_includes_actor_id(self):
        """_build_headers(actor_id) should include X-Actor-Id header."""
        from adapters.ui_gradio.app import _build_headers

        headers = _build_headers("u1")

        assert isinstance(headers, dict), f"Expected dict, got {type(headers)}"
        assert "X-Actor-Id" in headers, "X-Actor-Id header missing"
        assert headers["X-Actor-Id"] == "u1", (
            f"Expected 'u1', got '{headers.get('X-Actor-Id')}'"
        )
