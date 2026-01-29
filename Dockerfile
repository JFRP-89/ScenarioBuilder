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
# Dependencies stage
# =============================================================================
FROM base AS deps

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Final stage
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

EXPOSE 8000 7860

# Default command (Flask API)
# Override in docker-compose for different services
CMD ["python", "-m", "flask", "--app", "adapters.http_flask.app:create_app", "run", "--host=0.0.0.0", "--port=8000"]
