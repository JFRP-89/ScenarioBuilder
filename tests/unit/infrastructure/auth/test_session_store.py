"""Unit tests for infrastructure.auth.session_store."""

from __future__ import annotations

import pytest
from infrastructure.auth import session_store
from infrastructure.auth.session_store import (
    active_session_count,
    create_session,
    get_csrf_token,
    get_session,
    invalidate_session,
    is_recently_reauthed,
    mark_reauth,
    reset_sessions,
    rotate_session_id,
)
from infrastructure.clock import SystemClock

from tests.helpers.fake_clock import FakeClock


@pytest.fixture(autouse=True)
def _deterministic_clock():
    """Install a FakeClock and restore SystemClock after each test."""
    clock = FakeClock()
    session_store.set_clock(clock)
    reset_sessions()
    yield clock
    reset_sessions()
    session_store.set_clock(SystemClock())


@pytest.fixture()
def fake_clock(_deterministic_clock: FakeClock) -> FakeClock:
    """Expose the FakeClock for tests that need to manipulate time."""
    return _deterministic_clock


# ── create_session ───────────────────────────────────────────────────────────


class TestCreateSession:
    def test_returns_session_record(self):
        rec = create_session("alice")
        assert rec["actor_id"] == "alice"
        assert isinstance(rec["session_id"], str)
        assert len(rec["session_id"]) == 64  # 32 bytes hex
        assert isinstance(rec["csrf_token"], str)
        assert len(rec["csrf_token"]) == 64

    def test_session_id_is_unique(self):
        r1 = create_session("alice")
        r2 = create_session("alice")
        assert r1["session_id"] != r2["session_id"]

    def test_created_at_and_last_seen_are_set(self):
        rec = create_session("alice")
        assert rec["created_at"] is not None
        assert rec["last_seen_at"] is not None
        assert rec["reauth_at"] is None

    def test_active_count_increases(self):
        assert active_session_count() == 0
        create_session("alice")
        assert active_session_count() == 1
        create_session("bob")
        assert active_session_count() == 2


# ── get_session ──────────────────────────────────────────────────────────────


class TestGetSession:
    def test_returns_existing_session(self):
        rec = create_session("alice")
        result = get_session(rec["session_id"])
        assert result is not None
        assert result["actor_id"] == "alice"

    def test_returns_none_for_unknown_id(self):
        assert get_session("nonexistent") is None

    def test_updates_last_seen_at(self, fake_clock):
        rec = create_session("alice")
        old_last = rec["last_seen_at"]
        fake_clock.advance(seconds=1)
        result = get_session(rec["session_id"])
        assert result is not None
        assert result["last_seen_at"] > old_last

    def test_expired_by_idle_timeout(self, fake_clock):
        rec = create_session("alice")
        fake_clock.advance(minutes=20)
        assert get_session(rec["session_id"]) is None
        assert active_session_count() == 0

    def test_expired_by_max_lifetime(self, fake_clock):
        rec = create_session("alice")
        fake_clock.advance(hours=13)
        assert get_session(rec["session_id"]) is None

    def test_not_expired_within_limits(self, fake_clock):
        rec = create_session("alice")
        fake_clock.advance(minutes=10)
        result = get_session(rec["session_id"])
        assert result is not None


# ── invalidate_session ───────────────────────────────────────────────────────


class TestInvalidateSession:
    def test_removes_session(self):
        rec = create_session("alice")
        assert invalidate_session(rec["session_id"]) is True
        assert get_session(rec["session_id"]) is None

    def test_returns_false_for_unknown(self):
        assert invalidate_session("nonexistent") is False


# ── mark_reauth ──────────────────────────────────────────────────────────────


class TestMarkReauth:
    def test_marks_reauth_at(self):
        rec = create_session("alice")
        assert mark_reauth(rec["session_id"]) is True
        updated = get_session(rec["session_id"])
        assert updated is not None
        assert updated["reauth_at"] is not None

    def test_returns_false_for_unknown(self):
        assert mark_reauth("nonexistent") is False


# ── is_recently_reauthed ─────────────────────────────────────────────────────


class TestIsRecentlyReauthed:
    def test_false_when_no_reauth(self):
        rec = create_session("alice")
        assert is_recently_reauthed(rec["session_id"]) is False

    def test_true_after_mark(self):
        rec = create_session("alice")
        mark_reauth(rec["session_id"])
        assert is_recently_reauthed(rec["session_id"]) is True

    def test_false_after_window_expires(self, fake_clock):
        rec = create_session("alice")
        mark_reauth(rec["session_id"])
        fake_clock.advance(minutes=15)
        assert is_recently_reauthed(rec["session_id"]) is False

    def test_false_for_unknown(self):
        assert is_recently_reauthed("nonexistent") is False


# ── rotate_session_id ────────────────────────────────────────────────────────


class TestRotateSessionId:
    def test_new_id_preserves_actor(self):
        rec = create_session("alice")
        old_id = rec["session_id"]
        rotated = rotate_session_id(old_id)
        assert rotated is not None
        assert rotated["session_id"] != old_id
        assert rotated["actor_id"] == "alice"

    def test_old_id_invalidated(self):
        rec = create_session("alice")
        old_id = rec["session_id"]
        rotate_session_id(old_id)
        assert get_session(old_id) is None

    def test_new_id_valid(self):
        rec = create_session("alice")
        rotated = rotate_session_id(rec["session_id"])
        assert rotated is not None
        result = get_session(rotated["session_id"])
        assert result is not None
        assert result["actor_id"] == "alice"

    def test_preserves_created_at(self):
        rec = create_session("alice")
        created = rec["created_at"]
        rotated = rotate_session_id(rec["session_id"])
        assert rotated is not None
        assert rotated["created_at"] == created

    def test_new_csrf_token(self):
        rec = create_session("alice")
        old_csrf = rec["csrf_token"]
        rotated = rotate_session_id(rec["session_id"])
        assert rotated is not None
        assert rotated["csrf_token"] != old_csrf

    def test_returns_none_for_unknown(self):
        assert rotate_session_id("nonexistent") is None


# ── get_csrf_token ───────────────────────────────────────────────────────────


class TestGetCsrfToken:
    def test_returns_token(self):
        rec = create_session("alice")
        token = get_csrf_token(rec["session_id"])
        assert token == rec["csrf_token"]

    def test_returns_none_for_missing(self):
        assert get_csrf_token("nonexistent") is None


# ── reset_sessions ───────────────────────────────────────────────────────────


class TestResetSessions:
    def test_clears_all(self):
        create_session("alice")
        create_session("bob")
        reset_sessions()
        assert active_session_count() == 0
