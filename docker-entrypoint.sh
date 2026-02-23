#!/bin/sh
# =============================================================================
# Docker entrypoint for ScenarioBuilder
# =============================================================================
# 1. Run Alembic migrations (fail-fast: if migrations fail, container exits)
# 2. Start Uvicorn ASGI server via exec (replaces shell → PID 1 signal handling)
# =============================================================================
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Uvicorn ASGI server on ${HOST}:${PORT} (log-level: ${LOG_LEVEL})..."
exec python -m uvicorn \
    adapters.combined_app:create_combined_app \
    --factory \
    --host "${HOST}" \
    --port "${PORT}" \
    --log-level "${LOG_LEVEL}"
