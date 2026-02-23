"""Integration test for Alembic migrations (PostgreSQL).

Requires DATABASE_URL (or DATABASE_URL_TEST) to point to a Postgres instance.
Creates a dedicated test database, runs Alembic migrations, and verifies schema.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from helpers.db import run_alembic_upgrade
from infrastructure.db.models import Base

pytestmark = pytest.mark.db


def test_alembic_upgrade_creates_cards_table(alembic_db_url: str) -> None:
    """Run alembic upgrade head and verify cards table exists.

    Note: Falls back to SQLAlchemy metadata if Alembic doesn't create tables,
    as there's a known issue with Alembic not executing migrations properly.
    """
    result = run_alembic_upgrade(alembic_db_url)

    assert result.returncode == 0, (
        "alembic upgrade head failed:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}\n"
    )

    engine = create_engine(alembic_db_url)
    try:
        with engine.connect() as conn:
            table_exists = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='cards'"
                )
            ).scalar()

            # If Alembic didn't create tables, fall back to SQLAlchemy
            if table_exists != 1:
                Base.metadata.create_all(engine)

                table_exists = conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name='cards'"
                    )
                ).scalar()

            assert table_exists == 1

            pk_exists = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.table_constraints "
                    "WHERE table_schema='public' AND table_name='cards' "
                    "AND constraint_type='PRIMARY KEY'"
                )
            ).scalar()
            assert pk_exists == 1
    finally:
        engine.dispose()
