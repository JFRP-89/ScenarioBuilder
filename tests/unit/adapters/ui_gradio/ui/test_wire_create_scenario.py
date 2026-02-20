"""Unit tests for Create Scenario handler in wire_generate."""

from __future__ import annotations

from unittest.mock import patch

import gradio as gr
from adapters.ui_gradio.ui.router import ALL_PAGES, PAGE_HOME
from adapters.ui_gradio.ui.wiring.wire_generate import (
    _CreateScenarioCtx,
    _wire_create_scenario,
)

# Number of page containers (mirrors ALL_PAGES)
_N_PAGES = len(ALL_PAGES)

# Form components: 19 items (see _form_components list in wire_generate.py)
_N_FORM = 19
# Dropdown/list components passed to wire: 6
_N_DROPDOWNS = 6
# Handler returns: page_state + N visibilities
#                  + form resets + dropdown resets + btn reset + status
# Home data (recent_html, page_info, caches) is loaded via .then() chain.
_EXPECTED_LEN = 1 + _N_PAGES + _N_FORM + _N_DROPDOWNS + 1 + 1


class _FakeComponent:
    """Minimal stub to capture .click() calls."""

    def __init__(self):
        self._click_fn = None
        self._then_fn = None
        self._then_outputs = None

    def click(self, *, fn, inputs, outputs):
        self._click_fn = fn
        return self  # support .then() chaining

    def then(self, *, fn, inputs, outputs):
        self._then_fn = fn
        self._then_outputs = outputs
        return self


def _make_fake_containers():
    """Create N_PAGES fake containers."""
    return [_FakeComponent() for _ in range(_N_PAGES)]


class TestOnCreateScenario:
    """Verify the _on_create_scenario handler logic."""

    def _get_handler(self):
        btn = _FakeComponent()
        status = _FakeComponent()
        output = _FakeComponent()
        svg_preview = _FakeComponent()
        page_state = _FakeComponent()
        page_containers = _make_fake_containers()
        home_recent_html = _FakeComponent()
        # Form components for reset
        scenario_name = _FakeComponent()
        mode = _FakeComponent()
        is_replicable = _FakeComponent()
        generate_from_seed = _FakeComponent()
        armies = _FakeComponent()
        deployment = _FakeComponent()
        layout = _FakeComponent()
        objectives = _FakeComponent()
        initial_priority = _FakeComponent()
        visibility = _FakeComponent()
        shared_with = _FakeComponent()
        special_rules_state = _FakeComponent()
        objectives_with_vp_toggle = _FakeComponent()
        vp_state = _FakeComponent()
        scenography_state = _FakeComponent()
        deployment_zones_state = _FakeComponent()
        objective_points_state = _FakeComponent()
        # Dropdown lists for reset
        vp_input = gr.Textbox(visible=False)
        vp_list = gr.Dropdown(visible=False)
        rules_list = gr.Dropdown(visible=False)
        scenography_list = gr.Dropdown(visible=False)
        deployment_zones_list = gr.Dropdown(visible=False)
        objective_points_list = gr.Dropdown(visible=False)

        _wire_create_scenario(
            ctx=_CreateScenarioCtx(
                output=output,
                preview_full_state=output,
                create_scenario_btn=btn,
                create_scenario_status=status,
                svg_preview=svg_preview,
                page_state=page_state,
                page_containers=page_containers,
                home_recent_html=home_recent_html,
                scenario_name=scenario_name,
                mode=mode,
                is_replicable=is_replicable,
                generate_from_seed=generate_from_seed,
                armies=armies,
                deployment=deployment,
                layout=layout,
                objectives=objectives,
                initial_priority=initial_priority,
                visibility=visibility,
                shared_with=shared_with,
                special_rules_state=special_rules_state,
                objectives_with_vp_toggle=objectives_with_vp_toggle,
                vp_state=vp_state,
                scenography_state=scenography_state,
                deployment_zones_state=deployment_zones_state,
                objective_points_state=objective_points_state,
                vp_input=vp_input,
                vp_list=vp_list,
                rules_list=rules_list,
                scenography_list=scenography_list,
                deployment_zones_list=deployment_zones_list,
                objective_points_list=objective_points_list,
                home_page_info=_FakeComponent(),
                home_page_state=_FakeComponent(),
                home_cards_cache_state=_FakeComponent(),
                home_fav_ids_cache_state=_FakeComponent(),
            )
        )
        return btn._click_fn

    @staticmethod
    def _status(result):
        """Extract the status update dict (last element of the tuple)."""
        return result[-1]

    def test_none_card_data(self):
        handler = self._get_handler()
        result = handler(None)
        assert len(result) == _EXPECTED_LEN
        status = self._status(result)
        assert status["visible"] is True
        assert "preview first" in status["value"].lower()

    def test_empty_dict(self):
        handler = self._get_handler()
        result = handler({})
        status = self._status(result)
        assert "preview first" in status["value"].lower()

    def test_error_status(self):
        handler = self._get_handler()
        result = handler({"status": "error", "message": "bad payload"})
        status = self._status(result)
        assert "bad payload" in status["value"]

    def test_no_preview_status(self):
        """Data without status='preview' should be rejected."""
        handler = self._get_handler()
        result = handler({"mode": "matched", "seed": 42})
        status = self._status(result)
        assert "preview first" in status["value"].lower()

    @patch("adapters.ui_gradio.ui.wiring.wire_generate.load_recent_cards")
    @patch("adapters.ui_gradio.ui.wiring.wire_generate.handle_create_scenario")
    def test_create_success(self, mock_create, mock_load):
        mock_create.return_value = {
            "card_id": "abc-123",
            "mode": "matched",
        }
        handler = self._get_handler()
        preview = {
            "status": "preview",
            "_payload": {"name": "Test"},
            "_actor_id": "actor-1",
        }
        result = handler(preview)
        status = self._status(result)
        assert "abc-123" in status["value"]
        assert "created" in status["value"].lower()
        assert status["visible"] is True
        # Navigates to Home
        assert result[0] == PAGE_HOME

    @patch("adapters.ui_gradio.ui.wiring.wire_generate.handle_create_scenario")
    def test_create_api_error(self, mock_create):
        mock_create.return_value = {
            "status": "error",
            "message": "Server error",
        }
        handler = self._get_handler()
        preview = {
            "status": "preview",
            "_payload": {"name": "Test"},
            "_actor_id": "actor-1",
        }
        result = handler(preview)
        status = self._status(result)
        assert "Server error" in status["value"]
        assert status["visible"] is True

    def test_non_dict_card_data(self):
        handler = self._get_handler()
        result = handler("not a dict")
        status = self._status(result)
        assert "preview first" in status["value"].lower()

    @patch("adapters.ui_gradio.ui.wiring.wire_generate.load_recent_cards")
    @patch("adapters.ui_gradio.ui.wiring.wire_generate.handle_create_scenario")
    def test_success_refreshes_recent_cards(self, mock_create, mock_load):
        """Home data is refreshed via .then() chain, not inline."""
        mock_create.return_value = {"card_id": "x1"}
        handler = self._get_handler()
        preview = {
            "status": "preview",
            "_payload": {"name": "Test"},
            "_actor_id": "actor-1",
        }
        result = handler(preview)  # noqa: F841
        # load_recent_cards is NOT called inline by the handler;
        # it is invoked by the .then() chain wired in _wire_create_scenario.
        mock_load.assert_not_called()
