"""Helpers para tests E2E API."""

import os


def get_api_base_url() -> str:
    """
    Obtiene la URL base de la API desde env var o default.

    Returns:
        API_BASE_URL (default: http://localhost:8000)
    """
    return os.environ.get("API_BASE_URL", "http://localhost:8000")
