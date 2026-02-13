"""Facade compatibility tests — ensure all public symbols are re-exported."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.builders import payload

_EXPECTED_SYMBOLS = [
    "build_generate_payload",
    "apply_table_config",
    "apply_optional_text_fields",
    "apply_special_rules",
    "apply_visibility",
    "validate_victory_points",
    "validate_required_fields",
    "TABLE_MIN_CM",
    "TABLE_MAX_CM",
    "UNIT_LIMITS",
]


class TestFacadeReExports:
    @pytest.mark.parametrize("symbol", _EXPECTED_SYMBOLS)
    def test_symbol_available(self, symbol):
        assert hasattr(payload, symbol), f"payload.{symbol} missing"

    @pytest.mark.parametrize("symbol", _EXPECTED_SYMBOLS)
    def test_symbol_callable_or_dict(self, symbol):
        attr = getattr(payload, symbol)
        assert callable(attr) or isinstance(attr, (dict, int, float))


class TestBuildGeneratePayload:
    def test_basic(self):
        result = payload.build_generate_payload("matched", 42)
        assert result == {"mode": "matched", "seed": 42}

    def test_no_seed(self):
        result = payload.build_generate_payload("narrative", None)
        assert result == {"mode": "narrative", "seed": None}
