"""System clock — production implementation of ``Clock`` port."""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClock:
    """Returns real UTC wall-clock time."""

    __slots__ = ()

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)
