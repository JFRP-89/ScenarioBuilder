"""HTTP adapter constants to avoid magic strings in Flask routes."""

from __future__ import annotations

# JSON keys
KEY_CARD_ID = "card_id"
KEY_OWNER_ID = "owner_id"
KEY_SEED = "seed"
KEY_MODE = "mode"
KEY_VISIBILITY = "visibility"
KEY_TABLE_MM = "table_mm"
KEY_SHAPES = "shapes"
KEY_CARDS = "cards"
KEY_SHARED_WITH = "shared_with"
KEY_TABLE_PRESET = "table_preset"
KEY_FILTER = "filter"
KEY_STATUS = "status"
KEY_IS_FAVORITE = "is_favorite"
KEY_CARD_IDS = "card_ids"
KEY_ARMIES = "armies"
KEY_DEPLOYMENT = "deployment"
KEY_LAYOUT = "layout"
KEY_OBJECTIVES = "objectives"
KEY_OBJECTIVE_SHAPES = "objective_shapes"
KEY_INITIAL_PRIORITY = "initial_priority"
KEY_NAME = "name"
KEY_SPECIAL_RULES = "special_rules"
KEY_DEPLOYMENT_SHAPES = "deployment_shapes"
KEY_SCENOGRAPHY_SPECS = "scenography_specs"

# Defaults
DEFAULT_MODE = "casual"
DEFAULT_VISIBILITY = "private"
DEFAULT_TABLE_PRESET = "standard"
DEFAULT_FILTER = "mine"

# Allowed values (adapter-level reference only)
ALLOWED_GAME_MODES = {"casual", "narrative", "matched"}
ALLOWED_VISIBILITIES = {"private", "shared", "public"}
ALLOWED_TABLE_PRESETS = {"standard", "massive"}

# Table presets
TABLE_PRESET_STANDARD = "standard"
TABLE_PRESET_MASSIVE = "massive"

# Health
STATUS_OK = "ok"
