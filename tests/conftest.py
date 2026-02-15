"""Test fixtures and configuration."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Keys that should NOT leak into general tests to avoid side-effects
# (e.g., connecting to a real database during unit/integration tests).
_DB_KEYS = {"DATABASE_URL", "DATABASE_URL_TEST"}


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load .env file at the start of the test session.

    Loads all variables EXCEPT database connection strings, which are
    only set explicitly in tests that need a real database (e.g., Alembic
    migration tests).
    """
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
    # Remove DB keys so general tests use InMemoryCardRepository
    saved = {}
    for key in _DB_KEYS:
        if key in os.environ:
            saved[key] = os.environ.pop(key)
    yield
    # Restore after session ends
    os.environ.update(saved)
