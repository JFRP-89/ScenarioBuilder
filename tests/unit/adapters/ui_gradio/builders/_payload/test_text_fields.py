"""Tests for _payload._text_fields — optional text fields."""

from __future__ import annotations

from adapters.ui_gradio.builders._payload._text_fields import (
    apply_optional_text_fields,
)


class TestApplyOptionalTextFields:
    def test_adds_non_empty_fields(self):
        payload: dict = {}
        apply_optional_text_fields(
            payload,
            deployment="Deploy A",
            layout="Layout B",
            objectives="Obj C",
            initial_priority="Priority D",
            armies="Armies E",
            name="Name F",
        )
        assert payload["deployment"] == "Deploy A"
        assert payload["layout"] == "Layout B"
        assert payload["objectives"] == "Obj C"
        assert payload["initial_priority"] == "Priority D"
        assert payload["armies"] == "Armies E"
        assert payload["name"] == "Name F"

    def test_skips_none_fields(self):
        payload: dict = {}
        apply_optional_text_fields(payload, deployment=None)
        assert "deployment" not in payload

    def test_skips_empty_string_fields(self):
        payload: dict = {}
        apply_optional_text_fields(payload, deployment="", armies="  ")
        assert "deployment" not in payload
        assert "armies" not in payload

    def test_strips_whitespace(self):
        payload: dict = {}
        apply_optional_text_fields(payload, name="  My Name  ")
        assert payload["name"] == "My Name"

    def test_no_args_leaves_payload_empty(self):
        payload: dict = {}
        apply_optional_text_fields(payload)
        assert payload == {}
