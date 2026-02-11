"""E2E Security test: Edit button visible only for card owner.

Security by design — the ✏️ Edit button on the scenario detail page
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


def _create_public_card(api_url: str, owner: str) -> str:
    """Create a public card via API and return its card_id."""
    headers = {"X-Actor-Id": owner}
    payload = {
        "mode": "casual",
        "seed": 999,
        "table_preset": "standard",
        "visibility": "public",
        "name": "Public Card for Ownership Test",
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


def _navigate_to_detail_via_view(page: Page, card_id: str) -> None:
    """Navigate to the scenario detail page for *card_id*.

    Uses the hidden ``#view-card-id`` textbox + ``#view-card-btn`` button
    that Gradio wires for card-tile View buttons.  We set the value via
    the native setter so Gradio's reactive system picks up the change.
    """
    # Set the hidden textbox value using the native setter (bypasses Gradio's
    # controlled-input wrapper so the change event fires correctly).
    page.evaluate(
        """(cardId) => {
            const el = document.querySelector('#view-card-id textarea')
                    || document.querySelector('#view-card-id input');
            if (!el) return;
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            )?.set || Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            )?.set;
            if (setter) setter.call(el, cardId);
            el.dispatchEvent(new Event('input', {bubbles: true}));
        }""",
        card_id,
    )
    page.wait_for_timeout(500)

    # Click the hidden View button to trigger the Gradio handler
    page.evaluate(
        """() => {
            const btn = document.querySelector('#view-card-btn');
            if (btn) btn.click();
        }"""
    )
    page.wait_for_timeout(3000)


def _wait_for_detail_page(page: Page, timeout: int = 15_000) -> None:
    """Wait until the detail page content has rendered.

    Looks for indicators that the detail page is active and has loaded
    card data (title, svg preview, or content sections).
    """
    # Wait for any text that indicates the detail page rendered
    with contextlib.suppress(Exception):
        page.locator(
            "#detail-title, #detail-svg-preview, #detail-content-html"
        ).first.wait_for(state="attached", timeout=timeout)
    # Additional wait for the backend callback to complete
    page.wait_for_timeout(2000)


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
            page.wait_for_timeout(2000)

            # The UI's default actor is "demo-user" (≠ "owner-user")
            _navigate_to_detail_via_view(page, card_id)

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

        try:
            ui_url = os.environ.get("UI_BASE_URL", "http://localhost:7860")
            page.goto(ui_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            _navigate_to_detail_via_view(page, card_id)

            # Wait for detail page to render
            _wait_for_detail_page(page)

            # The Edit button SHOULD be visible (actor == owner)
            edit_btn = page.locator("#detail-edit-btn")

            # Wait up to 15s for the edit button to become visible
            with contextlib.suppress(Exception):
                edit_btn.first.wait_for(state="visible", timeout=15_000)

            assert edit_btn.count() > 0, "Edit button element not found in DOM"
            is_visible = edit_btn.first.is_visible()
            assert is_visible, (
                "Edit button should be visible for the card owner "
                "(demo-user owns this card)"
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
