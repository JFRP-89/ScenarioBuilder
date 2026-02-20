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

# ============================================================================
# Defaults
# ============================================================================
DEFAULT_TABLE_PRESET = "standard"
REQUEST_TIMEOUT_SECONDS = 30

# ============================================================================
# Error messages
# ============================================================================
ERROR_REQUESTS_NOT_AVAILABLE = "requests library not available"
ERROR_API_FAILURE = "API error"
ERROR_REQUEST_FAILED = "Request failed"
ERROR_UNEXPECTED = "Unexpected error"

# ============================================================================
# Table size limits
# ============================================================================
TABLE_MIN_CM = 60
TABLE_MAX_CM = 300
CM_PER_INCH = 2.5
CM_PER_FOOT = 30.0

TABLE_STANDARD_CM = (120, 120)
TABLE_MASSIVE_CM = (180, 120)

UNIT_LIMITS: dict[str, dict[str, int | float]] = {
    "cm": {"min": TABLE_MIN_CM, "max": TABLE_MAX_CM},
    "in": {"min": 24, "max": 120},
    "ft": {"min": 2, "max": 10},
}

# ============================================================================
# Scenography
# ============================================================================
SCENOGRAPHY_TYPES = ["circle", "rect", "polygon"]
POLYGON_PRESETS: dict[str, int] = {
    "triangle": 3,
    "pentagon": 5,
    "hexagon": 6,
}

# ============================================================================
# Deployment Zones
# ============================================================================
DEPLOYMENT_MAX_ZONES = 4
DEPLOYMENT_ZONE_MIN_SIZE = 100  # mm
DEPLOYMENT_ZONE_MAX_SIZE = 2000  # mm
