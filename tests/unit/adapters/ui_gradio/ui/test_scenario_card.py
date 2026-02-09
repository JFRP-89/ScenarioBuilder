"""Unit tests for ui.components.scenario_card — card rendering helpers."""

from __future__ import annotations

from adapters.ui_gradio.ui.components.scenario_card import (
    render_card_html,
    render_card_list_html,
)


class TestRenderCardHtml:
    """render_card_html() produces card summary HTML."""

    def test_basic_card(self):
        card = {
            "card_id": "abc-123",
            "name": "Test Scenario",
            "mode": "matched",
            "owner_id": "alice",
            "visibility": "public",
            "seed": 42,
        }
        html = render_card_html(card)
        assert "Test Scenario" in html
        assert "matched" in html
        assert "alice" in html
        assert "42" in html

    def test_favorite_shows_filled_star(self):
        card = {"card_id": "x", "name": "N", "mode": "m", "owner_id": "o"}
        html = render_card_html(card, is_favorite=True)
        assert "★" in html

    def test_not_favorite_shows_empty_star(self):
        card = {"card_id": "x", "name": "N", "mode": "m", "owner_id": "o"}
        html = render_card_html(card, is_favorite=False)
        assert "☆" in html

    def test_no_actions(self):
        card = {"card_id": "x", "name": "N", "mode": "m", "owner_id": "o"}
        html = render_card_html(card, show_actions=False)
        assert "card-view-btn" not in html
        assert "card-fav-btn" not in html

    def test_missing_fields_use_defaults(self):
        html = render_card_html({})
        assert "Scenario" in html
        assert "???" in html  # card_id default


class TestRenderCardListHtml:
    """render_card_list_html() combines multiple cards."""

    def test_empty_list_shows_message(self):
        html = render_card_list_html([])
        assert "No scenarios found" in html

    def test_single_card(self):
        cards = [{"card_id": "c1", "name": "One", "mode": "open", "owner_id": "u1"}]
        html = render_card_list_html(cards)
        assert "One" in html

    def test_multiple_cards(self):
        cards = [
            {"card_id": f"c{i}", "name": f"Card {i}", "mode": "m", "owner_id": "u"}
            for i in range(3)
        ]
        html = render_card_list_html(cards)
        assert "Card 0" in html
        assert "Card 2" in html

    def test_favorites_highlighted(self):
        cards = [
            {"card_id": "c1", "name": "Faved", "mode": "m", "owner_id": "u"},
            {"card_id": "c2", "name": "Normal", "mode": "m", "owner_id": "u"},
        ]
        html = render_card_list_html(cards, favorite_ids={"c1"})
        # c1 should have filled star, c2 empty star
        assert "★" in html
        assert "☆" in html
