# Tests E2E

Tests end-to-end con Playwright + docker-compose.

## Estructura

```
tests/e2e/
├── conftest.py          # Fixtures comunes (docker-compose, browser, page)
├── utils.py             # Helpers (wait_http_ok, dump_debug_artifacts)
├── artifacts/           # HTML + screenshots de tests fallidos (gitignored)
└── test_*.py            # Tests E2E (marcar con @pytest.mark.e2e)
```

## Fixtures disponibles

### `e2e_base_urls` (scope=session)
Dict con URLs base:
```python
{
    "api": "http://localhost:8000",
    "ui": "http://localhost:7860"
}
```

### `docker_compose_up` (scope=session)
Levanta `docker compose up -d --build api ui`, espera health checks, y al final hace `docker compose down -v`.

Health checks:
- API: `GET /health` → 200
- UI: `GET /` → 200 o 302

Si fallan, imprime `docker compose ps` y logs para debug.

### `browser` (scope=session)
Browser Chromium (Playwright sync API), reutilizado por todos los tests.

### `page` (scope=function)
Page nueva por cada test (se cierra automáticamente).

## Helpers

### `wait_http_ok(url, timeout_s=60, interval_s=1.0, acceptable_codes=(200,))`
Polling hasta que `GET {url}` devuelva código aceptable.

### `dump_debug_artifacts(page, name)`
Guarda HTML + screenshot en `artifacts/` para debug.

## Uso

```bash
# Todos los tests E2E
pytest -q tests/e2e -m e2e

# Test específico
pytest -q tests/e2e/test_gradio_ui.py::test_scenario_generation_flow

# Con verbose + artifacts en failures
pytest -v tests/e2e -m e2e --tb=short
```

## CI (GitHub Actions)

Requisitos:
- Docker Engine disponible en el runner.
- Playwright browsers instalados.

Ejemplo de pasos (jobs steps):

```yaml
- name: Set up Python
    uses: actions/setup-python@v5
    with:
        python-version: '3.11'

- name: Install dependencies
    run: pip install -r requirements.txt

- name: Install Playwright browsers
    run: python -m playwright install chromium

- name: Run E2E tests
    run: pytest -q tests/e2e -m e2e
```

Notas:
- El fixture `docker_compose_up` gestiona `docker compose up/down`.
- Si falla, imprime `docker compose ps` y `docker compose logs --tail=200 api ui`.

## Ejemplo de test

```python
import pytest
from tests.e2e.utils import dump_debug_artifacts


@pytest.mark.e2e
def test_gradio_scenario_generation(docker_compose_up, page, e2e_base_urls):
    """Test completo: abrir UI, generar carta, validar respuesta."""
    try:
        # Abrir UI
        page.goto(e2e_base_urls["ui"])
        
        # Fill inputs
        page.fill('input[placeholder*="Actor ID"]', "user_test")
        page.select_option('select[aria-label="Mode"]', "casual")
        page.fill('input[type="number"]', "42")
        
        # Click generate
        page.click('button:has-text("Generate")')
        
        # Wait for response
        page.wait_for_selector('pre:has-text("card_id")', timeout=10000)
        
        # Validate JSON response
        json_text = page.locator('pre').inner_text()
        assert "card_id" in json_text
        assert "mode" in json_text
        
    except Exception as exc:
        # Si falla, guardar artifacts
        dump_debug_artifacts(page, "test_gradio_scenario_generation")
        raise
```

## Notas

- **Playwright sync API**: Usamos `sync_playwright()` (no async).
- **Docker Compose**: Los servicios `api` y `ui` deben estar definidos en `docker-compose.yml`.
- **Artifacts**: `tests/e2e/artifacts/` debe estar en `.gitignore`.
- **Marker**: Todos los tests E2E deben tener `@pytest.mark.e2e`.
