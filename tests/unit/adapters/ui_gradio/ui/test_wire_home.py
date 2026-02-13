"""Unit tests for wire_home — load_recent_cards + wire_home_page."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestLoadRecentCards:
    """Verify load_recent_cards renders cards from Flask API."""

    @patch("adapters.ui_gradio.ui.wiring.wire_home.nav_svc")
    def test_returns_error_html_on_api_error(self, mock_nav):
        mock_nav.list_cards.return_value = {
            "status": "error",
            "message": "Connection refused",
        }
        from adapters.ui_gradio.ui.wiring.wire_home import load_recent_cards

        result = load_recent_cards()
        html = result[0]
        assert "Connection refused" in html
        assert "color:red" in html

    @patch("adapters.ui_gradio.ui.wiring.wire_home.nav_svc")
    def test_returns_placeholder_when_no_cards(self, mock_nav):
        mock_nav.list_cards.return_value = {"cards": []}
        mock_nav.list_favorites.return_value = {"card_ids": []}
        from adapters.ui_gradio.ui.wiring.wire_home import load_recent_cards

        result = load_recent_cards()
        html = result[0]
        assert "No scenarios match the selected filters." in html

    @patch("adapters.ui_gradio.ui.wiring.wire_home.nav_svc")
    def test_renders_cards_with_favorites(self, mock_nav):
        mock_nav.list_cards.return_value = {
            "cards": [
                {
                    "card_id": "c1",
                    "owner_id": "actor-1",
                    "mode": "matched",
                    "visibility": "private",
                }
            ]
        }
        mock_nav.list_favorites.return_value = {"card_ids": ["c1"]}
        from adapters.ui_gradio.ui.wiring.wire_home import load_recent_cards

        result = load_recent_cards()
        html = result[0]
        assert "c1" in html

    @patch("adapters.ui_gradio.ui.wiring.wire_home.nav_svc")
    def test_wire_home_page_registers_app_load(self, mock_nav):
        """wire_home_page should call app.load with the right outputs."""
        from adapters.ui_gradio.ui.wiring.wire_home import wire_home_page

        mock_app = MagicMock()
        mock_html = MagicMock()
        mock_mode_filter = MagicMock()
        mock_preset_filter = MagicMock()
        mock_unit_selector = MagicMock()
        mock_search_box = MagicMock()
        mock_per_page_dropdown = MagicMock()
        mock_reload_btn = MagicMock()
        mock_prev_btn = MagicMock()
        mock_page_info = MagicMock()
        mock_next_btn = MagicMock()
        mock_page_state = MagicMock()
        mock_cards_cache_state = MagicMock()
        mock_fav_ids_cache_state = MagicMock()

        wire_home_page(
            home_recent_html=mock_html,
            home_mode_filter=mock_mode_filter,
            home_preset_filter=mock_preset_filter,
            home_unit_selector=mock_unit_selector,
            home_search_box=mock_search_box,
            home_per_page_dropdown=mock_per_page_dropdown,
            home_reload_btn=mock_reload_btn,
            home_prev_btn=mock_prev_btn,
            home_page_info=mock_page_info,
            home_next_btn=mock_next_btn,
            home_page_state=mock_page_state,
            home_cards_cache_state=mock_cards_cache_state,
            home_fav_ids_cache_state=mock_fav_ids_cache_state,
            app=mock_app,
        )
        mock_app.load.assert_called_once()
        call_kwargs = mock_app.load.call_args
        assert mock_html in call_kwargs.kwargs["outputs"]
