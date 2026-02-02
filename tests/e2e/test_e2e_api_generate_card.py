"""E2E API test: POST /cards - generar y guardar card."""

import pytest
import requests

from tests.e2e._support import get_api_base_url


@pytest.mark.e2e
def test_api_generate_card_post(e2e_services, wait_for_health, generated_card_id):
    """
    E2E API: generar carta vía POST /cards y validar respuesta.

    Flujo:
    1. POST /cards con X-Actor-Id: u1
    2. Validar status 201
    3. Validar JSON contiene: card_id, owner_id, seed, mode, visibility, table_mm, shapes
    4. Guardar card_id en fixture para reuso
    """
    wait_for_health()

    api_url = get_api_base_url()
    headers = {"X-Actor-Id": "u1"}
    payload = {
        "mode": "matched",
        "seed": 123,
        "table_preset": "standard",
        "visibility": "private",
    }

    # POST /cards
    response = requests.post(
        f"{api_url}/cards",
        headers=headers,
        json=payload,
        timeout=30,
    )

    # Validar status
    assert response.status_code == 201, (
        f"POST /cards falló con status {response.status_code}. "
        f"Response: {response.text}"
    )

    # Validar JSON
    card_data = response.json()

    # Required keys
    required_keys = {"card_id", "owner_id", "seed", "mode", "visibility", "table_mm", "shapes"}
    actual_keys = set(card_data.keys())

    missing_keys = required_keys - actual_keys
    assert not missing_keys, (
        f"Faltan keys en respuesta: {missing_keys}. "
        f"Keys presentes: {actual_keys}"
    )

    # Validar tipos y valores
    card_id = card_data["card_id"]
    assert isinstance(card_id, str) and card_id, "card_id debe ser string no vacío"

    assert card_data["owner_id"] == "u1", (
        f"owner_id esperado 'u1', recibido '{card_data['owner_id']}'"
    )

    assert card_data["seed"] == 123, (
        f"seed esperado 123, recibido {card_data['seed']}"
    )

    assert card_data["mode"] == "matched", (
        f"mode esperado 'matched', recibido '{card_data['mode']}'"
    )

    assert card_data["visibility"] == "private", (
        f"visibility esperado 'private', recibido '{card_data['visibility']}'"
    )

    # Validar table_mm es dict con width_mm y height_mm
    table_mm = card_data["table_mm"]
    assert isinstance(table_mm, dict), "table_mm debe ser dict"
    assert "width_mm" in table_mm and "height_mm" in table_mm, (
        f"table_mm debe tener width_mm y height_mm. Recibido: {table_mm}"
    )

    # Validar shapes es lista (aunque sea vacía)
    shapes = card_data["shapes"]
    assert isinstance(shapes, list), (
        f"shapes debe ser lista, recibido {type(shapes).__name__}"
    )

    # Guardar card_id en fixture para reuso en otros tests
    generated_card_id["card_id"] = card_id

    print(f"✅ Card generado exitosamente: {card_id}")
    print(f"   - owner_id: {card_data['owner_id']}")
    print(f"   - seed: {card_data['seed']}")
    print(f"   - mode: {card_data['mode']}")
    print(f"   - table_mm: {table_mm}")
    print(f"   - shapes count: {len(shapes)}")


@pytest.mark.e2e
def test_api_get_generated_card(e2e_services, wait_for_health, generated_card_id):
    """
    E2E API: recuperar card generado previamente por card_id.

    Depende de test_api_generate_card_post (debe ejecutarse después).
    """
    wait_for_health()

    # Verificar que hay card_id del test anterior
    card_id = generated_card_id.get("card_id")
    if not card_id:
        pytest.skip("No hay card_id generado previamente (ejecutar test_api_generate_card_post primero)")

    api_url = get_api_base_url()
    headers = {"X-Actor-Id": "u1"}

    # GET /cards/{card_id}
    response = requests.get(
        f"{api_url}/cards/{card_id}",
        headers=headers,
        timeout=30,
    )

    # Validar status
    assert response.status_code == 200, (
        f"GET /cards/{card_id} falló con status {response.status_code}. "
        f"Response: {response.text}"
    )

    # Validar JSON
    retrieved_card = response.json()
    assert retrieved_card["card_id"] == card_id
    assert retrieved_card["owner_id"] == "u1"
    assert retrieved_card["seed"] == 123
    assert retrieved_card["mode"] == "matched"

    print(f"✅ Card recuperado exitosamente: {card_id}")

