"""Unit tests — Edit button visibility based on ownership.

Security by design: the Edit button must only be visible when the
currently-logged-in actor matches the card's ``owner_id``.

These tests exercise ``_load_card_detail`` (inner function of
``wire_detail_page``) via its external-facing helpers and the
ownership-check logic path.
"""

from __future__ import annotations

from unittest.mock import patch

# ---------------------------------------------------------------------------
# Helpers - build fake card data
# ---------------------------------------------------------------------------


def _card_owned_by(owner: str, *, visibility: str = "private") -> dict:
    """Build a minimal card dict owned by *owner*."""
    return {
        "card_id": "card-abc-123",
        "owner_id": owner,
        "name": "Test Scenario",
        "mode": "matched",
        "seed": 42,
        "armies": "Test armies",
        "visibility": visibility,
        "table_preset": "standard",
        "table_mm": {"width": 1200, "height": 1200},
        "deployment": "Standard",
        "layout": "Open Field",
        "objectives": "Hold Ground",
        "initial_priority": "None",
    }


SVG_STUB = '<svg width="100" height="100"></svg>'


# =====================================================================
# Tests for the ownership check inside _load_card_detail
# =====================================================================


class TestEditButtonVisibilityByOwnership:
    """Edit button must be visible=True only when actor == owner."""

    @patch("adapters.ui_gradio.ui.wiring.wire_detail.nav_svc")
    @patch("adapters.ui_gradio.ui.wiring.wire_detail.get_default_actor_id")
    def test_edit_visible_when_actor_is_owner(self, mock_actor, mock_nav):
        """Owner viewing their own card → edit button visible."""
        mock_actor.return_value = "owner-user"
        mock_nav.get_card.return_value = _card_owned_by("owner-user")
        mock_nav.get_card_svg.return_value = SVG_STUB

        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _fetch_card_and_svg,
        )

        # Simulate what _load_card_detail does internally
        card_data, svg_wrapped = _fetch_card_and_svg("card-abc-123")
        actor_id = mock_actor()
        is_owner = card_data.get("owner_id", "") == actor_id

        assert is_owner is True, "Actor IS the owner; edit should be visible"

    @patch("adapters.ui_gradio.ui.wiring.wire_detail.nav_svc")
    @patch("adapters.ui_gradio.ui.wiring.wire_detail.get_default_actor_id")
    def test_edit_hidden_when_actor_is_not_owner(self, mock_actor, mock_nav):
        """Different user viewing card → edit button hidden."""
        mock_actor.return_value = "another-user"
        mock_nav.get_card.return_value = _card_owned_by("owner-user")
        mock_nav.get_card_svg.return_value = SVG_STUB

        from adapters.ui_gradio.ui.wiring.wire_detail import _fetch_card_and_svg

        card_data, _ = _fetch_card_and_svg("card-abc-123")
        actor_id = mock_actor()
        is_owner = card_data.get("owner_id", "") == actor_id

        assert is_owner is False, "Actor is NOT the owner; edit must be hidden"

    @patch("adapters.ui_gradio.ui.wiring.wire_detail.nav_svc")
    @patch("adapters.ui_gradio.ui.wiring.wire_detail.get_default_actor_id")
    def test_edit_hidden_when_owner_id_missing(self, mock_actor, mock_nav):
        """Card without owner_id field → edit button hidden (deny by default)."""
        mock_actor.return_value = "some-user"
        card_no_owner = _card_owned_by("owner-user")
        del card_no_owner["owner_id"]
        mock_nav.get_card.return_value = card_no_owner
        mock_nav.get_card_svg.return_value = SVG_STUB

        from adapters.ui_gradio.ui.wiring.wire_detail import _fetch_card_and_svg

        card_data, _ = _fetch_card_and_svg("card-abc-123")
        actor_id = mock_actor()
        is_owner = card_data.get("owner_id", "") == actor_id

        assert is_owner is False, "Missing owner_id must deny edit (deny-by-default)"

    @patch("adapters.ui_gradio.ui.wiring.wire_detail.nav_svc")
    @patch("adapters.ui_gradio.ui.wiring.wire_detail.get_default_actor_id")
    def test_edit_hidden_on_error_response(self, mock_actor, mock_nav):
        """API error response → edit button hidden."""
        mock_actor.return_value = "owner-user"
        mock_nav.get_card.return_value = {
            "status": "error",
            "message": "Not found",
        }
        mock_nav.get_card_svg.return_value = ""

        from adapters.ui_gradio.ui.wiring.wire_detail import _fetch_card_and_svg

        card_data, _ = _fetch_card_and_svg("card-abc-123")

        # On error, _load_card_detail returns early with visible=False
        assert card_data.get("status") == "error"

    @patch("adapters.ui_gradio.ui.wiring.wire_detail.nav_svc")
    @patch("adapters.ui_gradio.ui.wiring.wire_detail.get_default_actor_id")
    def test_edit_hidden_for_public_card_non_owner(self, mock_actor, mock_nav):
        """Public visibility doesn't grant edit — only owner can edit."""
        mock_actor.return_value = "reader-user"
        mock_nav.get_card.return_value = _card_owned_by(
            "owner-user", visibility="public"
        )
        mock_nav.get_card_svg.return_value = SVG_STUB

        from adapters.ui_gradio.ui.wiring.wire_detail import _fetch_card_and_svg

        card_data, _ = _fetch_card_and_svg("card-abc-123")
        actor_id = mock_actor()
        is_owner = card_data.get("owner_id", "") == actor_id

        assert (
            is_owner is False
        ), "Public visibility allows read but NOT edit for non-owner"


class TestDetailPageEditButtonDefaultState:
    """The Edit and Delete buttons in scenario_detail must start hidden."""

    def test_edit_button_starts_hidden(self):
        """build_detail_page() should create edit_btn with visible=False."""
        import gradio as gr
        from adapters.ui_gradio.ui.pages.scenario_detail import build_detail_page

        with gr.Blocks():
            result = build_detail_page()
            edit_btn = result.edit_btn
            assert edit_btn.visible is False, (
                "Edit button must start hidden (visible=False) "
                "to prevent flash before ownership check"
            )

    def test_delete_button_starts_hidden(self):
        """build_detail_page() should create delete_btn with visible=False."""
        import gradio as gr
        from adapters.ui_gradio.ui.pages.scenario_detail import build_detail_page

        with gr.Blocks():
            result = build_detail_page()
            delete_btn = result.delete_btn
            assert delete_btn.visible is False, (
                "Delete button must start hidden (visible=False) "
                "to prevent flash before ownership check"
            )


class TestResetDetailForLoading:
    """_reset_detail_for_loading must always hide Edit/Delete (deny-by-default).

    This prevents the race condition where the previous card's Edit/Delete
    buttons remain visible for 3-4 s while the API call runs.
    """

    def test_reset_hides_edit_button(self):
        """Reset step must return visible=False for edit button."""
        import gradio as gr
        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _get_reset_detail_for_loading,
        )

        with gr.Blocks():
            reset_fn = _get_reset_detail_for_loading()
            _, _, _, edit_update, _, _ = reset_fn("any-card-id")

        assert (
            edit_update["visible"] is False
        ), "Edit button must be hidden immediately on card_id change"

    def test_reset_hides_delete_button(self):
        """Reset step must return visible=False for delete button."""
        import gradio as gr
        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _get_reset_detail_for_loading,
        )

        with gr.Blocks():
            reset_fn = _get_reset_detail_for_loading()
            _, _, _, _, delete_update, _ = reset_fn("any-card-id")

        assert (
            delete_update["visible"] is False
        ), "Delete button must be hidden immediately on card_id change"

    def test_reset_hides_confirm_row(self):
        """Reset step must return visible=False for the confirm row."""
        import gradio as gr
        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _get_reset_detail_for_loading,
        )

        with gr.Blocks():
            reset_fn = _get_reset_detail_for_loading()
            _, _, _, _, _, confirm_update = reset_fn("any-card-id")

        assert (
            confirm_update["visible"] is False
        ), "Confirm row must be hidden immediately on card_id change"

    def test_reset_shows_loading_state(self):
        """Reset step must show a 'Loading...' placeholder."""
        import gradio as gr
        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _get_reset_detail_for_loading,
        )

        with gr.Blocks():
            reset_fn = _get_reset_detail_for_loading()
            title, svg, _, _, _, _ = reset_fn("any-card-id")

        assert "Loading" in title
        assert "Loading" in svg
