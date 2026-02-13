"""Tests for _payload._table — table config and constants."""

from __future__ import annotations

from adapters.ui_gradio.builders._payload._table import (
    TABLE_MAX_CM,
    TABLE_MIN_CM,
    UNIT_LIMITS,
    apply_table_config,
)

# ── Constants ────────────────────────────────────────────────────────────────


class TestTableConstants:
    def test_table_min_cm(self):
        assert TABLE_MIN_CM == 60

    def test_table_max_cm(self):
        assert TABLE_MAX_CM == 300

    def test_unit_limits_keys(self):
        assert set(UNIT_LIMITS.keys()) == {"cm", "in", "ft"}

    def test_unit_limits_cm_range(self):
        assert UNIT_LIMITS["cm"]["min"] == TABLE_MIN_CM
        assert UNIT_LIMITS["cm"]["max"] == TABLE_MAX_CM


# ── apply_table_config ──────────────────────────────────────────────────────


class TestApplyTableConfig:
    def test_standard_preset(self):
        payload: dict = {}
        custom, err = apply_table_config(payload, "standard", 0, 0, "cm")
        assert custom is None
        assert err is None
        assert payload["table_preset"] == "standard"

    def test_massive_preset(self):
        payload: dict = {}
        custom, err = apply_table_config(payload, "massive", 0, 0, "cm")
        assert custom is None
        assert err is None
        assert payload["table_preset"] == "massive"

    def test_custom_valid_cm(self):
        payload: dict = {}
        custom, err = apply_table_config(payload, "custom", 120, 120, "cm")
        assert err is None
        assert custom == {"width_cm": 120, "height_cm": 120}
        assert payload["table_preset"] == "custom"
        assert payload["table_cm"] == custom

    def test_custom_valid_inches(self):
        payload: dict = {}
        custom, err = apply_table_config(payload, "custom", 48, 48, "inches")
        assert err is None
        assert custom is not None
        assert abs(custom["width_cm"] - 48 * 2.54) < 0.01

    def test_custom_out_of_range_returns_error(self):
        payload: dict = {}
        custom, err = apply_table_config(payload, "custom", 10, 10, "cm")
        assert custom is None
        assert err is not None
        assert err["status"] == "error"

    def test_custom_too_large_returns_error(self):
        payload: dict = {}
        custom, err = apply_table_config(payload, "custom", 500, 500, "cm")
        assert custom is None
        assert err is not None
        assert err["status"] == "error"
