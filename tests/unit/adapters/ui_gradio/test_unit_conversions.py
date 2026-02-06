"""
Characterization tests for unit conversion helpers in Gradio UI adapter.

These tests freeze the current behavior of pure functions for unit conversion
to allow safe refactoring later.
"""

from __future__ import annotations


class TestConvertToCm:
    """Characterization tests for _convert_to_cm()."""

    def test_converts_cm_returns_unchanged(self):
        """cm → cm returns same value."""
        from adapters.ui_gradio.compat import _convert_to_cm

        assert _convert_to_cm(120.0, "cm") == 120.0
        assert _convert_to_cm(60.5, "cm") == 60.5

    def test_converts_inches_to_cm(self):
        """in → cm uses factor 2.5."""
        from adapters.ui_gradio.compat import _convert_to_cm

        # 1 inch = 2.5 cm
        assert _convert_to_cm(1.0, "in") == 2.5
        assert _convert_to_cm(48.0, "in") == 120.0

    def test_converts_feet_to_cm(self):
        """ft → cm uses factor 30.0."""
        from adapters.ui_gradio.compat import _convert_to_cm

        # 1 foot = 30 cm
        assert _convert_to_cm(1.0, "ft") == 30.0
        assert _convert_to_cm(4.0, "ft") == 120.0


class TestConvertFromCm:
    """Characterization tests for _convert_from_cm()."""

    def test_converts_cm_to_cm_unchanged(self):
        """cm → cm returns same value."""
        from adapters.ui_gradio.compat import _convert_from_cm

        assert _convert_from_cm(120.0, "cm") == 120.0

    def test_converts_cm_to_inches(self):
        """cm → in divides by 2.5."""
        from adapters.ui_gradio.compat import _convert_from_cm

        assert _convert_from_cm(2.5, "in") == 1.0
        assert _convert_from_cm(120.0, "in") == 48.0

    def test_converts_cm_to_feet(self):
        """cm → ft divides by 30.0."""
        from adapters.ui_gradio.compat import _convert_from_cm

        assert _convert_from_cm(30.0, "ft") == 1.0
        assert _convert_from_cm(120.0, "ft") == 4.0


class TestConvertUnitToUnit:
    """Characterization tests for _convert_unit_to_unit()."""

    def test_same_unit_returns_unchanged(self):
        """Converting from unit to itself returns same value."""
        from adapters.ui_gradio.compat import _convert_unit_to_unit

        assert _convert_unit_to_unit(120.0, "cm", "cm") == 120.0
        assert _convert_unit_to_unit(48.0, "in", "in") == 48.0
        assert _convert_unit_to_unit(4.0, "ft", "ft") == 4.0

    def test_converts_cm_to_inches(self):
        """cm → in conversion."""
        from adapters.ui_gradio.compat import _convert_unit_to_unit

        assert _convert_unit_to_unit(120.0, "cm", "in") == 48.0
        assert _convert_unit_to_unit(2.5, "cm", "in") == 1.0

    def test_converts_cm_to_feet(self):
        """cm → ft conversion."""
        from adapters.ui_gradio.compat import _convert_unit_to_unit

        assert _convert_unit_to_unit(120.0, "cm", "ft") == 4.0
        assert _convert_unit_to_unit(30.0, "cm", "ft") == 1.0

    def test_converts_inches_to_cm(self):
        """in → cm conversion."""
        from adapters.ui_gradio.compat import _convert_unit_to_unit

        assert _convert_unit_to_unit(48.0, "in", "cm") == 120.0

    def test_converts_feet_to_cm(self):
        """ft → cm conversion."""
        from adapters.ui_gradio.compat import _convert_unit_to_unit

        assert _convert_unit_to_unit(4.0, "ft", "cm") == 120.0

    def test_rounds_to_2_decimals(self):
        """Result is rounded to 2 decimal places."""
        from adapters.ui_gradio.compat import _convert_unit_to_unit

        # 100 cm / 2.5 = 40.0 inches
        assert _convert_unit_to_unit(100.0, "cm", "in") == 40.0

        # 100 cm / 30.0 = 3.33... feet → 3.33
        assert _convert_unit_to_unit(100.0, "cm", "ft") == 3.33


class TestBuildCustomTablePayload:
    """Characterization tests for _build_custom_table_payload()."""

    def test_valid_dimensions_returns_dict_with_cm(self):
        """Valid dimensions return dict with width_cm and height_cm."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        result = _build_custom_table_payload(120.0, 120.0, "cm")
        assert result == {"width_cm": 120.0, "height_cm": 120.0}

    def test_converts_inches_to_cm(self):
        """Dimensions in inches are converted to cm."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        result = _build_custom_table_payload(48.0, 48.0, "in")
        # 48 in * 2.5 = 120 cm
        assert result == {"width_cm": 120.0, "height_cm": 120.0}

    def test_converts_feet_to_cm(self):
        """Dimensions in feet are converted to cm."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        result = _build_custom_table_payload(4.0, 4.0, "ft")
        # 4 ft * 30 = 120 cm
        assert result == {"width_cm": 120.0, "height_cm": 120.0}

    def test_zero_width_returns_none(self):
        """Width <= 0 returns None."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        assert _build_custom_table_payload(0.0, 120.0, "cm") is None
        assert _build_custom_table_payload(-10.0, 120.0, "cm") is None

    def test_zero_height_returns_none(self):
        """Height <= 0 returns None."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        assert _build_custom_table_payload(120.0, 0.0, "cm") is None
        assert _build_custom_table_payload(120.0, -10.0, "cm") is None

    def test_below_min_limit_returns_none(self):
        """Dimensions below 60cm return None."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        # 59 cm < 60 cm minimum
        assert _build_custom_table_payload(59.0, 120.0, "cm") is None
        assert _build_custom_table_payload(120.0, 59.0, "cm") is None

    def test_above_max_limit_returns_none(self):
        """Dimensions above 300cm return None."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        # 301 cm > 300 cm maximum
        assert _build_custom_table_payload(301.0, 120.0, "cm") is None
        assert _build_custom_table_payload(120.0, 301.0, "cm") is None

    def test_exactly_at_limits_is_valid(self):
        """Dimensions exactly at 60cm and 300cm are valid."""
        from adapters.ui_gradio.compat import _build_custom_table_payload

        result_min = _build_custom_table_payload(60.0, 60.0, "cm")
        assert result_min == {"width_cm": 60.0, "height_cm": 60.0}

        result_max = _build_custom_table_payload(300.0, 300.0, "cm")
        assert result_max == {"width_cm": 300.0, "height_cm": 300.0}
