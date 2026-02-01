"""
Fixtures comunes para tests E2E con Playwright.

Levanta docker-compose, espera health checks, y provee browser/page.
"""
import subprocess
import time
from typing import Callable, Generator

import pytest
import requests
from playwright.sync_api import Browser, Page, Playwright, sync_playwright


# ============================================================================
# CONFIG
# ============================================================================


@pytest.fixture(scope="session")
def e2e_base_urls() -> dict[str, str]:
    """URLs base para API y UI en docker-compose."""
    return {
        "api": "http://localhost:8000",
        "ui": "http://localhost:7860",
    }


# ============================================================================
# DOCKER COMPOSE LIFECYCLE
# ============================================================================


@pytest.fixture(scope="session")
def docker_compose_up(e2e_base_urls: dict[str, str]) -> Generator[None, None, None]:  # noqa: F811
    """
    Levanta docker-compose con api y ui, espera health checks, y al final los baja.
    
    Scope: session -> se levanta una sola vez para todos los tests E2E.
    """
    print("\n🐳 Levantando docker-compose (api + ui)...")
    
    # Levantar servicios
    result = subprocess.run(
        ["docker", "compose", "up", "-d", "--build", "api", "ui"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    
    if result.returncode != 0:
        print("❌ Error al levantar docker-compose:")
        print(result.stdout)
        print(result.stderr)
        _dump_docker_debug()
        pytest.fail("No se pudo levantar docker-compose")
    
    print("✅ docker-compose up completado")
    _dump_docker_debug()
    
    # Esperar health checks
    try:
        _wait_for_health(e2e_base_urls)
        print("✅ Health checks OK")
    except (TimeoutError, requests.RequestException) as exc:
        print(f"❌ Health checks fallaron: {exc}")
        _dump_docker_debug()
        # Bajar servicios antes de fallar
        subprocess.run(["docker", "compose", "down", "-v"], check=False)
        pytest.fail(f"Health checks fallaron: {exc}")
    
    # Tests ejecutan aquí
    yield
    
    # Teardown: bajar servicios
    print("\n🐳 Bajando docker-compose...")
    subprocess.run(
        ["docker", "compose", "down", "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    print("✅ docker-compose down completado")


def _wait_for_health(base_urls: dict[str, str], timeout_s: int = 120, interval_s: float = 2.0) -> None:
    """
    Polling de health checks hasta que API y UI respondan.
    
    API: GET /health debe devolver 200
    UI: GET / debe devolver 200 o 302 (redirect aceptable)
    """
    api_url = f"{base_urls['api']}/health"
    ui_url = base_urls["ui"]
    
    start = time.time()
    api_ok = False
    ui_ok = False
    
    print(f"⏳ Esperando health checks (timeout={timeout_s}s)...")
    
    while time.time() - start < timeout_s:
        # Check API
        if not api_ok:
            api_ok = _check_endpoint(api_url, (200,), f"  ✓ API health OK ({api_url})")
        
        # Check UI
        if not ui_ok:
            ui_ok = _check_endpoint(ui_url, (200, 302), f"  ✓ UI health OK ({ui_url})")
        
        # Ambos OK?
        if api_ok and ui_ok:
            return
        
        time.sleep(interval_s)
    
    # Timeout
    raise TimeoutError(
        f"Health checks timeout después de {timeout_s}s. "
        f"API OK={api_ok}, UI OK={ui_ok}"
    )


@pytest.fixture
def wait_for_health(e2e_base_urls: dict[str, str]) -> Generator[Callable[[], None], None, None]:  # noqa: F811
    """Fixture callable para esperar health checks de API/UI."""
    def _wait() -> None:
        _wait_for_health(e2e_base_urls)

    yield _wait


def _check_endpoint(url: str, acceptable_codes: tuple[int, ...], success_msg: str) -> bool:
    """Check si un endpoint responde con código aceptable."""
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code in acceptable_codes:
            print(success_msg)
            return True
    except requests.RequestException:
        pass
    return False


def _dump_docker_debug() -> None:
    """Imprime docker compose ps y logs para debug."""
    print("\n📊 docker compose ps:")
    result = subprocess.run(
        ["docker", "compose", "ps"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    print(result.stdout)
    
    print("\n📋 docker compose logs (últimas 200 líneas):")
    result = subprocess.run(
        ["docker", "compose", "logs", "--tail=200", "api", "ui"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    print(result.stdout)


# ============================================================================
# PLAYWRIGHT BROWSER & PAGE
# ============================================================================


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:  # noqa: F811
    """Playwright instance (sync API) con scope=session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:  # noqa: F811
    """Browser Chromium con scope=session (reutilizado por todos los tests)."""
    browser = playwright_instance.chromium.launch(headless=True)  # noqa: F811
    yield browser
    browser.close()


@pytest.fixture
def page(browser: Browser) -> Generator[Page, None, None]:  # noqa: F811
    """Page (scope=function, nueva por cada test)."""
    page = browser.new_page()  # noqa: F811
    yield page
    page.close()


# ============================================================================
# API E2E SHARED STATE
# ============================================================================


@pytest.fixture(scope="session")
def generated_card_id():
    """
    Fixture compartida para almacenar card_id generado entre tests API.
    
    Permite reusar el card_id entre tests de la misma sesión.
    Usado por: test_api_generate_card.py, test_e2e_get_card_api.py
    """
    return {"card_id": None}
