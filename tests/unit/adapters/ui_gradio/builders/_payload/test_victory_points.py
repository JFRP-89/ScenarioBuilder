"""Tests for _payload._victory_points — VP validation."""

from __future__ import annotations

from adapters.ui_gradio.builders._payload._victory_points import (
    validate_victory_points,
)


class TestValidateVictoryPoints:
    def test_empty_returns_empty_list(self):
        result, err = validate_victory_points([])
        assert result == []
        assert err is None

    def test_valid_vps(self):
        vps = [{"description": "Hold point A"}, {"description": "Capture flag"}]
        result, err = validate_victory_points(vps)
        assert err is None
        assert result == ["Hold point A", "Capture flag"]

    def test_empty_description_returns_error(self):
        vps = [{"description": "OK"}, {"description": ""}]
        result, err = validate_victory_points(vps)
        assert result is None
        assert err is not None
        assert "Victory Point 2" in err

    def test_missing_description_key_returns_error(self):
        vps = [{}]
        result, err = validate_victory_points(vps)
        assert result is None
        assert "Victory Point 1" in err

    def test_strips_whitespace(self):
        vps = [{"description": "  trimmed  "}]
        result, err = validate_victory_points(vps)
        assert result == ["trimmed"]
        assert err is None
