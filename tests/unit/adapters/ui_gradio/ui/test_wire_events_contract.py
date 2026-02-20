"""Golden-contract tests: ``build_create_page`` ↔ ``wire_events``.

Ensures that every **required** key declared in ``_REQUIRED_KEYS`` is
supplied by the create-page namespace (plus the explicit overrides
passed separately in ``app.py``), and — in strict / CI mode — that the
namespace carries *no* extra keys outside ``_ACCEPTED_KEYS``.

Since ``wire_events`` uses ``**kwargs`` (to avoid a 134-parameter
signature), coverage is validated against the exported key-set constants
rather than via signature introspection.
"""

from __future__ import annotations

import gradio as gr
import pytest
from adapters.ui_gradio.ui.pages.create_scenario import build_create_page
from adapters.ui_gradio.ui.wiring import (
    _ACCEPTED_KEYS,
    _REQUIRED_KEYS,
    wire_events,
)
from adapters.ui_gradio.ui.wiring._kwargs import kwargs_for_call

# ── Constants (must mirror app.py) ────────────────────────────────────

#: Keys passed *explicitly* in the ``wire_events(...)`` call site,
#: i.e. NOT coming from ``vars(create)``.
EXPLICIT_OVERRIDES: frozenset[str] = frozenset(
    {
        "page_state",
        "page_containers",
        "home_recent_html",
        "editing_card_id",
    }
)

#: Keys present in the namespace that are consumed by ``app.py``
#: directly (navigation, layout) — never forwarded to ``wire_events``.
NAMESPACE_ONLY: frozenset[str] = frozenset({"container", "back_btn"})


@pytest.fixture(scope="module")
def create_ns():
    """Build the create-page namespace once for the whole module."""
    with gr.Blocks():
        return build_create_page()


# ── Test 1: no missing required (always active) ──────────────────────


class TestNoMissingRequired:
    """All required ``wire_events`` keys must be covered."""

    def test_kwargs_for_call_succeeds(self, create_ns):
        """``kwargs_for_call`` must NOT raise ``KwargsContractError``."""
        payload = {k: v for k, v in vars(create_ns).items() if k not in NAMESPACE_ONLY}
        filtered = kwargs_for_call(
            payload,
            wire_events,
            explicit_overrides=EXPLICIT_OVERRIDES,
            strict_extras=False,
        )
        final_keys = set(filtered) | EXPLICIT_OVERRIDES
        missing = _REQUIRED_KEYS - final_keys
        assert not missing, f"Missing required wire_events keys: {sorted(missing)}"

    def test_all_required_present_via_set_arithmetic(self, create_ns):
        """Direct set arithmetic (no kwargs_for_call)."""
        source_keys = set(vars(create_ns)) - NAMESPACE_ONLY
        covered = source_keys | EXPLICIT_OVERRIDES
        missing = _REQUIRED_KEYS - covered
        assert not missing, f"Missing required wire_events keys: {sorted(missing)}"


# ── Test 2: no extras (strict — CI only) ─────────────────────────────


class TestNoExtrasStrict:
    """Create namespace must not carry keys that ``wire_events`` ignores."""

    def test_no_extras_via_set_arithmetic(self, create_ns):
        source_keys = set(vars(create_ns)) - NAMESPACE_ONLY
        extras = source_keys - _ACCEPTED_KEYS - EXPLICIT_OVERRIDES
        assert not extras, (
            f"Create namespace contains extras not accepted "
            f"by wire_events: {sorted(extras)}"
        )

    def test_kwargs_for_call_strict_does_not_raise(self, create_ns):
        """``kwargs_for_call(..., strict_extras=True)`` must succeed."""
        payload = {k: v for k, v in vars(create_ns).items() if k not in NAMESPACE_ONLY}
        # Must NOT raise KwargsContractError
        kwargs_for_call(
            payload,
            wire_events,
            explicit_overrides=EXPLICIT_OVERRIDES,
            strict_extras=True,
        )
