"""Unit tests for services.navigation — direct use-case wrappers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from adapters.ui_gradio.services.navigation import (
    delete_card,
    get_card,
    get_card_svg,
    list_cards,
    list_favorites,
    toggle_favorite,
)

# ── Helpers ────────────────────────────────────────────────────────


def _mock_services(**overrides):
    """Return a mock Services container with overridden use cases."""
    svc = MagicMock()
    for name, value in overrides.items():
        setattr(svc, name, value)
    return svc


def _card_snapshot(
    card_id="c1",
    owner_id="actor1",
    mode="matched",
    visibility="public",
    seed=42,
    name="Test",
    table_preset="standard",
    table_mm=None,
):
    """Fake _CardSnapshot-like object."""
    obj = MagicMock()
    obj.card_id = card_id
    obj.owner_id = owner_id
    obj.mode = mode
    obj.visibility = visibility
    obj.seed = seed
    obj.name = name
    obj.table_preset = table_preset
    obj.table_mm = table_mm or {"width_mm": 1220, "height_mm": 1220}
    return obj


class TestListCards:
    """list_cards() via direct use-case call."""

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_success(self, mock_get):
        uc = MagicMock()
        resp = MagicMock()
        resp.cards = [_card_snapshot(card_id="c1")]
        uc.execute.return_value = resp
        mock_get.return_value = MagicMock(list_cards=uc)

        result = list_cards("actor1", "mine")
        assert len(result["cards"]) == 1
        assert result["cards"][0]["card_id"] == "c1"

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_error_status(self, mock_get):
        uc = MagicMock()
        uc.execute.side_effect = ValueError("bad filter")
        mock_get.return_value = MagicMock(list_cards=uc)

        result = list_cards("actor1")
        assert result.get("status") == "error"
        assert "bad filter" in result["message"]

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_services_not_initialised(self, mock_get):
        mock_get.side_effect = RuntimeError("Services not initialised")
        result = list_cards("actor1")
        assert result["status"] == "error"


class TestGetCard:
    """get_card() via direct use-case call."""

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_success(self, mock_get):
        uc = MagicMock()
        resp = MagicMock()
        resp.card_id = "c1"
        resp.owner_id = "actor1"
        resp.seed = 42
        resp.mode = "matched"
        resp.visibility = "public"
        resp.table_mm = {"width_mm": 1220, "height_mm": 1220}
        resp.table_preset = "standard"
        resp.name = "Test"
        resp.shared_with = []
        resp.armies = None
        resp.deployment = None
        resp.layout = None
        resp.objectives = None
        resp.initial_priority = None
        resp.special_rules = None
        resp.shapes = {}
        uc.execute.return_value = resp
        mock_get.return_value = MagicMock(get_card=uc)

        result = get_card("actor1", "c1")
        assert result["card_id"] == "c1"

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_not_found(self, mock_get):
        uc = MagicMock()
        uc.execute.side_effect = Exception("Card not found")
        mock_get.return_value = MagicMock(get_card=uc)

        result = get_card("actor1", "nonexistent")
        assert result.get("status") == "error"


class TestToggleFavorite:
    """toggle_favorite() via direct use-case call."""

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_toggle_on(self, mock_get):
        uc = MagicMock()
        resp = MagicMock()
        resp.card_id = "c1"
        resp.is_favorite = True
        uc.execute.return_value = resp
        mock_get.return_value = MagicMock(toggle_favorite=uc)

        result = toggle_favorite("actor1", "c1")
        assert result["is_favorite"] is True

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_error(self, mock_get):
        uc = MagicMock()
        uc.execute.side_effect = Exception("fail")
        mock_get.return_value = MagicMock(toggle_favorite=uc)

        result = toggle_favorite("actor1", "c1")
        assert result["status"] == "error"


class TestDeleteCard:
    """delete_card() via direct use-case call."""

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_success(self, mock_get):
        uc = MagicMock()
        resp = MagicMock()
        resp.card_id = "c1"
        resp.deleted = True
        uc.execute.return_value = resp
        mock_get.return_value = MagicMock(delete_card=uc)

        result = delete_card("actor1", "c1")
        assert result == {"card_id": "c1", "deleted": True}


class TestListFavorites:
    """list_favorites() via direct use-case call."""

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_success(self, mock_get):
        uc = MagicMock()
        resp = MagicMock()
        resp.card_ids = ["c1", "c2"]
        uc.execute.return_value = resp
        mock_get.return_value = MagicMock(list_favorites=uc)

        result = list_favorites("actor1")
        assert result == {"card_ids": ["c1", "c2"]}


class TestGetCardSvg:
    """get_card_svg() via direct use-case call."""

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_success(self, mock_get):
        uc = MagicMock()
        resp = MagicMock()
        resp.svg = '<svg width="100" height="100"></svg>'
        uc.execute.return_value = resp
        mock_get.return_value = MagicMock(render_map_svg=uc)

        result = get_card_svg("actor1", "c1")
        assert "<svg" in result

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_error_returns_placeholder(self, mock_get):
        uc = MagicMock()
        uc.execute.side_effect = Exception("render failed")
        mock_get.return_value = MagicMock(render_map_svg=uc)

        result = get_card_svg("actor1", "c1")
        assert "unavailable" in result

    @patch("adapters.ui_gradio.services.navigation.get_services")
    def test_services_not_ready_returns_placeholder(self, mock_get):
        mock_get.side_effect = RuntimeError("Services not initialised")
        result = get_card_svg("actor1", "c1")
        assert "unavailable" in result
