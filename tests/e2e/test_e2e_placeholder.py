"""Placeholder para tests E2E (infra lista, esperando implementación)."""

import pytest


@pytest.mark.e2e
def test_e2e_infrastructure_ready(docker_compose_up, e2e_base_urls):
    """
    Smoke test: verifica que la infraestructura E2E esté levantada.

    Este test solo valida que docker-compose arrancó y los health checks pasaron.
    Los tests reales de flujo Gradio/API vendrán en siguientes PRs.
    """
    # Si llegamos aquí, docker_compose_up ya validó health checks
    assert e2e_base_urls["api"] in {"http://localhost:8000", "http://127.0.0.1:8000"}
    assert e2e_base_urls["ui"] in {"http://localhost:7860", "http://127.0.0.1:7860"}
