"""E2E test: Missing X-Actor-Id header validation."""

import pytest
import requests


@pytest.mark.e2e
def test_post_cards_missing_actor_id(e2e_services, wait_for_health):  # noqa: ARG001
    """POST /cards sin X-Actor-Id debe devolver 400."""
    wait_for_health()

    api_url = "http://localhost:8000"
    payload = {
        "mode": "casual",
        "seed": 111,
        "table_preset": "standard",
        "visibility": "private",
    }

    # POST sin header
    response = requests.post(
        f"{api_url}/cards",
        json=payload,
        timeout=30,
    )

    assert response.status_code == 400, (
        f"POST /cards sin X-Actor-Id debe retornar 400, "
        f"pero retornó {response.status_code}: {response.text}"
    )

    # Validar JSON de error
    error_data = response.json()
    assert "error" in error_data or "message" in error_data, (
        f"Response debe contener 'error' o 'message': {error_data}"
    )


@pytest.mark.e2e
def test_get_cards_missing_actor_id(e2e_services, wait_for_health):  # noqa: ARG001
    """GET /cards sin X-Actor-Id debe devolver 400."""
    wait_for_health()

    api_url = "http://localhost:8000"

    # GET sin header
    response = requests.get(
        f"{api_url}/cards",
        timeout=30,
    )

    assert response.status_code == 400, (
        f"GET /cards sin X-Actor-Id debe retornar 400, "
        f"pero retornó {response.status_code}: {response.text}"
    )

    # Validar JSON de error
    error_data = response.json()
    assert "error" in error_data or "message" in error_data, (
        f"Response debe contener 'error' o 'message': {error_data}"
    )


@pytest.mark.e2e
def test_get_favorites_missing_actor_id(e2e_services, wait_for_health):  # noqa: ARG001
    """GET /favorites sin X-Actor-Id debe devolver 400."""
    wait_for_health()

    api_url = "http://localhost:8000"

    # GET sin header
    response = requests.get(
        f"{api_url}/favorites",
        timeout=30,
    )

    assert response.status_code == 400, (
        f"GET /favorites sin X-Actor-Id debe retornar 400, "
        f"pero retornó {response.status_code}: {response.text}"
    )

    # Validar JSON de error
    error_data = response.json()
    assert "error" in error_data or "message" in error_data, (
        f"Response debe contener 'error' o 'message': {error_data}"
    )

