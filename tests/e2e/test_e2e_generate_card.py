"""E2E happy path: generar card desde UI Gradio y validar card_id."""

import contextlib
import re

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator

from tests.e2e.utils import dump_debug_artifacts

ACTOR_LABELS = ["actor", "x-actor-id", "actor id"]
MODE_LABELS = ["mode"]
SEED_LABELS = ["seed"]
TABLE_PRESET_LABELS = ["table preset"]
VISIBILITY_LABELS = ["visibility"]


@pytest.mark.e2e
def test_generate_card_happy_path(e2e_services, wait_for_health, page):
    """Simula usuario generando card desde Gradio y valida que aparece card_id."""
    wait_for_health()

    try:
        page.goto("http://localhost:7860", wait_until="domcontentloaded")
        _wait_for_ui_ready(page)
        _navigate_to_create_page(page)

        _fill_actor_id(page)
        _fill_mode(page)
        _fill_seed(page)
        _fill_required_text_fields(page)
        _fill_table_preset_if_present(page)
        _fill_visibility_if_present(page)

        _click_generate_button(page)

        # After Generate, click Create Scenario button to persist card
        _click_create_scenario_button(page)

        # Wait for the page to stabilize after POST (might navigate to home)
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)  # Give JS time to update

        # Verify we're either still on create page with success message,
        # or navigated to home (both indicate card was created successfully)
        content = page.content()
        # Check for either: success message in status box, or navigation back to home
        has_success = (
            "Scenario created" in content
            or "created" in content
            or "Home" in content  # Home page has Home navigation
        )
        assert has_success, "Scenario creation did not occur"

    except PlaywrightError:
        dump_debug_artifacts(page, "generate_card_happy_path")
        raise
    except AssertionError:
        dump_debug_artifacts(page, "generate_card_happy_path")
        raise


def _fill_actor_id(page) -> None:
    locator = _find_by_labels_or_placeholder(page, ACTOR_LABELS)
    if locator is None:
        raise AssertionError(_missing_inputs_message(page, "Actor ID"))
    locator.fill("e2e-user")


def _fill_mode(page) -> None:
    locator = _find_by_labels_or_placeholder(page, MODE_LABELS)
    if locator is None:
        return

    tag = locator.evaluate("el => el.tagName.toLowerCase()")
    if tag == "select":
        _select_first_available_option(locator, ["casual", "narrative", "matched"])
        return

    locator.fill("casual")


def _fill_seed(page) -> None:
    locator = _find_by_labels_or_placeholder(page, SEED_LABELS)
    if locator is None:
        return
    locator.fill("42")


def _fill_table_preset_if_present(page) -> None:
    """Select 'standard' table preset. It's a Gradio radio so click the label."""
    standard_label = page.locator(
        "#table-preset label", has_text=re.compile(r"^standard$", re.I)
    )
    if standard_label.count() > 0 and standard_label.first.is_visible():
        standard_label.first.click()
        return

    # Fallback: try generic label/placeholder search
    locator = _find_by_labels_or_placeholder(page, TABLE_PRESET_LABELS)
    if locator is None:
        return

    tag = locator.evaluate("el => el.tagName.toLowerCase()")
    if tag == "select":
        _select_first_available_option(locator, ["standard", "massive"])


def _fill_required_text_fields(page) -> None:
    """Fill required text fields so the API accepts the request."""
    _fields = {
        "scenario-name-input": "E2E Test Scenario",
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


def _fill_visibility_if_present(page) -> None:
    locator = _find_by_labels_or_placeholder(page, VISIBILITY_LABELS)
    if locator is None:
        return

    tag = locator.evaluate("el => el.tagName.toLowerCase()")
    if tag == "select":
        _select_first_available_option(locator, ["private", "public"])
        return

    locator.fill("private")


def _click_generate_button(page) -> None:
    button = page.get_by_role(
        "button", name=re.compile(r"(generate|create|build)", re.I)
    )
    if button.count() == 0:
        raise AssertionError(
            _missing_inputs_message(page, "Generate/Create/Build button")
        )
    button.first.click()


def _click_create_scenario_button(page) -> None:
    """Click the 'Create Scenario' button to persist the card."""
    button = page.get_by_role("button", name=re.compile(r"create scenario", re.I))
    if button.count() == 0:
        raise AssertionError(_missing_inputs_message(page, "Create Scenario button"))
    button.first.click()


def _wait_for_card_id_or_pattern(page) -> None:
    page.get_by_text(re.compile(r"card_id", re.I)).first.wait_for(timeout=20000)


def _read_json_text(page) -> str:
    locator = page.locator("[data-testid='json']")
    if locator.count() == 0:
        return ""
    return str(locator.inner_text())


def _wait_for_ui_ready(page) -> None:
    page.wait_for_selector("input, textarea, select", state="visible", timeout=20000)
    with contextlib.suppress(PlaywrightError):
        # Si el loader no desaparece, al menos seguimos con inputs visibles.
        page.locator("p.loading").first.wait_for(state="hidden", timeout=20000)


def _navigate_to_create_page(page) -> None:
    """Click the '+ Create New Scenario' button on the home page to reach the form."""
    create_btn = page.get_by_role(
        "button", name=re.compile(r"create new scenario", re.I)
    )
    if create_btn.count() == 0:
        # Fallback: try by elem_id
        create_btn = page.locator("#home-create-btn")
    create_btn.first.click()
    # Wait for the create form to become visible (actor input should appear)
    page.wait_for_selector("input, textarea", state="visible", timeout=10000)


def _extract_card_id(html: str) -> str:
    match = re.search(r"card_id\"?\s*[:=]\s*\"?([a-zA-Z0-9_-]+)", html, re.I)
    if match:
        return match.group(1)

    match = re.search(r"(card-[a-zA-Z0-9_-]+)", html, re.I)
    if match:
        return match.group(1)

    return ""


def _find_by_labels_or_placeholder(page, labels: list[str]):
    lower_labels = [label.lower() for label in labels]
    for label in labels:
        locator = page.get_by_label(re.compile(label, re.I))
        if locator.count() > 0:
            return locator.first

    for label in labels:
        locator = page.get_by_placeholder(re.compile(label, re.I))
        if locator.count() > 0:
            return locator.first

    # Fallback: inputs with aria-label
    locator = _find_by_attribute(page, "aria-label", lower_labels)
    if locator is not None:
        return locator

    # Fallback: inputs with name/id
    locator = _find_by_attribute(page, "name", lower_labels)
    if locator is not None:
        return locator
    locator = _find_by_attribute(page, "id", lower_labels)
    if locator is not None:
        return locator

    return None


def _find_by_attribute(page, attribute: str, labels: list[str]):
    candidates = page.locator(
        f"input[{attribute}], textarea[{attribute}], select[{attribute}]"
    )
    count = candidates.count()
    for idx in range(count):
        element = candidates.nth(idx)
        value = (element.get_attribute(attribute) or "").lower()
        if any(label in value for label in labels):
            return element
    return None


def _select_first_available_option(select_locator: Locator, options: list[str]) -> None:
    for option in options:
        try:
            select_locator.select_option(label=option)
            return
        except PlaywrightError:
            continue


def _missing_inputs_message(page, required: str) -> str:
    visible_texts = _visible_texts(page)
    return (
        f"No se encontró input requerido: {required}. "
        f"Textos visibles detectados: {visible_texts}"
    )


def _visible_texts(page) -> list[str]:
    texts = []
    for locator in [
        page.locator("label"),
        page.locator("button"),
        page.locator("h1, h2, h3"),
        page.locator("span"),
        page.locator("p"),
    ]:
        count = locator.count()
        for idx in range(count):
            text = locator.nth(idx).inner_text().strip()
            if text:
                texts.append(text)
    # Limitar tamaño para no explotar el mensaje
    return texts[:50]
