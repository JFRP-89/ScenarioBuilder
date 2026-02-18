# =============================================================================
# Multi-stage Dockerfile for ScenarioBuilder
# =============================================================================
FROM python:3.11-slim AS base

WORKDIR /app

# Python environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Dependencies stage (production)
# =============================================================================
FROM base AS deps

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Final stage (production — cloud-ready)
# =============================================================================
FROM base AS final

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code and migrations
COPY src/ /app/src/
COPY content/ /app/content/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY pytest.ini /app/

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# PORT is configurable via env var (PaaS like Railway, Render, Fly.io set it)
ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE ${PORT}

# Healthcheck for orchestrators (Docker Swarm, K8s liveness, ECS, etc.)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run migrations then start Uvicorn ASGI server on configurable host:port
CMD sh -c "alembic upgrade head && python -m uvicorn adapters.combined_app:create_combined_app --factory --host ${HOST} --port ${PORT}"
