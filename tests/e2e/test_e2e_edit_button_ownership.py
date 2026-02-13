"""E2E Security test: Edit button visible only for card owner.

Security by design — the Edit button on the scenario detail page
must only appear when the currently logged-in user matches the card's
``owner_id``.  A non-owner must NEVER see the Edit button, regardless
of the card's visibility (public, shared, private).

Flow:
1. Create a public card via API with owner ``owner-user``.
2. Open the UI as ``demo-user`` (the Gradio default actor).
3. Navigate to the card's detail page.
4. Assert the Edit button is NOT visible.
"""

from __future__ import annotations

import contextlib
import os

import pytest
import requests
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from tests.e2e._support import get_api_base_url
from tests.e2e.utils import dump_debug_artifacts

# =====================================================================
# Helpers
# =====================================================================


def _create_public_card(api_url: str, owner: str, name: str = "") -> str:
    """Create a public card via API and return its card_id."""
    headers = {"X-Actor-Id": owner}
    card_name = name or f"Ownership Test {owner}"
    payload = {
        "mode": "casual",
        "seed": 999,
        "table_preset": "standard",
        "visibility": "public",
        "name": card_name,
        "armies": "Test armies",
        "deployment": "Standard",
        "layout": "Open Field",
        "objectives": "Hold Ground",
        "initial_priority": "None",
    }
    resp = requests.post(
        f"{api_url}/cards",
        headers=headers,
        json=payload,
        timeout=30,
    )
    assert (
        resp.status_code == 201
    ), f"Failed to create test card: {resp.status_code} — {resp.text}"
    data = resp.json()
    card_id = data.get("card_id")
    assert card_id, f"Response missing card_id: {data}"
    return str(card_id)


def _navigate_to_detail(page: Page, card_id: str) -> None:
    """Navigate to the detail page via the hidden Gradio view components.

    Makes the hidden ``#view-card-id`` textbox and ``#view-card-btn``
    visible, types the card_id character-by-character (which fires
    keyboard events that Gradio's Svelte binding picks up), then clicks
    the button to trigger the Python navigation handler.
    """
    # Force visibility of Gradio hidden components
    page.evaluate(
        """() => {
        [document.querySelector('#view-card-id textarea'),
         document.querySelector('#view-card-id input'),
         document.querySelector('#view-card-btn')]
            .filter(Boolean)
            .forEach(el => {
                let curr = el;
                while (curr && curr.tagName !== 'BODY') {
                    curr.style.display = 'block';
                    curr.style.visibility = 'visible';
                    curr.style.opacity = '1';
                    curr.style.pointerEvents = 'auto';
                    if (curr.style.height === '0') curr.style.height = 'auto';
                    if (curr.classList) curr.classList.remove('hidden');
                    curr = curr.parentElement;
                }
            });
    }"""
    )
    page.wait_for_timeout(500)

    # Type card_id character-by-character (dispatches keydown/input/keyup)
    textarea = page.locator("#view-card-id textarea")
    if textarea.count() == 0:
        textarea = page.locator("#view-card-id input")

    # Wait for textarea to be in a stable state
    textarea.first.wait_for(state="attached", timeout=5000)
    page.wait_for_timeout(200)

    textarea.first.click(force=True)
    page.wait_for_timeout(150)
    textarea.first.press("Control+a")
    page.wait_for_timeout(100)
    textarea.first.press("Delete")
    page.wait_for_timeout(100)
    textarea.first.press_sequentially(card_id, delay=35)
    page.wait_for_timeout(700)

    # Click the view button to trigger the Python handler
    view_btn = page.locator("#view-card-btn").first
    view_btn.wait_for(state="attached", timeout=5000)
    view_btn.click(force=True)
    page.wait_for_timeout(5000)


def _wait_for_detail_page(
    page: Page,
    *,
    card_id: str | None = None,
    timeout_ms: int = 20_000,
) -> bool:
    """Wait for detail page to load completely.

    Checks:
    - One of many detail selectors exists and is attached:
      #detail-content-html, #detail-title, #detail-card-id, [data-testid="detail"]
    - Content does NOT contain error markers (API error 404, etc.)
    - If card_id provided: verifies it appears in detail HTML/text

    Returns True if detail loaded successfully; False if error detected or timeout.
    """
    # Try multiple selectors for detail content (UI may vary)
    detail_selectors = [
        "#detail-content-html",
        "#detail-title",
        "#detail-card-id",
        '[data-testid="detail"]',
    ]

    detail_locator = None
    for selector in detail_selectors:
        with contextlib.suppress(Exception):
            locator = page.locator(selector).first
            locator.wait_for(state="attached", timeout=3000)
            detail_locator = locator
            break

    if detail_locator is None:
        return False

    # Get content text and check for errors
    try:
        content_text = detail_locator.inner_text(timeout=timeout_ms)
    except Exception:
        return False

    # Check for error markers (case-insensitive)
    error_markers = [
        "api error 404",
        "resource not found",
        "not found",
        "unauthorized",
    ]
    content_lower = content_text.lower()
    for marker in error_markers:
        if marker in content_lower:
            return False

    # If card_id provided, verify it appears in the detail area
    if card_id:
        with contextlib.suppress(Exception):
            detail_html = detail_locator.inner_html(timeout=timeout_ms)
            if card_id in detail_html:
                return True
            page.wait_for_timeout(800)
            detail_html = detail_locator.inner_html(timeout=timeout_ms)
            return card_id in detail_html
        return True

    # No error markers and content is not empty
    return len(content_text.strip()) > 0


def _expect_visible(
    page: Page,
    locator_selector: str,
    *,
    timeout_ms: int = 10_000,
    name: str = "element",
) -> None:
    """Robustly wait for element to be visible with diagnostics on failure.

    Validates: attached -> visible

    On failure: dumps debug artifacts and pytest.fail with detailed info
    (element count, CSS classes, detail page snippet, original error).
    """
    locator = page.locator(locator_selector).first

    # Step 1: Wait for attached
    try:
        locator.wait_for(state="attached", timeout=timeout_ms)
    except PlaywrightError as e:
        dump_debug_artifacts(page, f"{name}_attach_failed")
        pytest.fail(f"Element {name} ({locator_selector}) failed to attach: {e}")

    # Step 2: Wait for visible
    try:
        locator.wait_for(state="visible", timeout=timeout_ms)
    except PlaywrightError as e:
        # Gather diagnostics
        count = page.locator(locator_selector).count()
        classes_str = "(unable to retrieve)"
        with contextlib.suppress(Exception):
            classes_str = locator.get_attribute("class") or "(no class)"

        detail_snippet = "(unable to retrieve)"
        with contextlib.suppress(Exception):
            detail_elem = page.locator("#detail-content-html").first
            detail_text = detail_elem.inner_text(timeout=2000)
            detail_snippet = detail_text[:200] if detail_text else "(empty)"

        dump_debug_artifacts(page, f"{name}_visibility_failed")
        pytest.fail(
            f"\n{name} ({locator_selector}) NOT VISIBLE (timeout={timeout_ms}ms)\n"
            f"  Element count: {count}\n"
            f"  Classes: {classes_str}\n"
            f"  Detail snippet: {detail_snippet}\n"
            f"  Error: {e}"
        )


# =====================================================================
# Tests
# =====================================================================


@pytest.mark.e2e
class TestEditButtonOwnershipSecurity:
    """Edit button must only appear for the card owner."""

    def test_edit_button_hidden_for_non_owner(
        self, e2e_services, wait_for_health, page
    ):
        """Non-owner viewing a public card must NOT see the Edit button."""
        wait_for_health()

        api_url = get_api_base_url()
        card_id = _create_public_card(api_url, owner="owner-user")

        try:
            ui_url = os.environ.get("UI_BASE_URL", "http://localhost:7860")
            page.goto(ui_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # The UI's default actor is "demo-user" (≠ "owner-user")
            _navigate_to_detail(page, card_id)

            # Wait for detail content to load
            _wait_for_detail_page(page)

            # The Edit button must NOT be visible
            edit_btn = page.locator("#detail-edit-btn")
            if edit_btn.count() > 0:
                is_visible = edit_btn.first.is_visible()
                assert not is_visible, (
                    "SECURITY VIOLATION: Edit button is visible for a "
                    "non-owner user. Only the card owner should see it."
                )
            # If the element is not even in the DOM, that's also acceptable

        except (PlaywrightError, AssertionError):
            dump_debug_artifacts(page, "edit_btn_non_owner")
            raise

    def test_edit_button_visible_for_owner(self, e2e_services, wait_for_health, page):
        """Owner viewing their own card SHOULD see the Edit button."""
        wait_for_health()

        api_url = get_api_base_url()

        # The UI default actor is "demo-user", so create card as "demo-user"
        card_id = _create_public_card(api_url, owner="demo-user")

        # Verify card exists via API before navigating the UI
        verify = requests.get(
            f"{api_url}/cards/{card_id}",
            headers={"X-Actor-Id": "demo-user"},
            timeout=10,
        )
        assert (
            verify.status_code == 200
        ), f"Card {card_id} not found in API: {verify.status_code}"

        try:
            ui_url = os.environ.get("UI_BASE_URL", "http://localhost:7860")
            page.goto(ui_url, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Navigate to detail and wait for load (max 1 retry)
            detail_loaded = False
            for attempt in range(2):
                _navigate_to_detail(page, card_id)
                detail_loaded = _wait_for_detail_page(
                    page, card_id=card_id, timeout_ms=20_000
                )

                if detail_loaded:
                    break

                # Retry: go back to list and try again
                if attempt == 0:
                    page.goto(ui_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(500)

            if not detail_loaded:
                dump_debug_artifacts(page, "edit_btn_owner_detail_failed")
                pytest.fail(
                    f"Detail page failed to load card {card_id} after 2 attempts"
                )

            # The Edit button SHOULD be visible (actor == owner)
            _expect_visible(
                page,
                "#detail-edit-btn",
                name="edit_btn_owner",
                timeout_ms=15_000,
            )

        except (PlaywrightError, AssertionError):
            dump_debug_artifacts(page, "edit_btn_owner")
            raise

    def test_edit_button_starts_hidden_before_load(
        self, e2e_services, wait_for_health, page
    ):
        """Edit button must be hidden on initial page load (no flash)."""
        wait_for_health()

        try:
            ui_url = os.environ.get("UI_BASE_URL", "http://localhost:7860")
            page.goto(ui_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            # Even before navigating to detail, the edit button (if present)
            # must be hidden
            edit_btn = page.locator("#detail-edit-btn")
            if edit_btn.count() > 0:
                is_visible = edit_btn.first.is_visible()
                assert not is_visible, (
                    "Edit button must NOT be visible on initial load "
                    "(security: prevent flash before ownership check)"
                )

        except (PlaywrightError, AssertionError):
            dump_debug_artifacts(page, "edit_btn_initial_state")
            raise
