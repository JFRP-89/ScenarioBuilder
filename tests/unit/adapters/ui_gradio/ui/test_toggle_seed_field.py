"""Tests for the seed-field toggle logic.

When the user toggles replicability OFF, the seed value is saved and
cleared.  When toggled back ON, the previously-saved seed is restored.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# We extract the same logic used by the closure inside wire_events so we can
# unit-test it in isolation without booting a full Gradio app.
# ---------------------------------------------------------------------------
class _SeedToggle:
    """Mirrors the closure logic in wiring/__init__.py."""

    def __init__(self) -> None:
        self._saved: float | None = None

    def toggle(
        self, replicable: bool, current_seed: float | None
    ) -> tuple[float | None, bool]:
        """Return (seed_value, interactive).

        The actual closure returns gr.update dicts; here we return the
        semantic values so assertions are clearer.
        """
        if replicable:
            return self._saved, True
        self._saved = current_seed
        return None, False


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def toggle() -> _SeedToggle:
    return _SeedToggle()


# =============================================================================
# TESTS
# =============================================================================
class TestToggleSeedFieldRestore:
    """Toggling OFF then ON restores the previous seed."""

    def test_off_clears_seed(self, toggle: _SeedToggle) -> None:
        seed_val, interactive = toggle.toggle(False, 548270841)
        assert seed_val is None
        assert interactive is False

    def test_on_after_off_restores_seed(self, toggle: _SeedToggle) -> None:
        toggle.toggle(False, 548270841)
        seed_val, interactive = toggle.toggle(True, None)
        assert seed_val == 548270841
        assert interactive is True

    def test_double_off_on_restores_same_seed(self, toggle: _SeedToggle) -> None:
        """OFF→ON→OFF→ON keeps restoring the same seed."""
        toggle.toggle(False, 548270841)
        toggle.toggle(True, None)  # restores 548270841
        toggle.toggle(False, 548270841)  # save again
        seed_val, _ = toggle.toggle(True, None)
        assert seed_val == 548270841

    def test_new_seed_applied_and_restored(self, toggle: _SeedToggle) -> None:
        """If user changes the seed before toggling OFF, new seed is saved."""
        toggle.toggle(False, 100)
        toggle.toggle(True, None)  # restores 100
        # user changes field to 999
        toggle.toggle(False, 999)
        seed_val, _ = toggle.toggle(True, None)
        assert seed_val == 999

    def test_initial_on_returns_none(self, toggle: _SeedToggle) -> None:
        """First toggle ON with no previous save → None (no saved seed)."""
        seed_val, interactive = toggle.toggle(True, None)
        assert seed_val is None
        assert interactive is True

    def test_off_saves_none_when_field_empty(self, toggle: _SeedToggle) -> None:
        """Toggling OFF when field is empty saves None."""
        toggle.toggle(False, None)
        seed_val, _ = toggle.toggle(True, None)
        assert seed_val is None

    def test_off_saves_zero(self, toggle: _SeedToggle) -> None:
        """Toggling OFF with seed=0 saves 0 and restores it."""
        toggle.toggle(False, 0)
        seed_val, _ = toggle.toggle(True, None)
        assert seed_val == 0
