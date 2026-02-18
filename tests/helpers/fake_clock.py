"""FakeClock — deterministic clock for testing.

Usage::

    clock = FakeClock()                         # starts at 2025-01-01T00:00Z
    clock.now_utc()                             # → 2025-01-01T00:00Z
    clock.advance(minutes=20)
    clock.now_utc()                             # → 2025-01-01T00:20Z

Satisfies the ``Clock`` protocol from ``application.ports.clock``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class FakeClock:
    """Deterministic clock — no real time ever passes."""

    __slots__ = ("_time",)

    def __init__(self, initial: datetime | None = None) -> None:
        self._time = initial or datetime(2025, 1, 1, tzinfo=timezone.utc)

    # ── Clock protocol ────────────────────────────────────────────
    def now_utc(self) -> datetime:
        return self._time

    # ── Test helpers ──────────────────────────────────────────────
    def advance(self, **kwargs: Any) -> None:
        """Advance the clock by the given ``timedelta`` keyword args."""
        self._time += timedelta(**kwargs)

    def set(self, time: datetime) -> None:
        """Set the clock to an exact instant."""
        self._time = time
