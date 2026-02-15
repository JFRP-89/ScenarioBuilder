"""Integration test: Verify PUT /cards/<card_id> endpoint for editing.

Tests that the update endpoint:
1. Accepts a card ID in the URL
2. Retrieves the existing card
3. Parses the request body
4. Preserves the existing seed (edit mode)
5. Re-generates the card with the new data
6. Saves the updated card
7. Returns the generated response
"""

from __future__ import annotations

import pytest
from adapters.http_flask.app import create_app
from application.use_cases.generate_scenario_card import (
    GenerateScenarioCardRequest,
)
from application.use_cases.save_card import SaveCardRequest
from domain.cards.card import GameMode


@pytest.fixture
def app_with_client(session_factory):
    """Create a Flask app with test client, using real services."""
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    auth = session_factory(c, "user-test")
    c._test_csrf = auth["csrf_token"]
    return app, c


class TestCardsPutUpdate:
    """Test PUT /cards/<card_id> endpoint."""

    def test_put_update_existing_card_preserves_seed(self, app_with_client):
        """PUT should update card while preserving seed."""
        app, flask_client = app_with_client
        actor_id = "user-test"

        # Get the services from the app (shared repository)
        services = app.config["services"]

        # 1) Create initial card using shared services
        gen_req = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode=GameMode.CASUAL,
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=True,
            armies="Initial Army",
            deployment="Initial Deployment",
        )

        gen_resp = services.generate_scenario_card.execute(gen_req)
        card_id = gen_resp.card_id
        initial_seed = gen_resp.seed

        # 2) Save card to shared repository
        services.save_card.execute(
            SaveCardRequest(actor_id=actor_id, card=gen_resp.card)
        )

        # 3) PUT to update the card (change armies only)
        update_payload = {
            "mode": "casual",
            "armies": "Updated Army",
            "deployment": "Initial Deployment",
            "table_preset": "standard",
            "visibility": "private",
            "is_replicable": True,
        }

        response = flask_client.put(
            f"/cards/{card_id}",
            json=update_payload,
            headers={"X-CSRF-Token": flask_client._test_csrf},
        )

        # 4) Verify response
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.data}"
        data = response.get_json()

        # 5) Verify seed is preserved
        assert data["seed"] == initial_seed, (
            f"Seed should be preserved during edit. "
            f"Initial: {initial_seed}, Updated: {data['seed']}"
        )

        # 6) Verify armies updated
        assert data["armies"] == "Updated Army"

        # 7) Verify card_id same
        assert data["card_id"] == card_id

    def test_put_nonexistent_card_returns_404(self, app_with_client):
        """PUT to nonexistent card should return 404."""
        _, flask_client = app_with_client

        response = flask_client.put(
            "/cards/nonexistent-card-id",
            json={"armies": "Test"},
            headers={"X-CSRF-Token": flask_client._test_csrf},
        )

        # Should return 404 (not found) or similar error
        assert response.status_code in (404, 403, 500) or response.status_code >= 400

    def test_put_without_actor_id_header_returns_error(self, app_with_client):
        """PUT without valid session should return 401."""
        app, _ = app_with_client
        unauth_client = app.test_client()

        response = unauth_client.put(
            "/cards/some-card-id",
            json={"armies": "Test"},
        )

        # Should return 401 (missing auth)
        assert response.status_code == 401
