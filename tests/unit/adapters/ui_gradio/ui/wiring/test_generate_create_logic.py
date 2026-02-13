"""Tests for _generate._create_logic — pure validation."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._generate._create_logic import validate_preview_data


# ── Valid ─────────────────────────────────────────────────────────────
class TestValidatePreviewDataValid:
    """Cases that should pass validation."""

    def test_valid_preview(self) -> None:
        data = {"status": "preview", "name": "Battle"}
        ok, msg = validate_preview_data(data)
        assert ok is True
        assert msg == ""

    def test_valid_preview_with_extra_fields(self) -> None:
        data = {"status": "preview", "name": "Battle", "seed": 42}
        ok, msg = validate_preview_data(data)
        assert ok is True
        assert msg == ""


# ── Invalid: empty / wrong type ──────────────────────────────────────
class TestValidatePreviewDataEmpty:
    """Cases where preview_data is missing or wrong type."""

    @pytest.mark.parametrize("bad_input", [None, "", 0, False, []])
    def test_falsy_values(self, bad_input: object) -> None:
        ok, msg = validate_preview_data(bad_input)
        assert ok is False
        assert msg == "Generate a card preview first."

    def test_non_dict(self) -> None:
        ok, msg = validate_preview_data("not a dict")
        assert ok is False
        assert msg == "Generate a card preview first."

    def test_list_input(self) -> None:
        ok, msg = validate_preview_data([1, 2, 3])
        assert ok is False
        assert msg == "Generate a card preview first."


# ── Invalid: error status ────────────────────────────────────────────
class TestValidatePreviewDataError:
    """Cases where preview_data indicates an error."""

    def test_error_with_message(self) -> None:
        data = {"status": "error", "message": "Invalid seed"}
        ok, msg = validate_preview_data(data)
        assert ok is False
        assert msg == "Error: Invalid seed"

    def test_error_without_message(self) -> None:
        data = {"status": "error"}
        ok, msg = validate_preview_data(data)
        assert ok is False
        assert msg == "Error: Generation failed"


# ── Invalid: wrong status ────────────────────────────────────────────
class TestValidatePreviewDataWrongStatus:
    """Cases where status is not 'preview'."""

    @pytest.mark.parametrize("status", ["created", "saved", "draft", ""])
    def test_unexpected_status(self, status: str) -> None:
        data = {"status": status}
        ok, msg = validate_preview_data(data)
        assert ok is False
        assert msg == "Generate a card preview first."

    def test_missing_status_key(self) -> None:
        data = {"name": "Battle"}
        ok, msg = validate_preview_data(data)
        assert ok is False
        assert msg == "Generate a card preview first."
