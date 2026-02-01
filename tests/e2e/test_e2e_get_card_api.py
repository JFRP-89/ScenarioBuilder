"""E2E API test: GET /cards/{id} - recuperar card y validaciones."""

import pytest
import requests

from tests.e2e._support import get_api_base_url


@pytest.mark.e2e
def test_api_get_card_happy_path(docker_compose_up, wait_for_health, generated_card_id):  # noqa: ARG001
    """
    E2E API: recuperar card por ID con actor autorizado.
    
    Flujo:
    1. GET /cards/{card_id} con X-Actor-Id: u1
    2. Validar status 200
    3. Validar JSON contiene: card_id, owner_id, seed, mode, visibility
    4. Validar valores coinciden con los del POST
    
    Depende de: test_api_generate_card_post (debe ejecutarse primero)
    """
    wait_for_health()

    # Obtener card_id del test anterior
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

    # Validar JSON contrato
    card_data = response.json()
    
    required_keys = {"card_id", "owner_id", "seed", "mode", "visibility"}
    actual_keys = set(card_data.keys())
    
    missing_keys = required_keys - actual_keys
    assert not missing_keys, (
        f"Faltan keys en respuesta: {missing_keys}. "
        f"Keys presentes: {actual_keys}"
    )

    # Validar valores específicos
    assert card_data["card_id"] == card_id, (
        f"card_id no coincide. Esperado: {card_id}, Recibido: {card_data['card_id']}"
    )
    
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

    print(f"✅ Card recuperado exitosamente: {card_id}")
    print(f"   - owner_id: {card_data['owner_id']}")
    print(f"   - seed: {card_data['seed']}")
    print(f"   - mode: {card_data['mode']}")
    print(f"   - visibility: {card_data['visibility']}")


@pytest.mark.e2e
def test_api_get_card_missing_actor_header(docker_compose_up, wait_for_health, generated_card_id):  # noqa: ARG001
    """
    E2E API: deny-by-default - GET sin X-Actor-Id debe fallar.
    
    Flujo:
    1. GET /cards/{card_id} SIN header X-Actor-Id
    2. Validar status 400
    3. Validar JSON tiene error/message
    
    Depende de: test_api_generate_card_post
    """
    wait_for_health()

    # Obtener card_id del test anterior
    card_id = generated_card_id.get("card_id")
    if not card_id:
        pytest.skip("No hay card_id generado previamente (ejecutar test_api_generate_card_post primero)")

    api_url = get_api_base_url()

    # GET sin header X-Actor-Id
    response = requests.get(
        f"{api_url}/cards/{card_id}",
        timeout=30,
    )

    # Validar status 400
    assert response.status_code == 400, (
        f"GET /cards/{card_id} sin X-Actor-Id debe retornar 400, "
        f"pero retornó {response.status_code}: {response.text}"
    )

    # Validar JSON de error
    try:
        error_data = response.json()
        has_error_info = "error" in error_data or "message" in error_data
        assert has_error_info, (
            f"Response debe contener 'error' o 'message'. "
            f"Recibido: {error_data}"
        )
        print(f"✅ Deny-by-default OK: {error_data.get('error') or error_data.get('message')}")
    except ValueError:
        pytest.fail(f"Response no es JSON válido: {response.text}")


@pytest.mark.e2e
def test_api_get_card_not_found(docker_compose_up, wait_for_health):  # noqa: ARG001
    """
    E2E API: GET card inexistente debe retornar 404.
    
    Flujo:
    1. GET /cards/does-not-exist-uuid con X-Actor-Id: u1
    2. Validar status 404
    3. Validar JSON tiene error/message
    """
    wait_for_health()

    api_url = get_api_base_url()
    headers = {"X-Actor-Id": "u1"}
    fake_card_id = "does-not-exist-uuid-12345"

    # GET card inexistente
    response = requests.get(
        f"{api_url}/cards/{fake_card_id}",
        headers=headers,
        timeout=30,
    )

    # Validar status 404
    assert response.status_code == 404, (
        f"GET /cards/{fake_card_id} (inexistente) debe retornar 404, "
        f"pero retornó {response.status_code}: {response.text}"
    )

    # Validar JSON de error
    try:
        error_data = response.json()
        has_error_info = "error" in error_data or "message" in error_data
        assert has_error_info, (
            f"Response debe contener 'error' o 'message'. "
            f"Recibido: {error_data}"
        )
        print(f"✅ 404 correcto: {error_data.get('error') or error_data.get('message')}")
    except ValueError:
        pytest.fail(f"Response no es JSON válido: {response.text}")
