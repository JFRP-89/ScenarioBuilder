"""Constants for Gradio UI adapter."""

# ============================================================================
# API Endpoints
# ============================================================================
ENDPOINT_GENERATE_CARD = "/cards"

# ============================================================================
# Payload fields
# ============================================================================
FIELD_MODE = "mode"
FIELD_SEED = "seed"
FIELD_TABLE_PRESET = "table_preset"

# ============================================================================
# Defaults
# ============================================================================
DEFAULT_TABLE_PRESET = "standard"
REQUEST_TIMEOUT_SECONDS = 30
SUCCESS_STATUS_CODES = {200, 201}

# ============================================================================
# Error messages
# ============================================================================
ERROR_REQUESTS_NOT_AVAILABLE = "requests library not available"
ERROR_API_FAILURE = "API error"
ERROR_REQUEST_FAILED = "Request failed"
ERROR_UNEXPECTED = "Unexpected error"
