"""Integration tests for PostgresSessionStore — PostgreSQL-backed sessions.

Requires a running PostgreSQL instance (configured via DATABASE_URL in .env).
These tests exercise the full CRUD lifecycle of sessions, including:
  - create + retrieve
  - idle timeout expiry
  - max lifetime expiry
  - rotation (atomically revokes old + creates new)
  - revocation (single and bulk)
  - CSRF token retrieval
  - reauth marking + window check
  - touch throttling
  - cleanup of expired/revoked sessions
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

# ── Deferred imports (DB modules can't load at collection time) ─────────────


def _import_pss():
    """Return the ``postgres_session_store`` module (deferred)."""
    from infrastructure.auth import postgres_session_store as pss

    return pss


def _make_store():
    """Create a fresh ``PostgresSessionStore`` with real SessionLocal."""
    from infrastructure.auth.postgres_session_store import PostgresSessionStore
    from infrastructure.db.session import SessionLocal

    return PostgresSessionStore(session_factory=SessionLocal)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def store():
    """Fresh PostgresSessionStore instance, cleaned before and after."""
    s = _make_store()
    s.reset_sessions()
    yield s
    s.reset_sessions()


@pytest.fixture()
def pss():
    """Return the postgres_session_store module for patching."""
    return _import_pss()


# ── create_session ──────────────────────────────────────────────────────────


class TestCreateSession:
    def test_returns_session_record(self, store):
        rec = store.create_session("alice")
        assert rec["actor_id"] == "alice"
        assert isinstance(rec["session_id"], str)
        assert len(rec["session_id"]) == 64  # 32 bytes hex
        assert isinstance(rec["csrf_token"], str)
        assert len(rec["csrf_token"]) == 64

    def test_session_id_is_unique(self, store):
        r1 = store.create_session("alice")
        r2 = store.create_session("alice")
        assert r1["session_id"] != r2["session_id"]

    def test_timestamps_are_set(self, store):
        rec = store.create_session("alice")
        assert rec["created_at"] is not None
        assert rec["last_seen_at"] is not None
        assert rec["reauth_at"] is None

    def test_active_count_increases(self, store):
        assert store.active_session_count() == 0
        store.create_session("alice")
        assert store.active_session_count() == 1
        store.create_session("bob")
        assert store.active_session_count() == 2


# ── get_session ─────────────────────────────────────────────────────────────


class TestGetSession:
    def test_returns_existing_session(self, store):
        rec = store.create_session("alice")
        result = store.get_session(rec["session_id"])
        assert result is not None
        assert result["actor_id"] == "alice"

    def test_returns_none_for_unknown_id(self, store):
        assert store.get_session("nonexistent") is None

    def test_returns_none_for_empty_id(self, store):
        assert store.get_session("") is None

    def test_expired_by_idle_timeout(self, store, pss):
        rec = store.create_session("alice")
        future = datetime.now(timezone.utc) + timedelta(minutes=20)
        with patch.object(pss, "_now", return_value=future):
            assert store.get_session(rec["session_id"]) is None

    def test_expired_by_max_lifetime(self, store, pss):
        rec = store.create_session("alice")
        future = datetime.now(timezone.utc) + timedelta(hours=13)
        with patch.object(pss, "_now", return_value=future):
            assert store.get_session(rec["session_id"]) is None

    def test_not_expired_within_limits(self, store, pss):
        rec = store.create_session("alice")
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        with patch.object(pss, "_now", return_value=future):
            result = store.get_session(rec["session_id"])
            assert result is not None


# ── invalidate_session ──────────────────────────────────────────────────────


class TestInvalidateSession:
    def test_revokes_session(self, store):
        rec = store.create_session("alice")
        assert store.invalidate_session(rec["session_id"]) is True
        assert store.get_session(rec["session_id"]) is None

    def test_returns_false_for_unknown(self, store):
        assert store.invalidate_session("nonexistent") is False

    def test_returns_false_for_already_revoked(self, store):
        rec = store.create_session("alice")
        store.invalidate_session(rec["session_id"])
        assert store.invalidate_session(rec["session_id"]) is False


# ── revoke_all_sessions ────────────────────────────────────────────────────


class TestRevokeAllSessions:
    def test_revokes_all_for_user(self, store):
        store.create_session("alice")
        store.create_session("alice")
        store.create_session("bob")
        assert store.revoke_all_sessions("alice") == 2
        assert store.active_session_count() == 1

    def test_returns_zero_if_none(self, store):
        assert store.revoke_all_sessions("nobody") == 0


# ── mark_reauth ─────────────────────────────────────────────────────────────


class TestMarkReauth:
    def test_marks_reauth_at(self, store):
        rec = store.create_session("alice")
        assert store.mark_reauth(rec["session_id"]) is True
        updated = store.get_session(rec["session_id"])
        assert updated is not None
        assert updated["reauth_at"] is not None

    def test_returns_false_for_unknown(self, store):
        assert store.mark_reauth("nonexistent") is False


# ── is_recently_reauthed ────────────────────────────────────────────────────


class TestIsRecentlyReauthed:
    def test_false_when_no_reauth(self, store):
        rec = store.create_session("alice")
        assert store.is_recently_reauthed(rec["session_id"]) is False

    def test_true_after_mark(self, store):
        rec = store.create_session("alice")
        store.mark_reauth(rec["session_id"])
        assert store.is_recently_reauthed(rec["session_id"]) is True

    def test_false_after_window_expires(self, store, pss):
        rec = store.create_session("alice")
        store.mark_reauth(rec["session_id"])
        future = datetime.now(timezone.utc) + timedelta(minutes=15)
        with patch.object(pss, "_now", return_value=future):
            assert store.is_recently_reauthed(rec["session_id"]) is False

    def test_false_for_unknown(self, store):
        assert store.is_recently_reauthed("nonexistent") is False


# ── rotate_session_id ───────────────────────────────────────────────────────


class TestRotateSessionId:
    def test_new_id_preserves_actor(self, store):
        rec = store.create_session("alice")
        old_id = rec["session_id"]
        rotated = store.rotate_session_id(old_id)
        assert rotated is not None
        assert rotated["session_id"] != old_id
        assert rotated["actor_id"] == "alice"

    def test_old_id_invalidated(self, store):
        rec = store.create_session("alice")
        old_id = rec["session_id"]
        store.rotate_session_id(old_id)
        assert store.get_session(old_id) is None

    def test_new_id_valid(self, store):
        rec = store.create_session("alice")
        rotated = store.rotate_session_id(rec["session_id"])
        assert rotated is not None
        result = store.get_session(rotated["session_id"])
        assert result is not None
        assert result["actor_id"] == "alice"

    def test_preserves_created_at(self, store):
        rec = store.create_session("alice")
        created = rec["created_at"]
        rotated = store.rotate_session_id(rec["session_id"])
        assert rotated is not None
        assert rotated["created_at"] == created

    def test_new_csrf_token(self, store):
        rec = store.create_session("alice")
        old_csrf = rec["csrf_token"]
        rotated = store.rotate_session_id(rec["session_id"])
        assert rotated is not None
        assert rotated["csrf_token"] != old_csrf

    def test_returns_none_for_unknown(self, store):
        assert store.rotate_session_id("nonexistent") is None


# ── get_csrf_token ──────────────────────────────────────────────────────────


class TestGetCsrfToken:
    def test_returns_token(self, store):
        rec = store.create_session("alice")
        token = store.get_csrf_token(rec["session_id"])
        assert token == rec["csrf_token"]

    def test_returns_none_for_missing(self, store):
        assert store.get_csrf_token("nonexistent") is None

    def test_returns_none_for_revoked(self, store):
        rec = store.create_session("alice")
        store.invalidate_session(rec["session_id"])
        assert store.get_csrf_token(rec["session_id"]) is None


# ── cleanup_expired_sessions ────────────────────────────────────────────────


class TestCleanupExpiredSessions:
    def test_removes_expired_sessions(self, store, pss):
        store.create_session("alice")
        future = datetime.now(timezone.utc) + timedelta(hours=13)
        with patch.object(pss, "_now", return_value=future):
            removed = store.cleanup_expired_sessions()
            assert removed >= 1

    def test_removes_old_revoked_sessions(self, store, pss):
        rec = store.create_session("alice")
        store.invalidate_session(rec["session_id"])
        # Skip 25 hours into the future
        future = datetime.now(timezone.utc) + timedelta(hours=25)
        with patch.object(pss, "_now", return_value=future):
            removed = store.cleanup_expired_sessions()
            assert removed >= 1


# ── reset_sessions ──────────────────────────────────────────────────────────


class TestResetSessions:
    def test_clears_all(self, store):
        store.create_session("alice")
        store.create_session("bob")
        store.reset_sessions()
        assert store.active_session_count() == 0


# ── touch throttling ───────────────────────────────────────────────────────


class TestTouchThrottling:
    def test_last_seen_not_updated_within_throttle(self, store, pss):
        rec = store.create_session("alice")
        initial_last_seen = rec["last_seen_at"]

        # Get within throttle window (< 30s) — should NOT update last_seen
        # Patch _now to be 10 seconds later
        near_future = initial_last_seen + timedelta(seconds=10)
        with patch.object(pss, "_now", return_value=near_future):
            result = store.get_session(rec["session_id"])
            assert result is not None
            # last_seen should NOT have changed (still initial)
            assert result["last_seen_at"] == initial_last_seen

    def test_last_seen_updated_after_throttle(self, store, pss):
        rec = store.create_session("alice")
        initial_last_seen = rec["last_seen_at"]

        # Get beyond throttle window (> 30s) — should update last_seen
        far_future = initial_last_seen + timedelta(seconds=60)
        with patch.object(pss, "_now", return_value=far_future):
            result = store.get_session(rec["session_id"])
            assert result is not None
            assert result["last_seen_at"] == far_future
