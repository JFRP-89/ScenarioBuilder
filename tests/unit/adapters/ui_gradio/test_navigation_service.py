"""Unit tests for services.navigation — API client for card/favorites."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from adapters.ui_gradio.services.navigation import (
    get_card,
    get_card_svg,
    list_cards,
    list_favorites,
    toggle_favorite,
)


class TestListCards:
    """list_cards() API wrapper."""

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_success(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"cards": [{"card_id": "c1"}]}
        mock_req.request.return_value = resp
        result = list_cards("actor1", "mine")
        assert result == {"cards": [{"card_id": "c1"}]}
        mock_req.request.assert_called_once()

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_error_status(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 500
        resp.json.return_value = {"message": "Internal error"}
        mock_req.request.return_value = resp
        result = list_cards("actor1")
        assert result.get("status") == "error"

    @patch("adapters.ui_gradio.services.navigation.requests", None)
    def test_no_requests_library(self):
        result = list_cards("actor1")
        assert result["status"] == "error"
        assert "not available" in result["message"]


class TestGetCard:
    """get_card() API wrapper."""

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_success(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"card_id": "c1", "mode": "matched"}
        mock_req.request.return_value = resp
        result = get_card("actor1", "c1")
        assert result["card_id"] == "c1"

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_not_found(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 404
        resp.json.return_value = {"message": "Not found"}
        mock_req.request.return_value = resp
        result = get_card("actor1", "nonexistent")
        assert result.get("status") == "error"


class TestToggleFavorite:
    """toggle_favorite() API wrapper."""

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_toggle_on(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"card_id": "c1", "is_favorite": True}
        mock_req.request.return_value = resp
        result = toggle_favorite("actor1", "c1")
        assert result["is_favorite"] is True

    @patch("adapters.ui_gradio.services.navigation.requests", None)
    def test_no_requests_library(self):
        result = toggle_favorite("actor1", "c1")
        assert result["status"] == "error"


class TestListFavorites:
    """list_favorites() API wrapper."""

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_success(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"card_ids": ["c1", "c2"]}
        mock_req.request.return_value = resp
        result = list_favorites("actor1")
        assert result == {"card_ids": ["c1", "c2"]}


class TestGetCardSvg:
    """get_card_svg() API wrapper."""

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_success(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = '<svg width="100" height="100"></svg>'
        mock_req.get.return_value = resp
        result = get_card_svg("actor1", "c1")
        assert "<svg" in result

    @patch("adapters.ui_gradio.services.navigation.requests")
    @patch(
        "adapters.ui_gradio.services.navigation.get_api_base_url",
        return_value="http://test:8000",
    )
    def test_error_returns_placeholder(self, _url, mock_req):
        resp = MagicMock()
        resp.status_code = 500
        mock_req.get.return_value = resp
        result = get_card_svg("actor1", "c1")
        assert "unavailable" in result

    @patch("adapters.ui_gradio.services.navigation.requests", None)
    def test_no_requests_returns_placeholder(self):
        result = get_card_svg("actor1", "c1")
        assert "unavailable" in result
