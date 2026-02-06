"""Payload construction functions for Gradio UI adapter.

Compatibility layer that re-exports builders from the new modules.
"""

from adapters.ui_gradio.builders.payload import (
    apply_optional_text_fields,
    apply_special_rules,
    apply_table_config,
    apply_visibility,
    build_generate_payload,
)
from adapters.ui_gradio.builders.shapes import (
    build_deployment_shapes_from_state,
    build_map_specs_from_state,
    build_objective_shapes_from_state,
)

__all__ = [
    "apply_optional_text_fields",
    "apply_special_rules",
    "apply_table_config",
    "apply_visibility",
    "build_deployment_shapes_from_state",
    "build_generate_payload",
    "build_map_specs_from_state",
    "build_objective_shapes_from_state",
]
