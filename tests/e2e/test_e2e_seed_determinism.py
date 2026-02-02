"""E2E test: Verificar determinismo de seed en mapa SVG."""

import hashlib

import pytest
import requests


@pytest.mark.e2e
def test_seed_determinism_api(e2e_services, wait_for_health, page):
    """
    Prueba que con la misma seed, el SVG del mapa es determinista.

    Genera dos cartas con seed=123, obtiene sus mapas SVG,
    y verifica que los hashes SHA256 son idénticos.
    """
    wait_for_health()

    api_url = "http://localhost:8000"
    headers = {"X-Actor-Id": "e2e-user"}
    payload = {
        "mode": "matched",
        "seed": 123,
        "table_preset": "standard",
        "visibility": "private",
    }

    # Primera generación
    svg_1 = _generate_and_fetch_svg(api_url, headers, payload)
    assert svg_1, "No se pudo obtener SVG en primera generación"

    # Segunda generación (misma seed)
    svg_2 = _generate_and_fetch_svg(api_url, headers, payload)
    assert svg_2, "No se pudo obtener SVG en segunda generación"

    # Comparar hashes
    hash_1 = hashlib.sha256(svg_1.encode()).hexdigest()
    hash_2 = hashlib.sha256(svg_2.encode()).hexdigest()

    try:
        assert hash_1 == hash_2, (
            f"SVGs no son deterministas con seed=123. "
            f"hash_1={hash_1}, hash_2={hash_2}"
        )
    except AssertionError:
        # Debug: guardar SVGs para análisis
        _save_artifact(svg_1, "seed_determinism_svg_1.svg")
        _save_artifact(svg_2, "seed_determinism_svg_2.svg")
        raise


def _generate_and_fetch_svg(api_url: str, headers: dict, payload: dict) -> str:
    """
    Genera una carta y obtiene su SVG del mapa.

    Returns:
        SVG content como string
    """
    # POST /cards
    response = requests.post(
        f"{api_url}/cards",
        headers=headers,
        json=payload,
        timeout=30,
    )
    assert response.status_code == 201, (
        f"POST /cards falló: {response.status_code} - {response.text}"
    )

    card_data = response.json()
    card_id = card_data.get("card_id")
    assert card_id, f"No se encontró card_id en respuesta: {card_data}"

    # GET /cards/{card_id}/map.svg
    svg_response = requests.get(
        f"{api_url}/cards/{card_id}/map.svg",
        headers=headers,
        timeout=30,
    )
    assert svg_response.status_code == 200, (
        f"GET /cards/{card_id}/map.svg falló: {svg_response.status_code} - {svg_response.text}"
    )
    assert "image/svg+xml" in svg_response.headers.get("Content-Type", ""), (
        f"Content-Type incorrecto: {svg_response.headers.get('Content-Type')}"
    )

    return svg_response.text


def _save_artifact(content: str, filename: str) -> None:
    """Guarda contenido en artifacts para debug."""
    from pathlib import Path

    artifacts_dir = Path(__file__).parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    artifact_path = artifacts_dir / filename
    artifact_path.write_text(content, encoding="utf-8")
    print(f"  💾 Artifact guardado: {artifact_path}")

