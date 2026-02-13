"""Tests for _payload._visibility — visibility application."""

from __future__ import annotations

from adapters.ui_gradio.builders._payload._visibility import apply_visibility


class TestApplyVisibility:
    def test_private(self):
        payload: dict = {}
        apply_visibility(payload, "private")
        assert payload["visibility"] == "private"
        assert "shared_with" not in payload

    def test_public(self):
        payload: dict = {}
        apply_visibility(payload, "public")
        assert payload["visibility"] == "public"

    def test_shared_with_users(self):
        payload: dict = {}
        apply_visibility(payload, "shared", "alice, bob")
        assert payload["visibility"] == "shared"
        assert payload["shared_with"] == ["alice", "bob"]

    def test_shared_empty_text_no_shared_with(self):
        payload: dict = {}
        apply_visibility(payload, "shared", "")
        assert payload["visibility"] == "shared"
        assert "shared_with" not in payload

    def test_shared_none_text_no_shared_with(self):
        payload: dict = {}
        apply_visibility(payload, "shared", None)
        assert payload["visibility"] == "shared"
        assert "shared_with" not in payload

    def test_shared_whitespace_only_no_shared_with(self):
        payload: dict = {}
        apply_visibility(payload, "shared", "  ,  ,  ")
        assert payload["visibility"] == "shared"
        assert "shared_with" not in payload
