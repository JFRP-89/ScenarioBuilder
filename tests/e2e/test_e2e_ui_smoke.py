"""E2E Smoke test: Gradio UI carga e interacción mínima."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError, Locator, Page


@pytest.mark.e2e
def test_ui_smoke_loads(e2e_services, wait_for_health, page):  # noqa: ARG001
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

        actor_input = _find_actor_input(page)
        assert actor_input is not None, "No se encontró input de actor_id"
        actor_input.fill("u1")

        mode_control = _find_mode_control(page)
        assert mode_control is not None, "No se encontró selector de mode"
        _select_mode(mode_control, "matched")

        seed_input = _find_seed_input(page)
        if seed_input is not None:
            seed_input.fill("123")

        generate_button = page.get_by_role(
            "button",
            name=re.compile("generate card|generate|generar", re.IGNORECASE),
        )
        assert generate_button.count() > 0, "No se encontró botón Generate"
        generate_button.first.click()

        _assert_generation_result(page)
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
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    actor_placeholder = page.locator("input[placeholder*='actor' i]")
    if actor_placeholder.count() > 0:
        actor_placeholder.first.wait_for(state="visible", timeout=30_000)
        return

    actor_label = page.get_by_text(re.compile("actor id|actor", re.IGNORECASE))
    if actor_label.count() > 0:
        actor_label.first.wait_for(state="visible", timeout=30_000)


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
        option = mode_control.page.get_by_role("option", name=re.compile(value, re.IGNORECASE))
        if option.count() > 0:
            option.first.click()
            return

    mode_control.fill(value)


def _assert_generation_result(page: Page) -> None:
    result = page.get_by_text(re.compile("card_id", re.IGNORECASE))
    result.wait_for(state="visible", timeout=30_000)


def _assert_svg_rendered_if_present(page: Page) -> None:
    svg_locator = page.locator("svg")
    iframe_locator = page.locator("iframe")
    if svg_locator.count() == 0 and iframe_locator.count() == 0:
        return

    assert svg_locator.count() > 0 or iframe_locator.count() > 0, (
        "No se encontró SVG ni iframe de resultado"
    )


def _dump_ui_artifacts(page: Page, name: str) -> None:
    artifacts_dir = Path(__file__).parent / "_artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    html_path = artifacts_dir / f"{name}.html"
    html_path.write_text(page.content(), encoding="utf-8")

    screenshot_path = artifacts_dir / f"{name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)

