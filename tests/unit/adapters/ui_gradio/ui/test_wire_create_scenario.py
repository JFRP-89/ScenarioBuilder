"""Unit tests for Create Scenario handler in wire_generate."""

from __future__ import annotations

from unittest.mock import patch

from adapters.ui_gradio.ui.router import ALL_PAGES, PAGE_HOME
from adapters.ui_gradio.ui.wiring.wire_generate import _wire_create_scenario

# Number of page containers (mirrors ALL_PAGES)
_N_PAGES = len(ALL_PAGES)
# Handler returns: page_state + N visibilities + home_recent_html + status
_EXPECTED_LEN = 1 + _N_PAGES + 1 + 1


class _FakeComponent:
    """Minimal stub to capture .click() calls."""

    def __init__(self):
        self._click_fn = None

    def click(self, *, fn, inputs, outputs):
        self._click_fn = fn


def _make_fake_containers():
    """Create N_PAGES fake containers."""
    return [_FakeComponent() for _ in range(_N_PAGES)]


class TestOnCreateScenario:
    """Verify the _on_create_scenario handler logic."""

    def _get_handler(self):
        btn = _FakeComponent()
        status = _FakeComponent()
        output = _FakeComponent()
        page_state = _FakeComponent()
        page_containers = _make_fake_containers()
        home_recent_html = _FakeComponent()
        _wire_create_scenario(
            output=output,
            create_scenario_btn=btn,
            create_scenario_status=status,
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home_recent_html,
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
        assert "Generate a card first" in status["value"]

    def test_empty_dict(self):
        handler = self._get_handler()
        result = handler({})
        status = self._status(result)
        assert "Generate a card first" in status["value"]

    def test_error_status(self):
        handler = self._get_handler()
        result = handler({"status": "error", "message": "bad payload"})
        status = self._status(result)
        assert "bad payload" in status["value"]

    def test_missing_card_id(self):
        handler = self._get_handler()
        result = handler({"mode": "matched", "seed": 42})
        status = self._status(result)
        assert "No card_id found" in status["value"]

    @patch("adapters.ui_gradio.ui.wiring.wire_generate.load_recent_cards")
    @patch("adapters.ui_gradio.ui.wiring.wire_generate.nav_svc")
    def test_card_verified_success(self, mock_nav, mock_load):
        mock_nav.get_card.return_value = {
            "card_id": "abc-123",
            "mode": "matched",
        }
        mock_load.return_value = "<div>recent</div>"
        handler = self._get_handler()
        result = handler({"card_id": "abc-123", "mode": "matched"})
        status = self._status(result)
        assert "abc-123" in status["value"]
        assert "created" in status["value"].lower()
        assert status["visible"] is True
        # Navigates to Home
        assert result[0] == PAGE_HOME

    @patch("adapters.ui_gradio.ui.wiring.wire_generate.nav_svc")
    def test_card_not_found_in_flask(self, mock_nav):
        mock_nav.get_card.return_value = {
            "status": "error",
            "message": "Card not found: xyz",
        }
        handler = self._get_handler()
        result = handler({"card_id": "xyz"})
        status = self._status(result)
        assert "Could not verify" in status["value"]
        assert status["visible"] is True

    def test_non_dict_card_data(self):
        handler = self._get_handler()
        result = handler("not a dict")
        status = self._status(result)
        assert "Generate a card first" in status["value"]

    @patch("adapters.ui_gradio.ui.wiring.wire_generate.load_recent_cards")
    @patch("adapters.ui_gradio.ui.wiring.wire_generate.nav_svc")
    def test_success_refreshes_recent_cards(self, mock_nav, mock_load):
        mock_nav.get_card.return_value = {"card_id": "x1"}
        mock_load.return_value = "<div>cards list</div>"
        handler = self._get_handler()
        result = handler({"card_id": "x1"})
        # Second-to-last element is the recent cards HTML
        recent_html = result[-2]
        assert recent_html == "<div>cards list</div>"
        mock_load.assert_called_once()
