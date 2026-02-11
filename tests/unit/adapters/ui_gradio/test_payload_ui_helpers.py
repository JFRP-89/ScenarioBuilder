"""
Characterization tests for payload/UI helpers in Gradio UI adapter.

These tests freeze the current behavior of functions that build payloads and handle
UI interactions (preset changes, unit changes) to allow safe refactoring.
"""

from __future__ import annotations


class TestBuildGeneratePayload:
    """Characterization tests for _build_generate_payload()."""

    def test_builds_payload_with_mode_and_seed(self):
        """Builds payload with mode and seed."""
        from adapters.ui_gradio.builders.payload import build_generate_payload

        result = build_generate_payload("matched_play", 12345)
        assert result == {"mode": "matched_play", "seed": 12345}

    def test_seed_none_returns_none_in_payload(self):
        """seed=None returns seed: None in payload."""
        from adapters.ui_gradio.builders.payload import build_generate_payload

        result = build_generate_payload("matched_play", None)
        assert result == {"mode": "matched_play", "seed": None}

    def test_seed_zero_is_falsy_returns_none(self):
        """seed=0 is falsy, so returns None (current behavior)."""
        from adapters.ui_gradio.builders.payload import build_generate_payload

        result = build_generate_payload("competitive", 0)
        # Characterization: seed=0 is falsy, so `int(seed) if seed else None` → None
        assert result == {"mode": "competitive", "seed": None}


class TestApplyTableConfig:
    """Characterization tests for _apply_table_config()."""

    def test_custom_preset_valid_dimensions_adds_table_cm(self):
        """preset='custom' with valid dimensions adds table_cm to payload."""
        from adapters.ui_gradio.builders.payload import apply_table_config

        payload: dict[str, object] = {}
        custom_table, error = apply_table_config(payload, "custom", 120.0, 120.0, "cm")

        assert error is None
        assert custom_table == {"width_cm": 120.0, "height_cm": 120.0}
        assert payload["table_cm"] == {"width_cm": 120.0, "height_cm": 120.0}

    def test_custom_preset_invalid_dimensions_returns_error(self):
        """preset='custom' with invalid dimensions returns error."""
        from adapters.ui_gradio.builders.payload import apply_table_config

        payload: dict[str, object] = {}
        custom_table, error = apply_table_config(payload, "custom", 0.0, 120.0, "cm")

        assert custom_table is None
        assert error == {
            "status": "error",
            "message": "Invalid table dimensions. Check limits (60-300 cm).",
        }

    def test_standard_preset_adds_table_preset(self):
        """preset='standard' adds table_preset to payload."""
        from adapters.ui_gradio.builders.payload import apply_table_config

        payload: dict[str, object] = {}
        custom_table, error = apply_table_config(payload, "standard", 0.0, 0.0, "cm")

        assert error is None
        assert custom_table is None
        assert payload["table_preset"] == "standard"

    def test_massive_preset_adds_table_preset(self):
        """preset='massive' adds table_preset to payload."""
        from adapters.ui_gradio.builders.payload import apply_table_config

        payload: dict[str, object] = {}
        custom_table, error = apply_table_config(payload, "massive", 0.0, 0.0, "cm")

        assert error is None
        assert custom_table is None
        assert payload["table_preset"] == "massive"


class TestApplyOptionalTextFields:
    """Characterization tests for _apply_optional_text_fields()."""

    def test_adds_non_empty_fields_to_payload(self):
        """Non-empty fields are added to payload."""
        from adapters.ui_gradio.builders.payload import apply_optional_text_fields

        payload: dict[str, object] = {}
        apply_optional_text_fields(
            payload,
            armies="Warriors 500",
            deployment="North deployment",
            layout="Forest layout",
            objectives="Control center",
        )

        assert payload["armies"] == "Warriors 500"
        assert payload["deployment"] == "North deployment"
        assert payload["layout"] == "Forest layout"
        assert payload["objectives"] == "Control center"

    def test_strips_whitespace_from_fields(self):
        """Whitespace is stripped from field values."""
        from adapters.ui_gradio.builders.payload import apply_optional_text_fields

        payload: dict[str, object] = {}
        apply_optional_text_fields(
            payload,
            armies="  Warriors  ",
            deployment="  Deploy  ",
            layout="  Layout  ",
            objectives="  Objectives  ",
        )

        assert payload["armies"] == "Warriors"
        assert payload["deployment"] == "Deploy"
        assert payload["layout"] == "Layout"
        assert payload["objectives"] == "Objectives"

    def test_empty_fields_not_added_to_payload(self):
        """Empty or whitespace-only fields are not added."""
        from adapters.ui_gradio.builders.payload import apply_optional_text_fields

        payload: dict[str, object] = {}
        apply_optional_text_fields(
            payload, armies="", deployment="   ", layout="layout", objectives=""
        )

        assert "armies" not in payload
        assert "deployment" not in payload
        assert "objectives" not in payload
        assert payload["layout"] == "layout"

    def test_does_not_mutate_payload_if_all_empty(self):
        """If all fields empty, payload keys remain unchanged."""
        from adapters.ui_gradio.builders.payload import apply_optional_text_fields

        payload = {"existing": "value"}
        apply_optional_text_fields(
            payload, armies="", deployment="", layout="", objectives=""
        )

        assert payload == {"existing": "value"}


class TestOnTablePresetChange:
    """Characterization tests for _on_table_preset_change()."""

    def test_custom_preset_returns_visible_and_default_values(self):
        """preset='custom' returns visibility=True and default 120x120."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("custom", "cm")

        # visibility is a dict (gr.update returns dict)
        assert visibility["visible"] is True
        assert width == 120.0
        assert height == 120.0

    def test_standard_preset_returns_120x120_in_cm(self):
        """preset='standard' returns 120x120 cm."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("standard", "cm")

        assert visibility["visible"] is False
        assert width == 120.0
        assert height == 120.0

    def test_standard_preset_returns_48x48_in_inches(self):
        """preset='standard' returns 48x48 inches (120cm / 2.5)."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("standard", "in")

        assert visibility["visible"] is False
        assert width == 48.0
        assert height == 48.0

    def test_standard_preset_returns_4x4_in_feet(self):
        """preset='standard' returns 4x4 feet (120cm / 30)."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("standard", "ft")

        assert visibility["visible"] is False
        assert width == 4.0
        assert height == 4.0

    def test_massive_preset_returns_180x120_in_cm(self):
        """preset='massive' returns 180x120 cm."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("massive", "cm")

        assert visibility["visible"] is False
        assert width == 180.0
        assert height == 120.0

    def test_massive_preset_converts_to_inches(self):
        """preset='massive' converts 180x120 cm to inches."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("massive", "in")

        assert visibility["visible"] is False
        assert width == 72.0  # 180 / 2.5
        assert height == 48.0  # 120 / 2.5

    def test_massive_preset_converts_to_feet(self):
        """preset='massive' converts 180x120 cm to feet."""
        from adapters.ui_gradio.compat import _on_table_preset_change

        visibility, width, height = _on_table_preset_change("massive", "ft")

        assert visibility["visible"] is False
        assert width == 6.0  # 180 / 30
        assert height == 4.0  # 120 / 30


class TestOnTableUnitChange:
    """Characterization tests for _on_table_unit_change()."""

    def test_same_unit_returns_unchanged(self):
        """Changing to same unit returns values unchanged."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        new_width, new_height, new_prev = _on_table_unit_change(
            "cm", 120.0, 120.0, "cm"
        )

        assert new_width == 120.0
        assert new_height == 120.0
        assert new_prev == "cm"

    def test_converts_cm_to_inches(self):
        """Converts cm → inches."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        new_width, new_height, new_prev = _on_table_unit_change(
            "in", 120.0, 120.0, "cm"
        )

        assert new_width == 48.0  # 120 / 2.5
        assert new_height == 48.0
        assert new_prev == "in"

    def test_converts_cm_to_feet(self):
        """Converts cm → feet."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        new_width, new_height, new_prev = _on_table_unit_change(
            "ft", 120.0, 120.0, "cm"
        )

        assert new_width == 4.0  # 120 / 30
        assert new_height == 4.0
        assert new_prev == "ft"

    def test_converts_inches_to_cm(self):
        """Converts inches → cm."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        new_width, new_height, new_prev = _on_table_unit_change("cm", 48.0, 48.0, "in")

        assert new_width == 120.0  # 48 * 2.5
        assert new_height == 120.0
        assert new_prev == "cm"

    def test_converts_feet_to_cm(self):
        """Converts feet → cm."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        new_width, new_height, new_prev = _on_table_unit_change("cm", 4.0, 4.0, "ft")

        assert new_width == 120.0  # 4 * 30
        assert new_height == 120.0
        assert new_prev == "cm"

    def test_clamps_to_min_limit_for_new_unit(self):
        """Values below min limit for new unit are clamped."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        # 1 cm is way below min (60 cm), converting to inches (min 24 in)
        # 1 cm = 0.4 in, should clamp to 24 in
        new_width, new_height, new_prev = _on_table_unit_change("in", 1.0, 1.0, "cm")

        assert new_width == 24.0  # min for inches
        assert new_height == 24.0
        assert new_prev == "in"

    def test_clamps_to_max_limit_for_new_unit(self):
        """Values above max limit for new unit are clamped."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        # 400 cm > max (300 cm), converting to inches (max 120 in)
        # 400 cm = 160 in, should clamp to 120 in
        new_width, new_height, new_prev = _on_table_unit_change(
            "in", 400.0, 400.0, "cm"
        )

        assert new_width == 120.0  # max for inches
        assert new_height == 120.0
        assert new_prev == "in"

    def test_returns_unchanged_if_width_or_height_falsy(self):
        """If width or height is 0/None, returns unchanged."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        new_width, new_height, new_prev = _on_table_unit_change("in", 0.0, 120.0, "cm")

        assert new_width == 0.0
        assert new_height == 120.0
        assert new_prev == "in"

    def test_rounds_to_2_decimals(self):
        """Result is rounded to 2 decimal places."""
        from adapters.ui_gradio.compat import _on_table_unit_change

        # 100 cm → feet: 100/30 = 3.333... → 3.33
        new_width, new_height, new_prev = _on_table_unit_change(
            "ft", 100.0, 100.0, "cm"
        )

        assert new_width == 3.33
        assert new_height == 3.33
        assert new_prev == "ft"
