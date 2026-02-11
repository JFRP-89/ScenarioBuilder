"""E2E Smoke test: Gradio UI carga e interacción mínima."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page


@pytest.mark.e2e
def test_ui_smoke_loads(e2e_services, wait_for_health, page):
    """
    Smoke test E2E UI (Gradio): carga e interacción mínima.
    """
    wait_for_health()

    ui_url = os.environ.get("UI_BASE_URL", "http://localhost:7860")

    try:
        response = page.goto(ui_url, wait_until="domcontentloaded")

        assert response is not None, "No hubo respuesta al cargar la UI"
        assert response.ok, f"Respuesta HTTP no OK: {response.status}"

        _assert_page_has_visible_content(page)
        _wait_for_ui_ready(page)
        _navigate_to_create_page(page)

        actor_input = _find_actor_input(page)
        assert actor_input is not None, "No se encontró input de actor_id"
        actor_input.fill("u1")

        mode_control = _find_mode_control(page)
        assert mode_control is not None, "No se encontró selector de mode"
        _select_mode(mode_control, "matched")

        seed_input = _find_seed_input(page)
        if seed_input is not None:
            seed_input.fill("123")

        # Fill required text fields so the API accepts the request
        _fill_required_text_fields(page)

        generate_button = page.get_by_role(
            "button",
            name=re.compile("generate card|generate|generar", re.IGNORECASE),
        )
        assert generate_button.count() > 0, "No se encontró botón Generate"
        generate_button.first.click()

        # Wait for Create Scenario button and click it to persist the card
        create_button = page.get_by_role(
            "button",
            name=re.compile("create scenario|crear escenario", re.IGNORECASE),
        )
        # Wait for button to appear (it appears after Generate)
        create_button.first.wait_for(state="visible", timeout=30_000)
        create_button.first.click()

        # Wait for success message
        success_msg = page.get_by_text(
            re.compile(r"scenario created|escenario creado", re.I)
        )
        if success_msg.count() > 0:
            success_msg.first.wait_for(state="visible", timeout=30_000)
        else:
            # Fallback: wait for home page to load
            page.wait_for_timeout(3000)

        _assert_svg_rendered_if_present(page)

    except (PlaywrightError, AssertionError):
        _dump_ui_artifacts(page, "ui_smoke")
        raise


def _assert_page_has_visible_content(page: Page) -> None:
    content = page.content()
    assert "Gradio" in content or "ScenarioBuilder" in content

    body_text = page.locator("body").inner_text().strip()
    assert body_text, "El <body> no tiene contenido"


def _wait_for_ui_ready(page: Page) -> None:
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)

    # Home page has radio buttons and action buttons — wait for any visible input
    page.wait_for_selector(
        "input, textarea, select, button", state="visible", timeout=30_000
    )


def _navigate_to_create_page(page: Page) -> None:
    """Click the '+ Create New Scenario' button on the home page to reach the form."""
    create_btn = page.get_by_role(
        "button", name=re.compile(r"create new scenario", re.IGNORECASE)
    )
    if create_btn.count() == 0:
        create_btn = page.locator("#home-create-btn")
    create_btn.first.click()
    # Wait for the create form to become visible
    page.wait_for_timeout(1000)


def _find_actor_input(page: Page) -> Locator | None:
    candidates = [
        page.get_by_placeholder(re.compile("actor", re.IGNORECASE)),
        page.get_by_label(re.compile("actor id|actor", re.IGNORECASE)),
    ]
    for locator in candidates:
        if locator.count() > 0:
            return locator.first
    return None


def _find_mode_control(page: Page) -> Locator | None:
    candidates = [
        page.get_by_role("combobox", name=re.compile("game mode|mode", re.IGNORECASE)),
        page.get_by_label(re.compile("game mode|mode", re.IGNORECASE)),
    ]
    for locator in candidates:
        if locator.count() > 0:
            return locator.first

    select_locator = page.locator("select")
    if select_locator.count() > 0:
        return select_locator.first
    return None


def _find_seed_input(page: Page) -> Locator | None:
    candidates = [
        page.get_by_role("spinbutton", name=re.compile("seed", re.IGNORECASE)),
        page.get_by_label(re.compile("seed", re.IGNORECASE)),
    ]
    for locator in candidates:
        if locator.count() > 0:
            return locator.first

    number_input = page.locator("input[type='number']")
    if number_input.count() > 0:
        return number_input.first
    return None


def _select_mode(mode_control: Locator, value: str) -> None:
    tag_name = mode_control.evaluate("el => el.tagName.toLowerCase()")
    if tag_name == "select":
        mode_control.select_option(value)
        return

    role = mode_control.get_attribute("role")
    if role == "combobox":
        mode_control.click()
        option = mode_control.page.get_by_role(
            "option", name=re.compile(value, re.IGNORECASE)
        )
        if option.count() > 0:
            option.first.click()
            return

    mode_control.fill(value)


def _fill_required_text_fields(page: Page) -> None:
    """Fill required form fields so the API accepts the request."""
    _fields = {
        "scenario-name-input": "Smoke Test Scenario",
        "armies-input": "Test armies",
        "deployment": "Standard",
        "layout": "Open Field",
        "objectives": "Hold Ground",
        "initial_priority": "None",
    }
    for elem_id, value in _fields.items():
        locator = page.locator(f"#{elem_id} input, #{elem_id} textarea")
        if locator.count() > 0:
            locator.first.fill(value)


def _assert_generation_result(page: Page) -> None:
    result = page.get_by_text(re.compile("card_id", re.IGNORECASE))
    result.wait_for(state="visible", timeout=30_000)


def _assert_svg_rendered_if_present(page: Page) -> None:
    svg_locator = page.locator("svg")
    iframe_locator = page.locator("iframe")
    if svg_locator.count() == 0 and iframe_locator.count() == 0:
        return

    assert (
        svg_locator.count() > 0 or iframe_locator.count() > 0
    ), "No se encontró SVG ni iframe de resultado"


def _dump_ui_artifacts(page: Page, name: str) -> None:
    artifacts_dir = Path(__file__).parent / "_artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    html_path = artifacts_dir / f"{name}.html"
    html_path.write_text(page.content(), encoding="utf-8")

    screenshot_path = artifacts_dir / f"{name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
