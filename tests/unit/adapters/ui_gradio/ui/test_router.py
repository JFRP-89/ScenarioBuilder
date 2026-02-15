"""Unit tests for ui.router — page constants and navigation helpers."""

from __future__ import annotations

from adapters.ui_gradio.ui.router import (
    ALL_PAGES,
    DEFAULT_PAGE,
    PAGE_CREATE,
    PAGE_DETAIL,
    PAGE_EDIT,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
    navigate_to_detail,
    navigate_to_edit,
    page_visibility,
)


class TestPageConstants:
    """Page constant definitions."""

    def test_all_pages_has_six_entries(self):
        assert len(ALL_PAGES) == 6

    def test_default_page_is_home(self):
        assert DEFAULT_PAGE == PAGE_HOME

    def test_page_names_are_unique(self):
        assert len(set(ALL_PAGES)) == len(ALL_PAGES)

    def test_all_pages_includes_expected(self):
        for page in [
            PAGE_HOME,
            PAGE_LIST,
            PAGE_DETAIL,
            PAGE_CREATE,
            PAGE_EDIT,
            PAGE_FAVORITES,
        ]:
            assert page in ALL_PAGES


class TestPageVisibility:
    """page_visibility() returns correct show/hide updates."""

    def test_home_visible_hides_others(self):
        updates = page_visibility(PAGE_HOME)
        assert len(updates) == len(ALL_PAGES)
        # Only HOME (index 0) should be visible
        for i, upd in enumerate(updates):
            expected = ALL_PAGES[i] == PAGE_HOME
            assert upd["visible"] == expected, f"Page {ALL_PAGES[i]}"

    def test_create_visible_hides_others(self):
        updates = page_visibility(PAGE_CREATE)
        for i, upd in enumerate(updates):
            expected = ALL_PAGES[i] == PAGE_CREATE
            assert upd["visible"] == expected

    def test_unknown_page_hides_all(self):
        updates = page_visibility("nonexistent")
        assert all(not upd["visible"] for upd in updates)


class TestNavigateTo:
    """navigate_to() returns correct state + visibility tuple."""

    def test_navigate_to_home(self):
        result = navigate_to(PAGE_HOME)
        assert result[0] == PAGE_HOME
        # 1 state + 6 visibility updates
        assert len(result) == 1 + len(ALL_PAGES)

    def test_navigate_to_list(self):
        result = navigate_to(PAGE_LIST)
        assert result[0] == PAGE_LIST

    def test_navigate_to_favorites(self):
        result = navigate_to(PAGE_FAVORITES)
        assert result[0] == PAGE_FAVORITES


class TestNavigateToDetail:
    """navigate_to_detail() includes card_id and previous_page in output."""

    def test_returns_card_id(self):
        result = navigate_to_detail("card-abc-123")
        assert result[0] == PAGE_DETAIL
        assert result[1] == "card-abc-123"
        assert result[3] == 1  # reload_trigger should be 1 (incremented from default 0)
        # 1 page_state + 1 card_id + 1 previous_page + 1 reload_trigger + 6 visibility
        assert len(result) == 4 + len(ALL_PAGES)

    def test_returns_default_from_page(self):
        result = navigate_to_detail("card-abc-123")
        assert result[2] == PAGE_HOME, "Default from_page should be HOME"

    def test_returns_custom_from_page(self):
        result = navigate_to_detail("card-abc-123", from_page=PAGE_LIST)
        assert result[2] == PAGE_LIST

    def test_reload_trigger_increments(self):
        """reload_trigger should increment to force reloads."""
        result1 = navigate_to_detail("card-1", reload_trigger=0)
        assert result1[3] == 1
        result2 = navigate_to_detail("card-1", reload_trigger=5)
        assert result2[3] == 6


class TestNavigateToEdit:
    """navigate_to_edit() includes card_id in output."""

    def test_returns_card_id(self):
        result = navigate_to_edit("card-xyz-789")
        assert result[0] == PAGE_EDIT
        assert result[1] == "card-xyz-789"
        assert len(result) == 2 + len(ALL_PAGES)
