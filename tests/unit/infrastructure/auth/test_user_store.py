"""Unit tests — user_store display-name helpers."""

from __future__ import annotations

import pytest

from infrastructure.auth.user_store import (
    create_user,
    get_display_name,
    get_display_names,
    reset_stores,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_stores()
    create_user("alice", "pw", "Alice Wonderland", "alice@example.com")
    create_user("bob", "pw", "Bob Builder", "bob@example.com")
    yield
    reset_stores()


class TestGetDisplayName:
    """get_display_name() resolves username → display name."""

    def test_known_user(self):
        assert get_display_name("alice") == "Alice Wonderland"

    def test_unknown_user_returns_username(self):
        assert get_display_name("unknown") == "unknown"

    def test_empty_name_returns_username(self):
        create_user("noname", "pw", "", "noname@example.com")
        assert get_display_name("noname") == "noname"


class TestGetDisplayNames:
    """get_display_names() batch-resolves usernames."""

    def test_all_known(self):
        result = get_display_names(["alice", "bob"])
        assert result == {"alice": "Alice Wonderland", "bob": "Bob Builder"}

    def test_mixed_known_unknown(self):
        result = get_display_names(["alice", "ghost"])
        assert result["alice"] == "Alice Wonderland"
        assert result["ghost"] == "ghost"

    def test_empty_list(self):
        assert get_display_names([]) == {}
