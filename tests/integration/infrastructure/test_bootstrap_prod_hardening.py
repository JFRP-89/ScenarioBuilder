"""Tests for production-hardening rules in bootstrap.

Verifies that ``APP_ENV=prod`` enforces strict fail-fast behaviour for
the session store and blocks demo seeding, while dev mode retains
graceful fallbacks.

All tests run **without** a real PostgreSQL database — connections and
imports are mocked/monkeypatched as needed.
"""

from __future__ import annotations

import importlib
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_bootstrap():
    """Reimport bootstrap to pick up patched env vars."""
    import infrastructure.bootstrap as mod

    importlib.reload(mod)
    return mod


def _set_env(
    monkeypatch, *, app_env: str = "", db_url: str | None = None, seed: str = ""
):
    """Set the environment knobs used by bootstrap.

    ``db_url=None`` means "not set" but we use an empty string via
    ``setenv`` rather than ``delenv`` so that ``load_dotenv(override=False)``
    inside the reloaded module cannot overwrite it from a local ``.env``
    file.
    """
    monkeypatch.setenv("APP_ENV", app_env)
    if db_url is None:
        # Set to empty — semantically "not configured"
        monkeypatch.setenv("DATABASE_URL", "")
    else:
        monkeypatch.setenv("DATABASE_URL", db_url)
    if seed:
        monkeypatch.setenv("SEED_DEMO_USERS", seed)
    else:
        monkeypatch.setenv("SEED_DEMO_USERS", "")


VALID_PG_URL = "postgresql+psycopg2://u:p@localhost:5432/test"


# =========================================================================
# 1. Session store — ENV=prod, no DATABASE_URL → RuntimeError
# =========================================================================
class TestProdSessionStoreNoDatabaseUrl:

    def test_raises_when_database_url_missing(self, monkeypatch):
        _set_env(monkeypatch, app_env="prod", db_url=None)
        mod = _reload_bootstrap()
        with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
            mod._build_session_store()


# =========================================================================
# 2. Session store — ENV=prod, DATABASE_URL not postgres → RuntimeError
# =========================================================================
class TestProdSessionStoreNotPostgres:

    @pytest.mark.parametrize(
        "bad_url",
        [
            "sqlite:///test.db",
            "mysql://u:p@host/db",
            "http://example.com",
        ],
    )
    def test_raises_when_url_is_not_postgres(self, monkeypatch, bad_url):
        _set_env(monkeypatch, app_env="prod", db_url=bad_url)
        mod = _reload_bootstrap()
        with pytest.raises(RuntimeError, match="not a PostgreSQL URL"):
            mod._build_session_store()


# =========================================================================
# 3. Session store — ENV=prod, postgres URL, DB unreachable → RuntimeError
# =========================================================================
class TestProdSessionStoreDbUnreachable:

    def test_raises_when_db_is_unreachable(self, monkeypatch):
        _set_env(monkeypatch, app_env="prod", db_url=VALID_PG_URL)
        mod = _reload_bootstrap()

        # Stub the imports that _build_session_store does lazily
        fake_session_store_mod = types.ModuleType(
            "infrastructure.auth.postgres_session_store"
        )
        fake_session_store_mod.PostgresSessionStore = MagicMock  # type: ignore[attr-defined]

        fake_configure_mod = types.ModuleType("infrastructure.auth.session_store")
        fake_configure_mod.configure_store = MagicMock()  # type: ignore[attr-defined]

        fake_db_session_mod = types.ModuleType("infrastructure.db.session")
        failing_session = MagicMock()
        failing_session.return_value.execute.side_effect = ConnectionError("refused")
        fake_db_session_mod.SessionLocal = failing_session  # type: ignore[attr-defined]

        with (
            patch.dict(
                "sys.modules",
                {
                    "infrastructure.auth.postgres_session_store": fake_session_store_mod,
                    "infrastructure.auth.session_store": fake_configure_mod,
                    "infrastructure.db.session": fake_db_session_mod,
                },
            ),
            pytest.raises(RuntimeError, match="cannot connect to PostgreSQL"),
        ):
            mod._build_session_store()


# =========================================================================
# 4. Session store — ENV=prod, import fails → RuntimeError
# =========================================================================
class TestProdSessionStoreImportFails:

    def test_raises_when_sqlalchemy_not_installed(self, monkeypatch):
        _set_env(monkeypatch, app_env="prod", db_url=VALID_PG_URL)
        mod = _reload_bootstrap()

        # Make the lazy import fail
        with (
            patch.dict(
                "sys.modules",
                {
                    "infrastructure.auth.postgres_session_store": None,
                    "infrastructure.auth.session_store": None,
                    "infrastructure.db.session": None,
                },
            ),
            pytest.raises(RuntimeError, match="required dependency not installed"),
        ):
            mod._build_session_store()


# =========================================================================
# 5. Session store — ENV!=prod, DB unreachable → fallback (no error)
# =========================================================================
class TestDevSessionStoreFallback:

    def test_no_error_when_db_unreachable_in_dev(self, monkeypatch):
        _set_env(monkeypatch, app_env="dev", db_url=VALID_PG_URL)
        mod = _reload_bootstrap()

        fake_session_store_mod = types.ModuleType(
            "infrastructure.auth.postgres_session_store"
        )
        fake_session_store_mod.PostgresSessionStore = MagicMock  # type: ignore[attr-defined]

        fake_configure_mod = types.ModuleType("infrastructure.auth.session_store")
        fake_configure_mod.configure_store = MagicMock()  # type: ignore[attr-defined]

        fake_db_session_mod = types.ModuleType("infrastructure.db.session")
        failing_session = MagicMock()
        failing_session.return_value.execute.side_effect = ConnectionError("refused")
        fake_db_session_mod.SessionLocal = failing_session  # type: ignore[attr-defined]

        with patch.dict(
            "sys.modules",
            {
                "infrastructure.auth.postgres_session_store": fake_session_store_mod,
                "infrastructure.auth.session_store": fake_configure_mod,
                "infrastructure.db.session": fake_db_session_mod,
            },
        ):
            # Should NOT raise — logs warning and falls back
            mod._build_session_store()

    def test_no_error_when_database_url_missing_in_dev(self, monkeypatch):
        _set_env(monkeypatch, app_env="dev", db_url=None)
        mod = _reload_bootstrap()
        # Should silently fall back to in-memory
        mod._build_session_store()

    def test_no_error_when_url_not_postgres_in_dev(self, monkeypatch):
        _set_env(monkeypatch, app_env="dev", db_url="sqlite:///test.db")
        mod = _reload_bootstrap()
        mod._build_session_store()


# =========================================================================
# 6. Seed demo — blocked in prod even if explicitly requested
# =========================================================================
class TestSeedDemoBlockedInProd:

    def test_seed_demo_not_called_in_prod(self, monkeypatch):
        _set_env(monkeypatch, app_env="prod", db_url=VALID_PG_URL)

        # Stub the session store wiring to avoid a real DB connection
        mod = _reload_bootstrap()
        monkeypatch.setattr(mod, "_build_session_store", lambda: None)

        # Enable the seed flag — should still be ignored in prod
        monkeypatch.setenv("SEED_DEMO_USERS", "1")

        seed_fn = MagicMock()
        with patch.dict(
            "sys.modules",
            {
                "infrastructure.auth.user_store": MagicMock(
                    seed_demo_users_to_database=seed_fn
                ),
            },
        ):
            mod.build_services()

        seed_fn.assert_not_called()


# =========================================================================
# 7. Seed demo — allowed in dev when explicitly opted-in
# =========================================================================
class TestSeedDemoAllowedInDev:

    def test_seed_demo_called_in_dev_when_enabled(self, monkeypatch):
        _set_env(monkeypatch, app_env="dev", db_url=None, seed="1")
        mod = _reload_bootstrap()
        monkeypatch.setattr(mod, "_build_session_store", lambda: None)

        seed_fn = MagicMock()
        fake_user_store = types.ModuleType("infrastructure.auth.user_store")
        fake_user_store.seed_demo_users_to_database = seed_fn  # type: ignore[attr-defined]

        with patch.dict(
            "sys.modules",
            {"infrastructure.auth.user_store": fake_user_store},
        ):
            mod.build_services()

        seed_fn.assert_called_once()

    def test_seed_demo_not_called_in_dev_when_disabled(self, monkeypatch):
        _set_env(monkeypatch, app_env="dev", db_url=None, seed="0")
        mod = _reload_bootstrap()
        monkeypatch.setattr(mod, "_build_session_store", lambda: None)

        seed_fn = MagicMock()
        with patch.dict(
            "sys.modules",
            {
                "infrastructure.auth.user_store": MagicMock(
                    seed_demo_users_to_database=seed_fn
                ),
            },
        ):
            mod.build_services()

        seed_fn.assert_not_called()


# =========================================================================
# 8. Environment helpers
# =========================================================================
class TestEnvironmentHelpers:

    def test_is_prod_true(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        mod = _reload_bootstrap()
        assert mod._is_prod() is True

    def test_is_prod_false_for_dev(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        mod = _reload_bootstrap()
        assert mod._is_prod() is False

    def test_is_prod_false_when_unset(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "")
        mod = _reload_bootstrap()
        assert mod._is_prod() is False

    def test_get_env_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "  hello  ")
        mod = _reload_bootstrap()
        assert mod._get_env("TEST_VAR") == "hello"

    def test_get_env_returns_default(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "")
        mod = _reload_bootstrap()
        # empty string → falls through to default
        assert mod._get_env("TEST_VAR", "fallback") == ""
