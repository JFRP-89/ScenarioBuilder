"""Unit tests for wire_navigation — form reset and page reload.

Verifies that:
- Clicking 'Create New Scenario' resets all form fields and clears edit state.
- Back→Home buttons chain a home-data reload when ``home_reload_fn`` is set.
- List/Favorites pages always reload data (no skip-reload cache).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import gradio as gr
from adapters.ui_gradio.ui.router import PAGE_CREATE, PAGE_HOME
from adapters.ui_gradio.ui.wiring.wire_navigation import (
    NavigationCtx,
    _expired_result,
    wire_navigation,
)

# ── Helpers ────────────────────────────────────────────────────────


def _mock_component():
    """Return a mock Gradio component."""
    return MagicMock(spec=gr.Textbox)


def _build_nav_kwargs(
    *,
    with_form: bool = False,
    **extra,
):
    """Build a ``NavigationCtx`` for ``wire_navigation()``.

    When *with_form* is True, includes create-form components,
    dropdowns, editing_card_id, and heading so form resets are wired.
    """
    fields = {
        "page_state": MagicMock(spec=gr.State),
        "previous_page_state": MagicMock(spec=gr.State),
        "page_containers": [MagicMock(spec=gr.Column) for _ in range(6)],
        "home_create_btn": MagicMock(spec=gr.Button),
        "list_back_btn": MagicMock(spec=gr.Button),
        "detail_back_btn": MagicMock(spec=gr.Button),
        "create_back_btn": MagicMock(spec=gr.Button),
        "edit_back_btn": MagicMock(spec=gr.Button),
        "favorites_back_btn": MagicMock(spec=gr.Button),
        "session_id_state": MagicMock(spec=gr.State),
        "actor_id_state": MagicMock(spec=gr.State),
        "login_panel": MagicMock(spec=gr.Column),
        "top_bar_row": MagicMock(spec=gr.Row),
        "login_message": MagicMock(spec=gr.Textbox),
    }
    if with_form:
        fields["create_form_components"] = [_mock_component() for _ in range(19)]
        fields["create_dropdown_lists"] = [_mock_component() for _ in range(6)]
        fields["editing_card_id"] = MagicMock(spec=gr.State)
        fields["create_heading_md"] = MagicMock(spec=gr.Markdown)
    fields.update(extra)
    return NavigationCtx(**fields)  # type: ignore[arg-type]


def _click_mock(component: Any) -> Any:
    """Access the ``.click`` mock on a Gradio component.

    Gradio 4.x adds event-listener methods (``click``, ``change``, ...)
    at class-creation time via descriptors.  Pylance cannot resolve them
    statically, so this helper routes through ``Any`` to avoid false
    "has no 'click' member" diagnostics in test code.
    """
    return component.click


def _extract_click_handler(btn_mock: MagicMock) -> tuple:
    """Extract (fn, inputs, outputs) from the first .click() call."""
    assert btn_mock.click.called, "Button .click() was never called"
    call = btn_mock.click.call_args
    fn = call.kwargs.get("fn") or call.args[0]
    inputs = call.kwargs.get("inputs", [])
    outputs = call.kwargs.get("outputs", [])
    return fn, inputs, outputs


# ── Tests ──────────────────────────────────────────────────────────


class TestExpiredResult:
    """_expired_result() helper."""

    def test_returns_correct_length(self):
        n_containers = 6
        result = _expired_result(n_containers)
        # page_state + 6 containers + session + actor + login + topbar + message
        assert len(result) == 1 + n_containers + 5

    def test_page_state_reset_to_home(self):
        result = _expired_result(4)
        assert result[0] == PAGE_HOME


class TestWireNavigationWithoutForm:
    """Backward compatibility: wire_navigation works without form components."""

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_create_btn_wired_with_basic_nav(self, _mock_valid):
        ctx = _build_nav_kwargs(with_form=False)
        wire_navigation(ctx=ctx)
        assert _click_mock(ctx.home_create_btn).called

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_basic_nav_output_count(self, _mock_valid):
        ctx = _build_nav_kwargs(with_form=False)
        wire_navigation(ctx=ctx)
        _, _, outputs = _extract_click_handler(ctx.home_create_btn)
        # page_state + 6 containers + session + actor + login + topbar + message = 12
        assert len(outputs) == 12


class TestWireNavigationWithFormReset:
    """When create_form_components is supplied, Create resets the form."""

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_create_btn_output_includes_form_resets(self, _mock_valid):
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        _, _, outputs = _extract_click_handler(ctx.home_create_btn)
        # 12 nav + 19 form + 6 dropdowns + 2 extra (editing_card_id + heading) = 39
        assert len(outputs) == 39

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_guarded_create_resets_form_on_valid_session(self, mock_valid):
        mock_valid.return_value = True
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        fn, _, _ = _extract_click_handler(ctx.home_create_btn)

        result = fn("valid-session-id")

        # Should return 39 values total
        assert len(result) == 39

        # First value should be the PAGE_CREATE page state
        assert result[0] == PAGE_CREATE

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_guarded_create_clears_editing_card_id(self, mock_valid):
        mock_valid.return_value = True
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        fn, _, _ = _extract_click_handler(ctx.home_create_btn)

        result = fn("valid-session-id")
        result_list = list(result)

        # editing_card_id is the second-to-last value (before heading)
        # nav(12) + form(19) + dropdowns(6) = 37 → index 37 = editing_card_id
        editing_card_id_val = result_list[37]
        assert (
            editing_card_id_val == ""
        ), f"editing_card_id should be cleared, got {editing_card_id_val!r}"

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_guarded_create_resets_heading(self, mock_valid):
        mock_valid.return_value = True
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        fn, _, _ = _extract_click_handler(ctx.home_create_btn)

        result = fn("valid-session-id")
        result_list = list(result)

        # heading is the last value
        heading_val = result_list[-1]
        # build_extra_resets returns gr.update(value="## Create New Scenario")
        assert heading_val["value"] == "## Create New Scenario"

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_guarded_create_returns_expired_on_invalid_session(self, mock_valid):
        mock_valid.return_value = False
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        fn, _, _ = _extract_click_handler(ctx.home_create_btn)

        result = fn("expired-session-id")
        result_list = list(result)

        # Should still return 39 values (12 nav expired + 27 gr.update())
        assert len(result_list) == 39

        # First value should be PAGE_HOME (expired→reset)
        assert result_list[0] == PAGE_HOME

        # session_id_state should be cleared (empty string)
        # nav expired: [PAGE_HOME, *6 hidden containers, "", "", show, hide, msg]
        assert result_list[7] == ""  # session_id_state cleared
        assert result_list[8] == ""  # actor_id_state cleared

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_form_resets_contain_default_values(self, mock_valid):
        """Verify key form fields are reset to sensible defaults."""
        mock_valid.return_value = True
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        fn, _, _ = _extract_click_handler(ctx.home_create_btn)

        result = fn("valid-session-id")
        result_list = list(result)

        # Form resets start at index 12 (after nav outputs)
        form_start = 12
        # Index 0 → scenario_name → gr.update(value="")
        assert result_list[form_start]["value"] == ""
        # Index 1 → mode → gr.update(value="casual")
        assert result_list[form_start + 1]["value"] == "casual"
        # Index 2 → is_replicable → gr.update(value=True)
        assert result_list[form_start + 2]["value"] is True
        # Index 9 → visibility → gr.update(value="public")
        assert result_list[form_start + 9]["value"] == "public"

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_state_resets_are_empty_lists(self, mock_valid):
        """Verify gr.State components (lists) are reset to []."""
        mock_valid.return_value = True
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        fn, _, _ = _extract_click_handler(ctx.home_create_btn)

        result = fn("valid-session-id")
        result_list = list(result)

        form_start = 12
        # Index 11 → special_rules_state → []
        assert result_list[form_start + 11] == []
        # Index 14 → scenography_state → []
        assert result_list[form_start + 14] == []
        # Index 15 → deployment_zones_state → []
        assert result_list[form_start + 15] == []
        # Index 16 → objective_points_state → []
        assert result_list[form_start + 16] == []


class TestBackButtonsUnchanged:
    """Back buttons should still work with simple navigation (no form reset)."""

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_list_back_btn_wired(self, _mock_valid):
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        assert _click_mock(ctx.list_back_btn).called

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_create_back_btn_wired(self, _mock_valid):
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        assert _click_mock(ctx.create_back_btn).called

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_detail_back_btn_wired(self, _mock_valid):
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        assert _click_mock(ctx.detail_back_btn).called

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_back_buttons_have_basic_output_count(self, _mock_valid):
        """Back buttons should NOT include form resets in their outputs."""
        ctx = _build_nav_kwargs(with_form=True)
        wire_navigation(ctx=ctx)
        _, _, outputs = _extract_click_handler(ctx.list_back_btn)
        # Only navigation outputs, no form resets
        assert len(outputs) == 12


class TestBackHomeReload:
    """Back→Home buttons chain a home-data reload when reload_fn is set."""

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_back_buttons_chain_then_when_reload_fn_provided(self, _mock_valid):
        """Each back→home button should call .then() with reload function."""
        mock_reload_fn = MagicMock()
        mock_reload_inputs = [MagicMock()]
        mock_reload_outputs = [MagicMock()]
        ctx = _build_nav_kwargs(
            with_form=False,
            home_reload_fn=mock_reload_fn,
            home_reload_inputs=mock_reload_inputs,
            home_reload_outputs=mock_reload_outputs,
        )

        wire_navigation(ctx=ctx)

        for btn_name in ("list_back_btn", "create_back_btn", "favorites_back_btn"):
            btn = getattr(ctx, btn_name)
            event = _click_mock(btn).return_value
            assert event.then.called, f"{btn_name} should chain .then()"
            then_kwargs = event.then.call_args.kwargs
            assert then_kwargs["fn"] is mock_reload_fn
            assert then_kwargs["inputs"] is mock_reload_inputs
            assert then_kwargs["outputs"] is mock_reload_outputs

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_back_buttons_no_then_without_reload_fn(self, _mock_valid):
        """Without reload_fn, back buttons should not chain .then()."""
        ctx = _build_nav_kwargs(with_form=False)
        wire_navigation(ctx=ctx)

        for btn_name in ("list_back_btn", "create_back_btn", "favorites_back_btn"):
            btn = getattr(ctx, btn_name)
            event = _click_mock(btn).return_value
            assert not event.then.called, f"{btn_name} should NOT chain .then()"

    @patch("adapters.ui_gradio.ui.wiring.wire_navigation.is_session_valid")
    def test_detail_back_btn_does_not_chain_then(self, _mock_valid):
        """Detail/edit back go to previous_page, not necessarily home."""
        ctx = _build_nav_kwargs(
            with_form=False,
            home_reload_fn=MagicMock(),
            home_reload_inputs=[],
            home_reload_outputs=[],
        )

        wire_navigation(ctx=ctx)

        for btn_name in ("detail_back_btn", "edit_back_btn"):
            btn = getattr(ctx, btn_name)
            event = _click_mock(btn).return_value
            assert not event.then.called, f"{btn_name} should NOT chain .then()"
