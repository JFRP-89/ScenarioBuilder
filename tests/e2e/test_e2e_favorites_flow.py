"""E2E test: Favorites flow - toggle + list."""

import pytest
import requests

from tests.e2e._support import get_api_base_url


@pytest.mark.e2e
def test_favorites_toggle_and_list_flow(e2e_services, wait_for_health, generated_card_id):
    """
    E2E flujo de favoritos reutilizando card_id generado:
    1) Toggle favorite ON -> is_favorite=true
    2) GET /favorites -> card_id está en lista
    3) Toggle favorite OFF -> is_favorite=false
    4) GET /favorites -> card_id NO está en lista
    5) Validar determinismo (card_ids sorted o estable)

    Depende de: test_api_generate_card_post
    """
    wait_for_health()

    # Obtener card_id generado en test anterior
    card_id = generated_card_id.get("card_id")
    if not card_id:
        pytest.skip(
            "No hay card_id generado previamente (ejecutar test_api_generate_card_post primero)"
        )

    api_url = get_api_base_url()
    actor_id = "u1"  # Mismo actor que generó la card
    headers = {"X-Actor-Id": actor_id}

    # 2) Toggle ON
    toggle_response = requests.post(
        f"{api_url}/favorites/{card_id}/toggle",
        headers=headers,
        timeout=30,
    )
    assert (
        toggle_response.status_code == 200
    ), f"POST /favorites/{card_id}/toggle falló: {toggle_response.status_code} - {toggle_response.text}"

    toggle_data = toggle_response.json()
    assert toggle_data.get("card_id") == card_id
    assert (
        toggle_data.get("is_favorite") is True
    ), f"Esperado is_favorite=true, pero fue: {toggle_data}"

    # 3) GET /favorites -> card_id está en lista
    list_response = requests.get(
        f"{api_url}/favorites",
        headers=headers,
        timeout=30,
    )
    assert (
        list_response.status_code == 200
    ), f"GET /favorites falló: {list_response.status_code} - {list_response.text}"

    list_data = list_response.json()
    card_ids_in_favorites = list_data.get("card_ids", [])
    assert card_id in card_ids_in_favorites, (
        f"card_id {card_id} NO está en favoritos. " f"Favoritos: {card_ids_in_favorites}"
    )

    # 4) Toggle OFF
    toggle_response_2 = requests.post(
        f"{api_url}/favorites/{card_id}/toggle",
        headers=headers,
        timeout=30,
    )
    assert toggle_response_2.status_code == 200
    toggle_data_2 = toggle_response_2.json()
    assert (
        toggle_data_2.get("is_favorite") is False
    ), f"Esperado is_favorite=false, pero fue: {toggle_data_2}"

    # 5) GET /favorites -> card_id NO está en lista
    list_response_2 = requests.get(
        f"{api_url}/favorites",
        headers=headers,
        timeout=30,
    )
    assert list_response_2.status_code == 200
    list_data_2 = list_response_2.json()
    card_ids_in_favorites_2 = list_data_2.get("card_ids", [])
    assert card_id not in card_ids_in_favorites_2, (
        f"card_id {card_id} SIGUE en favoritos después de toggle OFF. "
        f"Favoritos: {card_ids_in_favorites_2}"
    )
