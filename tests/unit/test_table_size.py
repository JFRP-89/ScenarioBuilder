"""
RED tests for TableSize value object.

Wargame conversion factors:
- 1 in = 2.5 cm
- 1 ft = 30.0 cm (12 in)

Internal unit: mm (int)
Rounding: input cm with up to 2 decimals → round to 0.1 cm (HALF_UP) → convert to mm
Limits: min 60.0 cm (600 mm), max 300.0 cm (3000 mm)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

# TODO: Update import once TableSize is implemented
from domain.maps.table_size import TableSize


# =============================================================================
# 1) PRESETS - Equivalence between constructors
# =============================================================================
class TestPresets:
    """Standard and Massive presets must be equivalent across all constructors."""

    def test_standard_preset_returns_1200x1200_mm(self):
        ts = TableSize.standard()
        assert ts.width_mm == 1200
        assert ts.height_mm == 1200

    def test_massive_preset_returns_1800x1200_mm(self):
        ts = TableSize.massive()
        assert ts.width_mm == 1800
        assert ts.height_mm == 1200

    def test_standard_from_cm_equals_preset(self):
        preset = TableSize.standard()
        from_cm = TableSize.from_cm("120", "120")
        assert from_cm.width_mm == preset.width_mm
        assert from_cm.height_mm == preset.height_mm

    def test_standard_from_in_equals_preset(self):
        preset = TableSize.standard()
        from_in = TableSize.from_in("48", "48")
        assert from_in.width_mm == preset.width_mm
        assert from_in.height_mm == preset.height_mm

    def test_standard_from_ft_equals_preset(self):
        preset = TableSize.standard()
        from_ft = TableSize.from_ft("4", "4")
        assert from_ft.width_mm == preset.width_mm
        assert from_ft.height_mm == preset.height_mm

    def test_massive_from_cm_equals_preset(self):
        preset = TableSize.massive()
        from_cm = TableSize.from_cm("180", "120")
        assert from_cm.width_mm == preset.width_mm
        assert from_cm.height_mm == preset.height_mm

    def test_massive_from_in_equals_preset(self):
        preset = TableSize.massive()
        from_in = TableSize.from_in("72", "48")
        assert from_in.width_mm == preset.width_mm
        assert from_in.height_mm == preset.height_mm

    def test_massive_from_ft_equals_preset(self):
        preset = TableSize.massive()
        from_ft = TableSize.from_ft("6", "4")
        assert from_ft.width_mm == preset.width_mm
        assert from_ft.height_mm == preset.height_mm


# =============================================================================
# 2) ROUNDING in cm (HALF_UP to 0.1 cm)
# =============================================================================
class TestRoundingCm:
    """Rounding behavior: up to 2 decimals, HALF_UP to 0.1 cm."""

    @pytest.mark.parametrize(
        "width_cm,height_cm,expected_width_mm,expected_height_mm",
        [
            # 89.25 → 89.3 (HALF_UP), 76.35 → 76.4 (HALF_UP)
            ("89.25", "76.35", 893, 764),
            # 89.24 → 89.2 (round down), 76.34 → 76.3 (round down)
            ("89.24", "76.34", 892, 763),
            # Exact values (no rounding needed)
            ("100.0", "100.0", 1000, 1000),
            ("100.00", "100.00", 1000, 1000),
            # Edge cases for HALF_UP
            ("100.05", "100.05", 1001, 1001),  # .05 rounds up to .1
            ("100.04", "100.04", 1000, 1000),  # .04 rounds down to .0
        ],
    )
    def test_rounding_half_up_to_0_1_cm(
        self, width_cm, height_cm, expected_width_mm, expected_height_mm
    ):
        ts = TableSize.from_cm(width_cm, height_cm)
        assert ts.width_mm == expected_width_mm
        assert ts.height_mm == expected_height_mm

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            ("89.257", "76.35"),  # width has >2 decimals
            ("89.25", "76.357"),  # height has >2 decimals
            ("89.257", "76.357"),  # both have >2 decimals
            ("100.001", "100"),  # 3 decimals
        ],
    )
    def test_rejects_more_than_2_decimals_in_cm(self, invalid_width, invalid_height):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(invalid_width, invalid_height)


# =============================================================================
# 3) CONVERSION in inches (2.5 cm/in) + rounding
# =============================================================================
class TestConversionInches:
    """Conversion from inches: 1 in = 2.5 cm, then round to 0.1 cm."""

    @pytest.mark.parametrize(
        "width_in,height_in,expected_width_mm,expected_height_mm",
        [
            # Exact conversion: 24 in = 60 cm (minimum)
            ("24", "24", 600, 600),
            # Standard: 48 in = 120 cm
            ("48", "48", 1200, 1200),
            # Massive width: 72 in = 180 cm
            ("72", "48", 1800, 1200),
            # 24.01 in = 60.025 cm → round to 60.0 cm → 600 mm
            ("24.01", "24", 600, 600),
            # 24.06 in = 60.15 cm → round to 60.2 cm → 602 mm
            ("24.06", "24", 602, 600),
        ],
    )
    def test_conversion_from_inches_with_rounding(
        self, width_in, height_in, expected_width_mm, expected_height_mm
    ):
        ts = TableSize.from_in(width_in, height_in)
        assert ts.width_mm == expected_width_mm
        assert ts.height_mm == expected_height_mm

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            ("1.001", "1"),  # width has >2 decimals
            ("1", "1.001"),  # height has >2 decimals
            ("48.123", "48"),  # 3 decimals
        ],
    )
    def test_rejects_more_than_2_decimals_in_inches(
        self, invalid_width, invalid_height
    ):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_in(invalid_width, invalid_height)


# =============================================================================
# 4) CONVERSION in feet (30.0 cm/ft) + equivalences
# =============================================================================
class TestConversionFeet:
    """Conversion from feet: 1 ft = 30.0 cm = 12 in."""

    def test_2_ft_equals_24_in(self):
        """2 ft should equal 24 in (both are 60 cm = 600 mm, minimum)."""
        from_ft = TableSize.from_ft("2", "2")
        from_in = TableSize.from_in("24", "24")
        assert from_ft.width_mm == from_in.width_mm
        assert from_ft.height_mm == from_in.height_mm

    def test_2_ft_equals_60_cm(self):
        """2 ft = 60 cm = 600 mm (minimum valid size)."""
        ts = TableSize.from_ft("2", "2")
        assert ts.width_mm == 600
        assert ts.height_mm == 600

    @pytest.mark.parametrize(
        "width_ft,height_ft,expected_width_mm,expected_height_mm",
        [
            ("2", "2", 600, 600),  # Minimum: 60 cm
            ("4", "4", 1200, 1200),  # Standard
            ("6", "4", 1800, 1200),  # Massive
            ("10", "10", 3000, 3000),  # Maximum: 300 cm
        ],
    )
    def test_conversion_from_feet(
        self, width_ft, height_ft, expected_width_mm, expected_height_mm
    ):
        ts = TableSize.from_ft(width_ft, height_ft)
        assert ts.width_mm == expected_width_mm
        assert ts.height_mm == expected_height_mm

    def test_maximum_10x10_ft_is_allowed(self):
        """10×10 ft = 300×300 cm should be allowed (max limit)."""
        ts = TableSize.from_ft("10", "10")
        assert ts.width_mm == 3000
        assert ts.height_mm == 3000


# =============================================================================
# 5) LIMITS min/max (validation post-rounding)
# =============================================================================
class TestLimits:
    """Validation of min (60 cm = 600 mm) and max (300 cm = 3000 mm) limits."""

    # --- Minimum limit (60 cm = 600 mm) ---

    def test_accepts_exact_minimum_in_cm(self):
        ts = TableSize.from_cm("60.00", "60.00")
        assert ts.width_mm == 600
        assert ts.height_mm == 600

    def test_accepts_exact_minimum_in_inches(self):
        # 24 in = 60 cm
        ts = TableSize.from_in("24", "24")
        assert ts.width_mm == 600
        assert ts.height_mm == 600

    def test_accepts_exact_minimum_in_feet(self):
        # 2 ft = 60 cm
        ts = TableSize.from_ft("2", "2")
        assert ts.width_mm == 600
        assert ts.height_mm == 600

    @pytest.mark.parametrize(
        "width_cm,height_cm",
        [
            ("59.94", "60.00"),  # 59.94 → rounds to 59.9 cm (below min)
            ("60.00", "59.94"),  # height below min
            ("59.94", "59.94"),  # both below min
            ("59.00", "60.00"),  # clearly below
        ],
    )
    def test_rejects_below_minimum_post_rounding(self, width_cm, height_cm):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(width_cm, height_cm)

    # --- Maximum limit (300 cm = 3000 mm) ---

    def test_accepts_exact_maximum_in_cm(self):
        ts = TableSize.from_cm("300.00", "300.00")
        assert ts.width_mm == 3000
        assert ts.height_mm == 3000

    def test_accepts_exact_maximum_in_inches(self):
        # 120 in = 300 cm
        ts = TableSize.from_in("120", "120")
        assert ts.width_mm == 3000
        assert ts.height_mm == 3000

    def test_accepts_exact_maximum_in_feet(self):
        # 10 ft = 300 cm
        ts = TableSize.from_ft("10", "10")
        assert ts.width_mm == 3000
        assert ts.height_mm == 3000

    @pytest.mark.parametrize(
        "width_cm,height_cm",
        [
            ("300.06", "300.00"),  # 300.06 → rounds to 300.1 cm (above max)
            ("300.00", "300.06"),  # height above max
            ("300.06", "300.06"),  # both above max
            ("301.00", "300.00"),  # clearly above
        ],
    )
    def test_rejects_above_maximum_post_rounding(self, width_cm, height_cm):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(width_cm, height_cm)


# =============================================================================
# 6) PROPERTY ACCESSORS
# =============================================================================
class TestProperties:
    """Test property accessors (area_mm2, width_cm, height_cm)."""

    def test_area_mm2_property(self) -> None:
        """Test area calculation property (width_mm * height_mm)."""
        table = TableSize.from_cm("100", "80")
        expected_area = 1000 * 800  # mm²
        assert table.area_mm2 == expected_area

    def test_width_cm_property(self) -> None:
        """Test width_cm property returns Decimal."""
        table = TableSize.from_cm("100", "80")
        assert table.width_cm == Decimal("100.0")
        assert isinstance(table.width_cm, Decimal)

    def test_height_cm_property(self) -> None:
        """Test height_cm property returns Decimal."""
        table = TableSize.from_cm("100", "80")
        assert table.height_cm == Decimal("80.0")
        assert isinstance(table.height_cm, Decimal)


# =============================================================================
# 7) INVALID TYPES / INVALID INPUTS
# =============================================================================
class TestInvalidInputs:
    """Reject invalid types and malformed inputs."""

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            (None, "100"),  # None width
            ("100", None),  # None height
            (None, None),  # Both None
        ],
    )
    def test_rejects_none_values(self, invalid_width, invalid_height):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(invalid_width, invalid_height)

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            ("abc", "100"),  # Non-numeric width
            ("100", "xyz"),  # Non-numeric height
            ("abc", "xyz"),  # Both non-numeric
            ("12a", "100"),  # Mixed alphanumeric
            ("", "100"),  # Empty string width
            ("100", ""),  # Empty string height
            ("", ""),  # Both empty
        ],
    )
    def test_rejects_non_numeric_strings(self, invalid_width, invalid_height):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(invalid_width, invalid_height)

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            ("-100", "100"),  # Negative width
            ("100", "-100"),  # Negative height
            ("-100", "-100"),  # Both negative
            ("-0.01", "100"),  # Small negative
        ],
    )
    def test_rejects_negative_values(self, invalid_width, invalid_height):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(invalid_width, invalid_height)

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            ("0", "100"),  # Zero width
            ("100", "0"),  # Zero height
            ("0", "0"),  # Both zero
            ("0.00", "100"),  # Zero with decimals
        ],
    )
    def test_rejects_zero_values(self, invalid_width, invalid_height):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(invalid_width, invalid_height)

    @pytest.mark.parametrize(
        "invalid_width,invalid_height",
        [
            ("89,25", "100"),  # Comma decimal (European format) - width
            ("100", "76,35"),  # Comma decimal - height
            ("89,25", "76,35"),  # Both comma decimal
        ],
    )
    def test_rejects_comma_as_decimal_separator(self, invalid_width, invalid_height):
        """Domain requires dot as decimal separator, not comma."""
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_cm(invalid_width, invalid_height)

    def test_rejects_none_in_from_in(self):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_in(None, "48")

    def test_rejects_none_in_from_ft(self):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_ft(None, "4")

    def test_rejects_negative_in_from_in(self):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_in("-48", "48")

    def test_rejects_negative_height_in_from_in(self):
        """Test that negative height is rejected in from_in."""
        with pytest.raises(Exception):
            TableSize.from_in("48", "-48")

    def test_rejects_negative_in_from_ft(self):
        # TODO: Replace Exception with specific DomainError once implemented
        with pytest.raises(Exception):
            TableSize.from_ft("-4", "4")

    def test_rejects_negative_height_in_from_ft(self):
        """Test that negative height is rejected in from_ft."""
        with pytest.raises(Exception):
            TableSize.from_ft("4", "-4")

    def test_rejects_float_type(self):
        """Float type should be rejected for precision reasons."""
        with pytest.raises(Exception):
            TableSize.from_cm(100.5, "100")
        with pytest.raises(Exception):
            TableSize.from_cm("100", 100.5)

    def test_accepts_decimal_type_directly(self):
        """Decimal type should be accepted directly."""
        from decimal import Decimal

        ts = TableSize.from_cm(Decimal("120"), Decimal("120"))
        assert ts.width_mm == 1200
        assert ts.height_mm == 1200

    def test_accepts_int_type_directly(self):
        """Int type should be accepted directly."""
        ts = TableSize.from_cm(120, 120)
        assert ts.width_mm == 1200
        assert ts.height_mm == 1200

    def test_rejects_list_type(self):
        """List type should be rejected."""
        with pytest.raises(Exception):
            TableSize.from_cm([100], "100")

    def test_accepts_scientific_notation_lowercase_e(self):
        """Scientific notation with lowercase 'e' should work."""
        ts = TableSize.from_cm("1e2", "1.2e2")
        assert ts.width_mm == 1000
        assert ts.height_mm == 1200

    def test_rejects_decimal_with_exponent_less_than_minus_2(self):
        """Decimal with exponent < -2 should be rejected."""
        from decimal import Decimal

        # Decimal('100.001') has exponent -3
        with pytest.raises(Exception):
            TableSize.from_cm(Decimal("100.001"), "100")

    def test_rejects_below_minimum_in_from_in(self):
        """from_in should reject dimensions below minimum after conversion."""
        # 23.96 inches = 59.9 cm (below 60 cm minimum)
        with pytest.raises(Exception):
            TableSize.from_in("23.96", "24")
        with pytest.raises(Exception):
            TableSize.from_in("24", "23.96")

    def test_rejects_above_maximum_in_from_in(self):
        """from_in should reject dimensions above maximum after conversion."""
        # 120.03 inches = 300.1 cm (above 300 cm maximum)
        with pytest.raises(Exception):
            TableSize.from_in("120.03", "120")
        with pytest.raises(Exception):
            TableSize.from_in("120", "120.03")

    def test_rejects_below_minimum_in_from_ft(self):
        """from_ft should reject dimensions below minimum after conversion."""
        # 1.98 feet = 59.4 cm (below 60 cm minimum)
        with pytest.raises(Exception):
            TableSize.from_ft("1.98", "2")
        with pytest.raises(Exception):
            TableSize.from_ft("2", "1.98")

    def test_rejects_above_maximum_in_from_ft(self):
        """from_ft should reject dimensions above maximum after conversion."""
        # 10.01 feet = 300.3 cm (above 300 cm maximum)
        with pytest.raises(Exception):
            TableSize.from_ft("10.01", "10")
        with pytest.raises(Exception):
            TableSize.from_ft("10", "10.01")
