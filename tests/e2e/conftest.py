"""
Fixtures comunes para tests E2E con Playwright.

Levanta docker-compose o servidor local, espera health checks, y provee browser/page.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Generator
from urllib.parse import urlparse

import pytest
import requests
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from tests.e2e._support.port_checks import check_port_clean

# ============================================================================
# CONFIG
# ============================================================================


REPO_ROOT = Path(__file__).resolve().parents[2]


def _get_e2e_mode() -> str:
    return os.environ.get("E2E_MODE", "docker").strip().lower()


@pytest.fixture(scope="session")
def e2e_mode() -> str:
    """Modo E2E: docker (default) o local."""
    mode = _get_e2e_mode()
    if mode not in {"docker", "local"}:
        pytest.fail(f"E2E_MODE inválido: {mode}. Usa 'docker' o 'local'.")
    return mode


@pytest.fixture(scope="session")
def e2e_base_urls() -> dict[str, str]:
    """URLs base para API y UI. API se controla con E2E_BASE_URL."""
    api_base = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    ui_base = os.environ.get("UI_BASE_URL", "http://localhost:7860").rstrip("/")
    return {
        "api": api_base,
        "ui": ui_base,
    }


@pytest.fixture(scope="session", autouse=True)
def _set_e2e_env_vars(e2e_base_urls: dict[str, str]) -> Generator[None, None, None]:
    """Sincroniza env vars de base URLs para tests y helpers."""
    os.environ["API_BASE_URL"] = e2e_base_urls["api"]
    os.environ.setdefault("UI_BASE_URL", e2e_base_urls["ui"])
    yield


@pytest.fixture(scope="session")
def base_url(e2e_base_urls: dict[str, str]) -> str:
    """Base URL común para API en E2E."""
    return e2e_base_urls["api"]


# ============================================================================
# DOCKER COMPOSE LIFECYCLE
# ============================================================================


@pytest.fixture(scope="session")
def e2e_services(
    request: pytest.FixtureRequest,
    e2e_mode: str,
    e2e_base_urls: dict[str, str],
) -> Generator[None, None, None]:
    """
    Inicia servicios E2E según modo:
    - docker: docker compose up/down
    - local: proceso Flask local (sin Docker)
    """
    if e2e_mode == "local" and _is_ui_test(request):
        pytest.skip("E2E_MODE=local no levanta UI; saltando test UI.")

    if e2e_mode == "docker":
        if not _docker_available():
            pytest.skip("Docker no disponible. Usa E2E_MODE=local o instala Docker.")

        # Fail early if a rogue Python process is competing on port 8000
        check_port_clean(8000)

        print("\n🐳 Levantando docker-compose (api + ui)...")
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

        try:
            _wait_for_health(e2e_base_urls, check_ui=True)
            print("✅ Health checks OK")
        except (TimeoutError, requests.RequestException) as exc:
            print(f"❌ Health checks fallaron: {exc}")
            _dump_docker_debug()
            subprocess.run(["docker", "compose", "down", "-v"], check=False)
            pytest.fail(f"Health checks fallaron: {exc}")

        yield

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
        return

    process = _start_local_api(e2e_base_urls["api"])
    try:
        _wait_for_health(e2e_base_urls, check_ui=False)
        print("✅ Health checks OK (local API)")
    except (TimeoutError, requests.RequestException) as exc:
        print(f"❌ Health checks fallaron: {exc}")
        _terminate_process(process)
        pytest.fail(f"Health checks fallaron: {exc}")

    yield

    _terminate_process(process)


@pytest.fixture(scope="session")
def docker_compose_up(e2e_services: None) -> Generator[None, None, None]:
    """Compatibilidad con tests legacy: asegura servicios E2E arriba."""
    yield


def _wait_for_health(
    base_urls: dict[str, str],
    *,
    check_ui: bool,
    timeout_s: int = 120,
    interval_s: float = 2.0,
) -> None:
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
        if check_ui and not ui_ok:
            ui_ok = _check_endpoint(ui_url, (200, 302), f"  ✓ UI health OK ({ui_url})")

        # Ambos OK?
        if api_ok and (ui_ok or not check_ui):
            return

        time.sleep(interval_s)

    # Timeout
    raise TimeoutError(
        f"Health checks timeout después de {timeout_s}s. "
        f"API OK={api_ok}, UI OK={ui_ok}"
    )


@pytest.fixture
def wait_for_health(
    e2e_base_urls: dict[str, str],
    e2e_mode: str,
) -> Generator[Callable[[], None], None, None]:
    """Fixture callable para esperar health checks de API/UI."""

    def _wait() -> None:
        _wait_for_health(e2e_base_urls, check_ui=e2e_mode == "docker")

    yield _wait


def _check_endpoint(
    url: str, acceptable_codes: tuple[int, ...], success_msg: str
) -> bool:
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
    if result.stderr:
        print("STDERR:\n" + result.stderr)


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _start_local_api(base_url: str) -> subprocess.Popen[bytes]:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000

    env = os.environ.copy()
    env.setdefault("API_HOST", host)
    env.setdefault("API_PORT", str(port))
    env["PYTHONPATH"] = str(REPO_ROOT)

    command = (
        "from adapters.http_flask.app import create_app; "
        f"create_app().run(host='{host}', port={port})"
    )

    return subprocess.Popen(
        [sys.executable, "-c", command],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _is_ui_test(request: pytest.FixtureRequest) -> bool:
    """Verifica si el test es un test de UI."""
    filename = request.node.fspath.basename
    return filename in {
        "test_e2e_ui_smoke.py",
        "test_e2e_generate_card.py",
        "test_e2e_edit_button_ownership.py",
    }


# ============================================================================
# PLAYWRIGHT BROWSER & PAGE
# ============================================================================


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """Playwright instance (sync API) con scope=session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    """Browser Chromium con scope=session (reutilizado por todos los tests)."""
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture
def page(browser: Browser) -> Generator[Page, None, None]:
    """Page (scope=function, nueva por cada test)."""
    page = browser.new_page()
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
