"""Clock port — abstracts time for testability.

Production code uses ``SystemClock``; tests inject ``FakeClock``
to get fully deterministic behaviour without ``time.sleep``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Structural protocol for time providers."""

    def now_utc(self) -> datetime:
        """Return the current UTC time."""
        ...
