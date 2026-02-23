"""Shared fixtures for adapter integration tests."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from adapters.combined_app import create_combined_app


@pytest.fixture()
def combined_client() -> TestClient:
    """Create a Starlette TestClient for the combined ASGI app."""
    app = create_combined_app()
    return TestClient(app, follow_redirects=False)
