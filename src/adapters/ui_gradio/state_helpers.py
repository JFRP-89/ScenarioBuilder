"""UI state helper functions for Gradio adapter — FACADE.

Re-exports all public helpers from internal ``_state.*`` modules.
All existing ``from adapters.ui_gradio.state_helpers import ...`` continue
to work without any change.

Pure helpers for manipulating state, validating geometry and unit conversion.
No Gradio imports — only stdlib + typing.
"""

from __future__ import annotations

# ── re-exports (keep alphabetical per module) ────────────────────────────────
from adapters.ui_gradio._state._config import get_default_actor_id
from adapters.ui_gradio._state._deployment_zones import (
    add_deployment_zone,
    calculate_zone_coordinates,
    calculate_zone_depth,
    calculate_zone_separation,
    deployment_zones_overlap,
    get_deployment_zones_choices,
    remove_last_deployment_zone,
    remove_selected_deployment_zone,
    update_deployment_zone,
    validate_deployment_zone_within_table,
    validate_separation_coords,
)
from adapters.ui_gradio._state._geometry import (
    bounding_boxes_overlap,
    circles_overlap,
    delete_polygon_row,
    get_circle_bounds,
    get_polygon_bounds,
    get_rect_bounds,
    rects_overlap,
    shapes_overlap,
    validate_circle_within_bounds,
    validate_polygon_within_bounds,
    validate_rect_within_bounds,
    validate_shape_within_table,
)
from adapters.ui_gradio._state._objective_points import (
    add_objective_point,
    get_objective_points_choices,
    remove_last_objective_point,
    remove_selected_objective_point,
    update_objective_point,
)
from adapters.ui_gradio._state._scenography import (
    add_scenography_element,
    get_scenography_choices,
    remove_last_scenography_element,
    remove_selected_scenography_element,
    update_scenography_element,
)
from adapters.ui_gradio._state._special_rules import (
    add_special_rule,
    get_special_rules_choices,
    remove_last_special_rule,
    remove_selected_special_rule,
    update_special_rule,
)
from adapters.ui_gradio._state._victory_points import (
    add_victory_point,
    get_victory_points_choices,
    remove_last_victory_point,
    remove_selected_victory_point,
    update_victory_point,
)

__all__ = [
    # config
    "get_default_actor_id",
    # special rules
    "add_special_rule",
    "get_special_rules_choices",
    "remove_last_special_rule",
    "remove_selected_special_rule",
    "update_special_rule",
    # victory points
    "add_victory_point",
    "get_victory_points_choices",
    "remove_last_victory_point",
    "remove_selected_victory_point",
    "update_victory_point",
    # geometry
    "bounding_boxes_overlap",
    "circles_overlap",
    "delete_polygon_row",
    "get_circle_bounds",
    "get_polygon_bounds",
    "get_rect_bounds",
    "rects_overlap",
    "shapes_overlap",
    "validate_circle_within_bounds",
    "validate_polygon_within_bounds",
    "validate_rect_within_bounds",
    "validate_shape_within_table",
    # scenography
    "add_scenography_element",
    "get_scenography_choices",
    "remove_last_scenography_element",
    "remove_selected_scenography_element",
    "update_scenography_element",
    # deployment zones
    "add_deployment_zone",
    "calculate_zone_coordinates",
    "calculate_zone_depth",
    "calculate_zone_separation",
    "deployment_zones_overlap",
    "get_deployment_zones_choices",
    "remove_last_deployment_zone",
    "remove_selected_deployment_zone",
    "update_deployment_zone",
    "validate_deployment_zone_within_table",
    "validate_separation_coords",
    # objective points
    "add_objective_point",
    "get_objective_points_choices",
    "remove_last_objective_point",
    "remove_selected_objective_point",
    "update_objective_point",
]
