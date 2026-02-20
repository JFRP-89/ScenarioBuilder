"""Payload construction and validation for Gradio UI adapter.

Facade — re-exports from ``_payload.*`` internal modules.
Public API is unchanged; import from here as before.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.builders._payload._required_fields import (
    ValidationInput,
    validate_required_fields,
)
from adapters.ui_gradio.builders._payload._rules import (
    apply_special_rules,
)
from adapters.ui_gradio.builders._payload._table import (
    TABLE_MAX_CM,
    TABLE_MIN_CM,
    UNIT_LIMITS,
    apply_table_config,
)
from adapters.ui_gradio.builders._payload._text_fields import (
    apply_optional_text_fields,
)
from adapters.ui_gradio.builders._payload._victory_points import (
    validate_victory_points,
)
from adapters.ui_gradio.builders._payload._visibility import (
    apply_visibility,
)

__all__ = [
    "TABLE_MAX_CM",
    "TABLE_MIN_CM",
    "UNIT_LIMITS",
    "ValidationInput",
    "apply_optional_text_fields",
    "apply_special_rules",
    "apply_table_config",
    "apply_visibility",
    "build_generate_payload",
    "validate_required_fields",
    "validate_victory_points",
]


def build_generate_payload(mode: str, is_replicable: bool) -> dict[str, Any]:
    """Build base payload for generate card request.

    Args:
        mode: Game mode
        is_replicable: Whether to generate reproducible scenario

    Returns:
        Dict with mode and is_replicable fields
    """
    return {
        "mode": mode,
        "is_replicable": is_replicable,
    }
