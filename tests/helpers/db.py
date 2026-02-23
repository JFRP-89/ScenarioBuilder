"""Shared database helpers for integration tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_alembic_upgrade(db_url: str) -> subprocess.CompletedProcess[str]:
    """Run ``alembic upgrade head`` against *db_url*.

    Returns the completed process so callers can inspect stdout/stderr.
    """
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["CI"] = "true"  # Prevent alembic/env.py overwriting with .env

    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
