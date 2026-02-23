"""
Helpers comunes para tests E2E.

Incluye: wait_http_ok, dump_debug_artifacts.
"""

import time
from pathlib import Path
from typing import Optional

import requests
from playwright.sync_api import Page

# ============================================================================
# HTTP HELPERS
# ============================================================================


def wait_http_ok(
    url: str,
    timeout_s: int = 60,
    interval_s: float = 1.0,
    acceptable_codes: tuple[int, ...] = (200,),
) -> None:
    """
    Polling hasta que GET {url} devuelva uno de los códigos aceptables.

    Args:
        url: URL completa (ej: http://localhost:8000/health)
        timeout_s: Timeout total en segundos
        interval_s: Intervalo entre intentos
        acceptable_codes: Tupla de códigos HTTP aceptables (default: (200,))

    Raises:
        TimeoutError: Si no responde con código aceptable antes del timeout
    """
    start = time.time()
    last_error: Optional[Exception] = None

    while time.time() - start < timeout_s:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code in acceptable_codes:
                return
            last_error = Exception(f"HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_error = exc

        time.sleep(interval_s)

    # Timeout
    raise TimeoutError(
        f"wait_http_ok timeout después de {timeout_s}s para {url}. "
        f"Último error: {last_error}"
    )


# ============================================================================
# DEBUG ARTIFACTS
# ============================================================================


def dump_debug_artifacts(page: Page, name: str) -> None:
    """
    Guarda HTML + screenshot de la page actual en tests/e2e/artifacts/.

    Args:
        page: Playwright Page
        name: Nombre base para archivos (ej: "test_scenario_generation")

    Files created:
        tests/e2e/artifacts/{name}.html
        tests/e2e/artifacts/{name}.png
    """
    artifacts_dir = Path(__file__).parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    # HTML
    html_path = artifacts_dir / f"{name}.html"
    html_content = page.content()
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  💾 HTML guardado: {html_path}")

    # Screenshot
    screenshot_path = artifacts_dir / f"{name}.png"
    page.screenshot(path=str(screenshot_path))
    print(f"  📸 Screenshot guardado: {screenshot_path}")


def fill_required_text_fields(
    page: Page,
    scenario_name: str = "E2E Test Scenario",
) -> None:
    """Fill required form fields so the API accepts the request.

    Shared by UI-based E2E tests (smoke test, generate-card test).
    """
    fields = {
        "scenario-name-input": scenario_name,
        "armies-input": "Test armies",
        "deployment": "Standard",
        "layout": "Open Field",
        "objectives": "Hold Ground",
        "initial_priority": "None",
    }
    for elem_id, value in fields.items():
        locator = page.locator(f"#{elem_id} input, #{elem_id} textarea")
        if locator.count() > 0:
            locator.first.fill(value)
