"""Shared fixtures for infrastructure.auth unit tests."""

from __future__ import annotations

import pytest

from helpers.fake_clock import FakeClock
from infrastructure.auth import session_store
from infrastructure.auth.session_store import reset_sessions
from infrastructure.clock import SystemClock


@pytest.fixture(autouse=True)
def _deterministic_clock():
    """Install a FakeClock, force in-memory backend, restore after each test.

    When integration tests (e.g. test_bootstrap_services) run first they may
    call ``build_services()`` which configures a ``PostgresSessionStore``.
    That store has its own clock, so the module-level ``set_clock()`` would
    be ignored.  Forcing ``reset_store()`` ensures the in-memory
    path is used and our ``FakeClock`` controls time.
    """
    # Save previous state
    prev_store = session_store.get_store()

    # Force in-memory backend + deterministic clock
    session_store.reset_store()
    clock = FakeClock()
    session_store.set_clock(clock)
    reset_sessions()

    yield clock

    # Restore previous state
    reset_sessions()
    session_store.set_clock(SystemClock())
    if prev_store is not None:
        session_store.configure_store(prev_store)
    else:
        session_store.reset_store()


@pytest.fixture()
def fake_clock(_deterministic_clock: FakeClock) -> FakeClock:
    """Expose the FakeClock for tests that need to manipulate time."""
    return _deterministic_clock
