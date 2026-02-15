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
# Dependencies stage (development - includes quality tools)
# Optional: Use for CI/CD quality checks
# =============================================================================
FROM base AS deps-dev

COPY requirements.txt requirements-dev.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements-dev.txt

# =============================================================================
# Final stage (production)
# =============================================================================
FROM base AS final

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/
COPY content/ /app/content/
COPY pytest.ini /app/

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Default command: Uvicorn ASGI server (combined FastAPI + Flask/Gradio app)
# This serves both the API and UI from a single process with shared cookie handling
CMD ["python", "-m", "uvicorn", "adapters.combined_app:create_combined_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Quality check stage (for CI/CD pipelines)
# Usage: docker build --target quality-check -t scenariobuilder:quality .
# =============================================================================
FROM base AS quality-check

# Copy installed packages from deps-dev stage (includes quality tools)
COPY --from=deps-dev /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps-dev /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY pytest.ini /app/

# Run quality checks (for CI/CD)
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Default: run quality gate
CMD ["python", "scripts/quality/run_quality.py", "--layer", "all"]
