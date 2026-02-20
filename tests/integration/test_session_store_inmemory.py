"""Integration tests for the in-memory session store.

Covers: create_session, get_session (touch + expiry paths),
invalidate_session, mark_reauth, rotate_session_id,
is_recently_reauthed, get_csrf_token, reset_sessions,
active_session_count, set_clock.

Uses monkeypatch to isolate from the module-global _SESSIONS dict
and avoids touching the disk-based persistence file.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from infrastructure.auth import session_store


class _FakeClock:
    """Clock that returns a settable time."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def set(self, now: datetime) -> None:
        self._now = now

    def now_utc(self) -> datetime:
        return self._now


@pytest.fixture(autouse=True)
def _isolate_session_module(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Reset module state so tests don't pollute each other."""
    # Redirect store to None (use in-memory fallback)
    monkeypatch.setattr(session_store, "_store_holder", [None])
    # Clear sessions dict
    session_store._SESSIONS.clear()
    # Point disk path to temp so writes don't touch real file
    monkeypatch.setattr(session_store, "_STORE_PATH", tmp_path / "sess.json")
    # Install a known clock
    clock = _FakeClock(datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc))
    session_store.set_clock(clock)
    yield clock
    # Restore system clock
    from infrastructure.clock import SystemClock

    session_store.set_clock(SystemClock())


# ═════════════════════════════════════════════════════════════════════════════
# Basic CRUD
# ═════════════════════════════════════════════════════════════════════════════
class TestSessionCRUD:
    def test_create_and_get(self, _isolate_session_module) -> None:
        rec = session_store.create_session("alice")
        assert rec["actor_id"] == "alice"
        assert rec["csrf_token"]
        fetched = session_store.get_session(rec["session_id"])
        assert fetched is not None
        assert fetched["actor_id"] == "alice"

    def test_get_nonexistent_returns_none(self) -> None:
        assert session_store.get_session("no-such-id") is None

    def test_active_session_count(self) -> None:
        assert session_store.active_session_count() == 0
        session_store.create_session("bob")
        assert session_store.active_session_count() == 1

    def test_invalidate_existing(self) -> None:
        rec = session_store.create_session("carol")
        assert session_store.invalidate_session(rec["session_id"]) is True
        assert session_store.get_session(rec["session_id"]) is None

    def test_invalidate_nonexistent(self) -> None:
        assert session_store.invalidate_session("no-such") is False

    def test_reset_sessions(self) -> None:
        session_store.create_session("d1")
        session_store.create_session("d2")
        session_store.reset_sessions()
        assert session_store.active_session_count() == 0


# ═════════════════════════════════════════════════════════════════════════════
# Expiry (idle + max lifetime)
# ═════════════════════════════════════════════════════════════════════════════
class TestSessionExpiry:
    def test_idle_timeout_expires_session(self, _isolate_session_module) -> None:
        clock: _FakeClock = _isolate_session_module
        rec = session_store.create_session("eve")
        # Advance beyond idle timeout
        clock.set(
            datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
            + timedelta(minutes=session_store.SESSION_IDLE_MINUTES + 1)
        )
        assert session_store.get_session(rec["session_id"]) is None

    def test_max_lifetime_expires_session(self, _isolate_session_module) -> None:
        clock: _FakeClock = _isolate_session_module
        rec = session_store.create_session("frank")
        # Touch it so idle doesn't expire first
        clock.set(
            datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
            + timedelta(hours=session_store.SESSION_MAX_HOURS + 1)
        )
        assert session_store.get_session(rec["session_id"]) is None

    def test_valid_session_touch_updates_last_seen(
        self, _isolate_session_module
    ) -> None:
        clock: _FakeClock = _isolate_session_module
        rec = session_store.create_session("grace")
        # Advance 5 minutes (within idle window)
        clock.set(datetime(2025, 6, 1, 12, 5, 0, tzinfo=timezone.utc))
        fetched = session_store.get_session(rec["session_id"])
        assert fetched is not None
        assert fetched["last_seen_at"] == clock.now_utc()


# ═════════════════════════════════════════════════════════════════════════════
# Reauth + rotation
# ═════════════════════════════════════════════════════════════════════════════
class TestReauthAndRotation:
    def test_mark_reauth_sets_timestamp(self, _isolate_session_module) -> None:
        rec = session_store.create_session("hank")
        assert session_store.mark_reauth(rec["session_id"]) is True
        assert session_store.is_recently_reauthed(rec["session_id"]) is True

    def test_mark_reauth_nonexistent_returns_false(self) -> None:
        assert session_store.mark_reauth("bad-id") is False

    def test_is_recently_reauthed_false_without_mark(self) -> None:
        rec = session_store.create_session("iris")
        assert session_store.is_recently_reauthed(rec["session_id"]) is False

    def test_is_recently_reauthed_expires(self, _isolate_session_module) -> None:
        clock: _FakeClock = _isolate_session_module
        rec = session_store.create_session("jade")
        session_store.mark_reauth(rec["session_id"])
        # Advance beyond reauth window
        clock.set(
            datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
            + timedelta(minutes=session_store.REAUTH_WINDOW_MINUTES + 1)
        )
        assert session_store.is_recently_reauthed(rec["session_id"]) is False

    def test_is_recently_reauthed_nonexistent(self) -> None:
        assert session_store.is_recently_reauthed("x") is False

    def test_rotate_session_id(self) -> None:
        rec = session_store.create_session("karl")
        old_id = rec["session_id"]
        rotated = session_store.rotate_session_id(old_id)
        assert rotated is not None
        assert rotated["session_id"] != old_id
        assert rotated["actor_id"] == "karl"
        # Old session gone
        assert session_store.get_session(old_id) is None
        # New session works
        assert session_store.get_session(rotated["session_id"]) is not None

    def test_rotate_nonexistent_returns_none(self) -> None:
        assert session_store.rotate_session_id("nope") is None


# ═════════════════════════════════════════════════════════════════════════════
# CSRF token
# ═════════════════════════════════════════════════════════════════════════════
class TestCsrfToken:
    def test_get_csrf_token(self) -> None:
        rec = session_store.create_session("luna")
        token = session_store.get_csrf_token(rec["session_id"])
        assert token == rec["csrf_token"]

    def test_get_csrf_token_nonexistent(self) -> None:
        assert session_store.get_csrf_token("missing") is None
