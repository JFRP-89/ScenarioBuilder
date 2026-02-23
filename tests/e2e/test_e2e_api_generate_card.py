"""E2E API test: POST /cards - generar y guardar card."""

import pytest
import requests
from e2e._support import get_api_base_url
from e2e._support.api_helpers import matched_payload, post_card


def _assert_card_structure(card_data: dict) -> str:
    """Validate card JSON structure and return card_id."""
    required_keys = {
        "card_id",
        "owner_id",
        "seed",
        "mode",
        "visibility",
        "table_mm",
        "shapes",
    }
    actual_keys = set(card_data.keys())
    missing_keys = required_keys - actual_keys
    assert (
        not missing_keys
    ), f"Faltan keys en respuesta: {missing_keys}. Keys presentes: {actual_keys}"

    card_id = card_data["card_id"]
    assert isinstance(card_id, str) and card_id, "card_id debe ser string no vacío"

    assert (
        card_data["owner_id"] == "u1"
    ), f"owner_id esperado 'u1', recibido '{card_data['owner_id']}'"
    assert card_data["seed"] == 123, f"seed esperado 123, recibido {card_data['seed']}"
    assert (
        card_data["mode"] == "matched"
    ), f"mode esperado 'matched', recibido '{card_data['mode']}'"
    assert (
        card_data["visibility"] == "private"
    ), f"visibility esperado 'private', recibido '{card_data['visibility']}'"

    table_mm = card_data["table_mm"]
    assert isinstance(table_mm, dict), "table_mm debe ser dict"
    assert (
        "width_mm" in table_mm and "height_mm" in table_mm
    ), f"table_mm debe tener width_mm y height_mm. Recibido: {table_mm}"

    return card_id


def _assert_shapes_structure(shapes: dict) -> None:
    """Validate shapes dict has expected sub-lists."""
    assert isinstance(
        shapes, dict
    ), f"shapes debe ser dict, recibido {type(shapes).__name__}"

    expected_keys = {"deployment_shapes", "objective_shapes", "scenography_specs"}
    actual_keys = set(shapes.keys())
    missing = expected_keys - actual_keys
    assert (
        not missing
    ), f"Faltan keys en shapes: {missing}. Keys presentes: {actual_keys}"

    for key in expected_keys:
        assert isinstance(
            shapes[key], list
        ), f"shapes['{key}'] debe ser lista, recibido {type(shapes[key]).__name__}"


@pytest.mark.e2e
@pytest.mark.usefixtures("e2e_services")
def test_api_generate_card_post(wait_for_health, generated_card_id):
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
    payload = matched_payload()

    response = post_card(api_url, headers, payload)

    assert (
        response.status_code == 201
    ), f"POST /cards falló con status {response.status_code}. Response: {response.text}"

    card_data = response.json()
    card_id = _assert_card_structure(card_data)
    _assert_shapes_structure(card_data["shapes"])

    generated_card_id["card_id"] = card_id

    print(f"✅ Card generado exitosamente: {card_id}")
    print(f"   - owner_id: {card_data['owner_id']}")
    print(f"   - seed: {card_data['seed']}")
    print(f"   - mode: {card_data['mode']}")
    print(f"   - table_mm: {card_data['table_mm']}")
    print(f"   - shapes: {list(card_data['shapes'].keys())}")


@pytest.mark.e2e
@pytest.mark.usefixtures("e2e_services")
def test_api_get_generated_card(wait_for_health, generated_card_id):
    """
    E2E API: recuperar card generado previamente por card_id.

    Depende de test_api_generate_card_post (debe ejecutarse después).
    """
    wait_for_health()

    # Verificar que hay card_id del test anterior
    card_id = generated_card_id.get("card_id")
    if not card_id:
        pytest.skip(
            "No hay card_id generado previamente (ejecutar test_api_generate_card_post primero)"
        )

    api_url = get_api_base_url()
    headers = {"X-Actor-Id": "u1"}

    # GET /cards/{card_id}
    response = requests.get(
        f"{api_url}/cards/{card_id}",
        headers=headers,
        timeout=30,
    )

    # Validar status
    assert (
        response.status_code == 200
    ), f"GET /cards/{card_id} fall\u00f3 con status {response.status_code}. Response: {response.text}"

    # Validar JSON
    retrieved_card = response.json()
    assert retrieved_card["card_id"] == card_id
    assert retrieved_card["owner_id"] == "u1"
    assert retrieved_card["seed"] == 123
    assert retrieved_card["mode"] == "matched"

    print(f"✅ Card recuperado exitosamente: {card_id}")
