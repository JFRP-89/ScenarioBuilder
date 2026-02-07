"""Unit tests for state_helpers deployment zone helpers."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.state_helpers import validate_separation_coords


class TestValidateSeparationCoords:
    """Tests for validate_separation_coords()."""

    @pytest.mark.parametrize(
        "border,sep_x,sep_y,expected",
        [
            ("north", 100, 50, (100, 50)),
            ("south", 100, 50, (100, 850)),
            ("west", 100, 50, (100, 50)),
            ("east", 100, 50, (700, 50)),
        ],
    )
    def test_applies_separation_for_each_border(self, border, sep_x, sep_y, expected):
        table_w = 1200
        table_h = 1200
        zone_w = 400
        zone_h = 300
        x, y = validate_separation_coords(
            border, zone_w, zone_h, sep_x, sep_y, table_w, table_h
        )
        assert (x, y) == expected

    def test_clamps_separation_within_table_bounds(self):
        table_w = 1200
        table_h = 1200
        zone_w = 400
        zone_h = 300
        # sep_x and sep_y exceed max_x/max_y
        x, y = validate_separation_coords(
            "north", zone_w, zone_h, 2000, 2000, table_w, table_h
        )
        assert x == table_w - zone_w
        assert y == table_h - zone_h

    def test_negative_separation_clamped_to_zero(self):
        table_w = 1200
        table_h = 1200
        zone_w = 400
        zone_h = 300
        x, y = validate_separation_coords(
            "south", zone_w, zone_h, -10, -20, table_w, table_h
        )
        assert x == 0
        # south uses max_y - clamped_y, so with clamped_y=0, y is max_y
        assert y == table_h - zone_h
