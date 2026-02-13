"""Event handlers for Gradio UI.

Pure functions that respond to UI events (clicks, changes, etc).
These handlers don't capture closures - they only depend on their parameters.

Internal modules
----------------
- ``_table``          - table preset / unit / zone dimension handlers.
- ``_toggles``        - section visibility toggles.
- ``_special_rules``  - add / remove special rules.
- ``_victory_points`` - add / remove victory points + polygon presets.
"""

from adapters.ui_gradio.handlers._special_rules import (  # noqa: F401
    add_special_rule,
    remove_last_special_rule,
    remove_selected_special_rule,
)
from adapters.ui_gradio.handlers._table import (  # noqa: F401
    on_table_preset_change,
    on_table_unit_change,
    on_zone_border_or_fill_change,
    update_objective_defaults,
)
from adapters.ui_gradio.handlers._toggles import (  # noqa: F401
    toggle_deployment_zones_section,
    toggle_objective_points_section,
    toggle_scenography_forms,
    toggle_scenography_section,
    toggle_section,
    toggle_special_rules_section,
    toggle_vp_section,
    update_shared_with_visibility,
)
from adapters.ui_gradio.handlers._victory_points import (  # noqa: F401
    add_victory_point,
    on_polygon_preset_change,
    remove_last_victory_point,
    remove_selected_victory_point,
)
