"""E2E test: /cards/{id}/map.svg - seguridad y headers."""

import pytest
import requests

from tests.e2e._support import get_api_base_url


@pytest.mark.e2e
def test_map_svg_content_type_and_security_headers(
    e2e_services, wait_for_health, generated_card_id
):
    """
    E2E API: Verificar que /cards/<id>/map.svg devuelve SVG seguro.

    Valida:
    1. Reutiliza card_id del fixture generado
    2. GET /cards/<id>/map.svg con X-Actor-Id → 200
    3. Content-Type contiene image/svg+xml
    4. Body contiene <svg y al menos uno de: <rect, <circle, <polygon
    5. Headers defensivos: X-Content-Type-Options, Content-Security-Policy, Cache-Control
    6. NO contiene: <script, foreignObject, onload=, onclick=, onerror=, onmouseover=

    Depende de: test_api_generate_card_post
    """
    wait_for_health()

    # Obtener card_id generado previamente
    card_id = generated_card_id.get("card_id")
    if not card_id:
        pytest.skip("No hay card_id generado (ejecutar test_api_generate_card_post primero)")

    api_url = get_api_base_url()
    headers = {"X-Actor-Id": "u1"}

    # 2) GET /cards/{card_id}/map.svg
    svg_response = requests.get(
        f"{api_url}/cards/{card_id}/map.svg",
        headers=headers,
        timeout=30,
    )

    # 3) Validar status y Content-Type
    assert (
        svg_response.status_code == 200
    ), f"GET /cards/{card_id}/map.svg falló: {svg_response.status_code}"

    content_type = svg_response.headers.get("Content-Type", "")
    assert "image/svg+xml" in content_type, f"Content-Type incorrecto: {content_type}"

    # 4) Validar SVG content - debe contener <svg y al menos uno de los elementos gráficos
    svg_body = svg_response.text
    assert "<svg" in svg_body, "Response no contiene SVG válido (sin <svg)"

    has_graphic_element = any(
        [
            "<rect" in svg_body,
            "<circle" in svg_body,
            "<polygon" in svg_body,
        ]
    )
    assert has_graphic_element, "SVG no contiene elementos gráficos (<rect, <circle, o <polygon)"

    # 5) Validar headers anti-XSS
    _assert_security_headers(svg_response.headers)

    # 6) Validar que NO contiene scripts ni handlers peligrosos
    _assert_no_dangerous_svg_content(svg_body)


def _assert_security_headers(headers: dict) -> None:
    """Validar headers de seguridad."""
    # X-Content-Type-Options: nosniff
    x_content_type_options = headers.get("X-Content-Type-Options", "")
    assert (
        "nosniff" in x_content_type_options
    ), f"Header X-Content-Type-Options falta o incorrecto: {x_content_type_options}"

    # Content-Security-Policy con default-src 'none'
    csp = headers.get("Content-Security-Policy", "")
    assert csp, "Header Content-Security-Policy falta"
    assert "default-src" in csp, f"CSP no contiene default-src: {csp}"
    assert "'none'" in csp or "none" in csp, f"CSP no restringe con 'none': {csp}"

    # Cache-Control con no-store
    cache_control = headers.get("Cache-Control", "")
    assert cache_control, "Header Cache-Control falta"
    assert (
        "no-store" in cache_control or "private" in cache_control
    ), f"Cache-Control no restrictivo: {cache_control}"


def _assert_no_dangerous_svg_content(svg_body: str) -> None:
    """Validar que SVG no contiene scripts ni handlers."""
    # No <script> tags
    assert "<script" not in svg_body.lower(), "SVG contiene <script> tag (XSS vulnerability)"

    # No foreignObject (puede inyectar HTML)
    assert "foreignobject" not in svg_body.lower(), "SVG contiene foreignObject (XSS vector)"

    # No handlers inline
    dangerous_handlers = ["onload=", "onclick=", "onerror=", "onmouseover="]
    for handler in dangerous_handlers:
        assert handler not in svg_body.lower(), f"SVG contiene handler peligroso: {handler}"


@pytest.mark.e2e
def test_map_svg_missing_actor_header(e2e_services, wait_for_health, generated_card_id):
    """
    E2E API: Validar deny-by-default en GET /cards/<id>/map.svg.

    Sin X-Actor-Id header → 400 Bad Request

    Depende de: test_api_generate_card_post
    """
    wait_for_health()

    # Obtener card_id generado previamente
    card_id = generated_card_id.get("card_id")
    if not card_id:
        pytest.skip("No hay card_id generado (ejecutar test_api_generate_card_post primero)")

    api_url = get_api_base_url()

    # GET sin X-Actor-Id → debe fallar
    svg_response = requests.get(
        f"{api_url}/cards/{card_id}/map.svg",
        timeout=30,
    )

    assert (
        svg_response.status_code == 400
    ), f"GET sin X-Actor-Id debería ser 400, pero fue {svg_response.status_code}"

    response_json = svg_response.json()
    assert (
        "error" in response_json or "message" in response_json
    ), f"Respuesta 400 sin error/message: {response_json}"
