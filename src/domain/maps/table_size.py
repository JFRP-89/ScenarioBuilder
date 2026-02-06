"""TableSize value object for wargame table dimensions.

Wargame conversion factors:
- 1 in = 2.5 cm
- 1 ft = 30.0 cm (12 in)

Internal unit: mm (int)
Rounding: input with up to 2 decimals → round to 0.1 cm (HALF_UP) → convert to mm
Limits: min 60.0 cm (600 mm), max 300.0 cm (3000 mm) per axis
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Union

from domain.errors import ValidationError

# Conversion factors (as Decimal for precision)
CM_PER_INCH = Decimal("2.5")
CM_PER_FOOT = Decimal("30.0")

# Limits in mm
MIN_MM = 600  # 60.0 cm
MAX_MM = 3000  # 300.0 cm

# Rounding quantum
QUANTUM = Decimal("0.1")


def _to_decimal(value: Union[str, int, Decimal], field_name: str) -> Decimal:
    """Convert input to Decimal, rejecting invalid types."""
    if value is None:
        raise ValidationError(f"{field_name} cannot be None")

    if isinstance(value, float):
        raise ValidationError(
            f"{field_name} cannot be float (use str or Decimal for precision)"
        )

    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, str):
        if value == "":
            raise ValidationError(f"{field_name} cannot be empty string")

        # Reject comma as decimal separator
        if "," in value:
            raise ValidationError(
                f"{field_name} must use dot as decimal separator, not comma"
            )

        try:
            return Decimal(value)
        except InvalidOperation as e:
            raise ValidationError(f"{field_name} is not a valid number: {value}") from e

    raise ValidationError(f"{field_name} has invalid type: {type(value).__name__}")


def _count_decimals(value: str) -> int:
    """Count decimal places in a string representation."""
    if "." not in value:
        return 0
    # Handle scientific notation edge case
    if "e" in value.lower():
        return 0  # Let Decimal handle it
    return len(value.split(".")[1])


def _ensure_max_two_decimals(
    decimal_value: Decimal, original: Union[str, int, Decimal], field_name: str
) -> None:
    """Ensure input has at most 2 decimal places."""
    if isinstance(original, str):
        # For strings, count actual decimal places
        if _count_decimals(original) > 2:
            raise ValidationError(
                f"{field_name} cannot have more than 2 decimal places: {original}"
            )
    elif isinstance(original, Decimal):
        # For Decimal, check exponent
        _, _, exponent = decimal_value.as_tuple()
        if isinstance(exponent, int) and exponent < -2:
            raise ValidationError(
                f"{field_name} cannot have more than 2 decimal places"
            )
    # int always has 0 decimals, so it's fine


def _parse_and_round_to_mm(value: Union[str, int, Decimal], field_name: str) -> int:
    """Parse input, validate decimals, round to 0.1 cm, convert to mm."""
    decimal_value = _to_decimal(value, field_name)

    # Check for max 2 decimals
    _ensure_max_two_decimals(decimal_value, value, field_name)

    # Check for negative or zero
    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be positive, got: {decimal_value}")

    # Round to 0.1 cm using HALF_UP
    rounded_cm = decimal_value.quantize(QUANTUM, rounding=ROUND_HALF_UP)

    # Convert to mm (0.1 cm = 1 mm, so multiply by 10)
    mm = int(rounded_cm * 10)

    return mm


def _validate_limits(width_mm: int, height_mm: int) -> None:
    """Validate that dimensions are within allowed limits."""
    if width_mm < MIN_MM:
        raise ValidationError(
            f"width must be at least {MIN_MM / 10} cm ({MIN_MM} mm), "
            f"got {width_mm / 10} cm ({width_mm} mm)"
        )
    if width_mm > MAX_MM:
        raise ValidationError(
            f"width must be at most {MAX_MM / 10} cm ({MAX_MM} mm), "
            f"got {width_mm / 10} cm ({width_mm} mm)"
        )
    if height_mm < MIN_MM:
        raise ValidationError(
            f"height must be at least {MIN_MM / 10} cm ({MIN_MM} mm), "
            f"got {height_mm / 10} cm ({height_mm} mm)"
        )
    if height_mm > MAX_MM:
        raise ValidationError(
            f"height must be at most {MAX_MM / 10} cm ({MAX_MM} mm), "
            f"got {height_mm / 10} cm ({height_mm} mm)"
        )


@dataclass(frozen=True)
class TableSize:
    """Immutable value object representing wargame table dimensions.

    Internal unit is millimeters (int) for precision.
    """

    width_mm: int
    height_mm: int

    def __post_init__(self) -> None:
        """Validate dimensions after initialization."""
        _validate_limits(self.width_mm, self.height_mm)

    @property
    def area_mm2(self) -> int:
        """Calculate area in square millimeters."""
        return self.width_mm * self.height_mm

    @property
    def width_cm(self) -> Decimal:
        """Width in centimeters."""
        return Decimal(self.width_mm) / 10

    @property
    def height_cm(self) -> Decimal:
        """Height in centimeters."""
        return Decimal(self.height_mm) / 10

    @classmethod
    def from_cm(
        cls, width: Union[str, int, Decimal], height: Union[str, int, Decimal]
    ) -> "TableSize":
        """Create TableSize from centimeter values.

        Args:
            width: Width in cm (str, int, or Decimal). Max 2 decimal places.
            height: Height in cm (str, int, or Decimal). Max 2 decimal places.

        Returns:
            TableSize with dimensions in mm.

        Raises:
            ValidationError: If input is invalid or out of bounds.
        """
        width_mm = _parse_and_round_to_mm(width, "width")
        height_mm = _parse_and_round_to_mm(height, "height")
        return cls(width_mm=width_mm, height_mm=height_mm)

    @classmethod
    def from_in(
        cls, width: Union[str, int, Decimal], height: Union[str, int, Decimal]
    ) -> "TableSize":
        """Create TableSize from inch values.

        Conversion: 1 in = 2.5 cm

        Args:
            width: Width in inches (str, int, or Decimal). Max 2 decimal places.
            height: Height in inches (str, int, or Decimal). Max 2 decimal places.

        Returns:
            TableSize with dimensions in mm.

        Raises:
            ValidationError: If input is invalid or out of bounds.
        """
        width_dec = _to_decimal(width, "width")
        height_dec = _to_decimal(height, "height")

        # Check max 2 decimals on original input
        _ensure_max_two_decimals(width_dec, width, "width")
        _ensure_max_two_decimals(height_dec, height, "height")

        # Check for negative or zero
        if width_dec <= 0:
            raise ValidationError(f"width must be positive, got: {width_dec}")
        if height_dec <= 0:
            raise ValidationError(f"height must be positive, got: {height_dec}")

        # Convert inches to cm
        width_cm = width_dec * CM_PER_INCH
        height_cm = height_dec * CM_PER_INCH

        # Round to 0.1 cm and convert to mm
        width_mm = int(width_cm.quantize(QUANTUM, rounding=ROUND_HALF_UP) * 10)
        height_mm = int(height_cm.quantize(QUANTUM, rounding=ROUND_HALF_UP) * 10)

        return cls(width_mm=width_mm, height_mm=height_mm)

    @classmethod
    def from_ft(
        cls, width: Union[str, int, Decimal], height: Union[str, int, Decimal]
    ) -> "TableSize":
        """Create TableSize from feet values.

        Conversion: 1 ft = 30.0 cm (= 12 in)

        Args:
            width: Width in feet (str, int, or Decimal). Max 2 decimal places.
            height: Height in feet (str, int, or Decimal). Max 2 decimal places.

        Returns:
            TableSize with dimensions in mm.

        Raises:
            ValidationError: If input is invalid or out of bounds.
        """
        width_dec = _to_decimal(width, "width")
        height_dec = _to_decimal(height, "height")

        # Check max 2 decimals on original input
        _ensure_max_two_decimals(width_dec, width, "width")
        _ensure_max_two_decimals(height_dec, height, "height")

        # Check for negative or zero
        if width_dec <= 0:
            raise ValidationError(f"width must be positive, got: {width_dec}")
        if height_dec <= 0:
            raise ValidationError(f"height must be positive, got: {height_dec}")

        # Convert feet to cm
        width_cm = width_dec * CM_PER_FOOT
        height_cm = height_dec * CM_PER_FOOT

        # Round to 0.1 cm and convert to mm
        width_mm = int(width_cm.quantize(QUANTUM, rounding=ROUND_HALF_UP) * 10)
        height_mm = int(height_cm.quantize(QUANTUM, rounding=ROUND_HALF_UP) * 10)

        return cls(width_mm=width_mm, height_mm=height_mm)

    @classmethod
    def standard(cls) -> "TableSize":
        """Create standard 4x4 ft table (120x120 cm = 48x48 in)."""
        return cls(width_mm=1200, height_mm=1200)

    @classmethod
    def massive(cls) -> "TableSize":
        """Create massive 6x4 ft table (180x120 cm = 72x48 in)."""
        return cls(width_mm=1800, height_mm=1200)
