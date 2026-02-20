"""Unit tests for scenography shape limits in domain validation."""

from __future__ import annotations

import pytest
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.map_spec_shape_validation import (
    _MAX_SCENOGRAPHY_PASSABLE,
    _MAX_SCENOGRAPHY_SHAPES,
    _MAX_SCENOGRAPHY_SOLID,
    validate_scenography_shapes,
)
from domain.maps.table_size import TableSize


def _circle(
    cx: int = 100, cy: int = 100, r: int = 20, *, allow_overlap: bool = False
) -> dict:
    return {
        "type": "circle",
        "cx": cx,
        "cy": cy,
        "r": r,
        "allow_overlap": allow_overlap,
    }


# ── validate_scenography_shapes (standalone) ─────────────────────────────────


class TestValidateScenographyShapes:
    """Tests for the scenography limit validation function."""

    def test_empty_list_ok(self):
        validate_scenography_shapes([])

    def test_one_solid_ok(self):
        validate_scenography_shapes([_circle(allow_overlap=False)])

    def test_one_passable_ok(self):
        validate_scenography_shapes([_circle(allow_overlap=True)])

    def test_max_balanced_ok(self):
        """3 solid + 3 passable = 6 total → valid."""
        shapes = [
            _circle(cx=100, allow_overlap=False),
            _circle(cx=200, allow_overlap=False),
            _circle(cx=300, allow_overlap=False),
            _circle(cx=400, allow_overlap=True),
            _circle(cx=500, allow_overlap=True),
            _circle(cx=600, allow_overlap=True),
        ]
        validate_scenography_shapes(shapes)

    def test_fewer_than_max_ok(self):
        """2 solid + 1 passable = 3 total → valid."""
        shapes = [
            _circle(cx=100, allow_overlap=False),
            _circle(cx=200, allow_overlap=False),
            _circle(cx=400, allow_overlap=True),
        ]
        validate_scenography_shapes(shapes)

    def test_too_many_total_raises(self):
        """7 shapes (4 solid + 3 passable) exceeds max 6."""
        shapes = [_circle(cx=100 * i, allow_overlap=(i > 4)) for i in range(1, 8)]
        with pytest.raises(ValidationError, match="too many scenography"):
            validate_scenography_shapes(shapes)

    def test_too_many_solid_raises(self):
        """4 solid + 0 passable → exceeds max 3 solid."""
        shapes = [_circle(cx=100 * i, allow_overlap=False) for i in range(1, 5)]
        with pytest.raises(ValidationError, match="solid"):
            validate_scenography_shapes(shapes)

    def test_too_many_passable_raises(self):
        """0 solid + 4 passable → exceeds max 3 passable."""
        shapes = [_circle(cx=100 * i, allow_overlap=True) for i in range(1, 5)]
        with pytest.raises(ValidationError, match="passable"):
            validate_scenography_shapes(shapes)

    def test_exactly_three_solid_ok(self):
        shapes = [_circle(cx=100 * i, allow_overlap=False) for i in range(1, 4)]
        validate_scenography_shapes(shapes)

    def test_exactly_three_passable_ok(self):
        shapes = [_circle(cx=100 * i, allow_overlap=True) for i in range(1, 4)]
        validate_scenography_shapes(shapes)

    def test_default_allow_overlap_is_false(self):
        """Shapes without allow_overlap key default to solid (False)."""
        shapes = [
            {"type": "circle", "cx": 100 * i, "cy": 100, "r": 20} for i in range(1, 4)
        ]
        validate_scenography_shapes(shapes)  # 3 solid → ok

    def test_default_allow_overlap_exceeds_solid(self):
        """4 shapes without allow_overlap → 4 solid → exceeds."""
        shapes = [
            {"type": "circle", "cx": 100 * i, "cy": 100, "r": 20} for i in range(1, 5)
        ]
        with pytest.raises(ValidationError, match="solid"):
            validate_scenography_shapes(shapes)

    def test_constants_match_expected_values(self):
        assert _MAX_SCENOGRAPHY_SHAPES == 6
        assert _MAX_SCENOGRAPHY_SOLID == 3
        assert _MAX_SCENOGRAPHY_PASSABLE == 3


# ── MapSpec integration ──────────────────────────────────────────────────────


class TestMapSpecScenographyLimits:
    """Tests that MapSpec validates scenography limits in __post_init__."""

    TABLE = TableSize.from_cm(120, 120)

    def _make_spec(self, shapes: list[dict]) -> MapSpec:
        return MapSpec(table=self.TABLE, shapes=shapes)

    def test_six_balanced_shapes_ok(self):
        shapes = [
            _circle(cx=100 + 150 * i, cy=100, allow_overlap=False) for i in range(3)
        ] + [_circle(cx=100 + 150 * i, cy=300, allow_overlap=True) for i in range(3)]
        spec = self._make_spec(shapes)
        assert len(spec.shapes) == 6

    def test_seven_shapes_raises(self):
        # 4 solid + 3 passable = 7 total
        shapes = [
            _circle(cx=100 + 150 * i, cy=100, allow_overlap=False) for i in range(4)
        ] + [_circle(cx=100 + 150 * i, cy=300, allow_overlap=True) for i in range(3)]
        with pytest.raises(ValidationError, match="too many scenography"):
            self._make_spec(shapes)

    def test_four_solid_raises(self):
        shapes = [
            _circle(cx=100 + 150 * i, cy=100, allow_overlap=False) for i in range(4)
        ]
        with pytest.raises(ValidationError, match="solid"):
            self._make_spec(shapes)

    def test_four_passable_raises(self):
        shapes = [
            _circle(cx=100 + 150 * i, cy=100, allow_overlap=True) for i in range(4)
        ]
        with pytest.raises(ValidationError, match="passable"):
            self._make_spec(shapes)

    def test_zero_shapes_ok(self):
        spec = self._make_spec([])
        assert spec.shapes == []
