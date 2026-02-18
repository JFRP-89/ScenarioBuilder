"""Tests for ``adapters.ui_gradio.ui.wiring._kwargs.kwargs_for_call``."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._kwargs import KwargsContractError, kwargs_for_call

# ─── Dummy target functions ────────────────────────────────────────────


def _fn_no_varkw(*, a: int, b: str, c: float, page_state: object = None) -> None:
    """Keyword-only, NO **kwargs."""


def _fn_with_varkw(
    *, a: int, b: str, page_state: object = None, **_extra: object
) -> None:
    """Keyword-only WITH **kwargs."""


def _fn_all_required(*, x: int, y: int) -> None:
    """All params required, no defaults."""


# ─── Happy path ────────────────────────────────────────────────────────


class TestFiltersExtrasAndReturnsRequired:
    """When fn has no **kwargs, extra keys should be silently dropped."""

    def test_filters_extras(self):
        payload = {"a": 1, "b": "hi", "c": 3.0, "extra_key": "dropped"}
        result = kwargs_for_call(payload, _fn_no_varkw)
        assert result == {"a": 1, "b": "hi", "c": 3.0}

    def test_keeps_param_with_default_if_present(self):
        payload = {"a": 1, "b": "hi", "c": 3.0, "page_state": "ps"}
        result = kwargs_for_call(payload, _fn_no_varkw)
        assert result["page_state"] == "ps"


class TestVarKwPassesEverything:
    """When fn accepts **kwargs, all non-override keys pass through."""

    def test_passes_extras(self):
        payload = {"a": 1, "b": "hi", "extra_key": "kept"}
        result = kwargs_for_call(payload, _fn_with_varkw)
        assert result == {"a": 1, "b": "hi", "extra_key": "kept"}


# ─── Override conflict ─────────────────────────────────────────────────


class TestOverrideConflict:
    """Payload must never contain a key listed in explicit_overrides."""

    def test_raises_on_conflict_no_varkw(self):
        payload = {"a": 1, "b": "hi", "c": 3.0, "page_state": "boom"}
        with pytest.raises(KwargsContractError, match="page_state"):
            kwargs_for_call(
                payload,
                _fn_no_varkw,
                explicit_overrides={"page_state"},
            )

    def test_raises_on_conflict_with_varkw(self):
        payload = {"a": 1, "b": "hi", "page_state": "boom"}
        with pytest.raises(KwargsContractError, match="page_state"):
            kwargs_for_call(
                payload,
                _fn_with_varkw,
                explicit_overrides={"page_state"},
            )


# ─── Missing required ─────────────────────────────────────────────────


class TestMissingRequired:
    """Must raise when required params are missing from payload."""

    def test_missing_required_raises(self):
        payload = {"a": 1}  # missing b, c
        with pytest.raises(KwargsContractError, match="missing required"):
            kwargs_for_call(payload, _fn_no_varkw)

    def test_override_not_counted_as_missing(self):
        """Required params listed in overrides are NOT expected in payload."""
        payload = {"y": 2}
        result = kwargs_for_call(
            payload,
            _fn_all_required,
            explicit_overrides={"x"},
        )
        assert result == {"y": 2}


# ─── Strict extras ────────────────────────────────────────────────────


class TestStrictExtras:
    """strict_extras=True should reject unknown keys when fn has no **kwargs."""

    def test_strict_raises_on_extras(self):
        payload = {"a": 1, "b": "hi", "c": 3.0, "surprise": 99}
        with pytest.raises(KwargsContractError, match="unexpected keys"):
            kwargs_for_call(
                payload,
                _fn_no_varkw,
                strict_extras=True,
            )

    def test_strict_ok_when_no_extras(self):
        payload = {"a": 1, "b": "hi", "c": 3.0}
        result = kwargs_for_call(payload, _fn_no_varkw, strict_extras=True)
        assert result == {"a": 1, "b": "hi", "c": 3.0}

    def test_strict_ignored_when_varkw(self):
        """strict_extras is irrelevant when fn accepts **kwargs."""
        payload = {"a": 1, "b": "hi", "surprise": 99}
        result = kwargs_for_call(payload, _fn_with_varkw, strict_extras=True)
        assert "surprise" in result
