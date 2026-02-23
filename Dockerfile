# =============================================================================
# Multi-stage Dockerfile for ScenarioBuilder — Production Image
# =============================================================================
# Target: Cloud-ready ASGI application (Uvicorn)
# Size optimization: slim base, multi-stage build, production deps only
# Security: non-root user, minimal surface area
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
# Final stage: Production runtime (ASGI + migrations — fail-fast)
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

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Create non-root user for security
RUN chmod +x /app/docker-entrypoint.sh && \
    useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# PORT is configurable via env var (PaaS like Railway, Render, Fly.io set it)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=info

EXPOSE 8000

# Healthcheck for orchestrators (Docker Swarm, K8s liveness, ECS, etc.)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations then start Uvicorn ASGI server (exec form)
# Production: Migrations fail-fast on startup, fails entire container (correct behavior)
ENTRYPOINT ["./docker-entrypoint.sh"]
