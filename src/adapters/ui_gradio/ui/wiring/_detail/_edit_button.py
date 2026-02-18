"""Edit-button wiring — populates the Create form and navigates to edit mode.

Extracted from ``wire_detail.py`` to reduce its size.  The public entry
point is :func:`wire_edit_button`, called by ``wire_detail_page`` when the
edit-mode widgets are available.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.state_helpers import (
    get_deployment_zones_choices,
    get_objective_points_choices,
    get_scenography_choices,
    get_special_rules_choices,
    get_victory_points_choices,
)
from adapters.ui_gradio.ui.components.search_helpers import escape_html
from adapters.ui_gradio.ui.router import PAGE_EDIT, navigate_to
from adapters.ui_gradio.ui.wiring._detail._converters import (
    _api_deployment_to_state,
    _api_objectives_to_state,
    _api_scenography_to_state,
    _api_special_rules_to_state,
    _extract_objectives_text_for_form,
)


def wire_edit_button(  # noqa: C901
    *,
    fetch_card_and_svg: Any,
    detail_edit_btn: gr.Button,
    detail_card_id_state: gr.State,
    page_state: gr.State,
    page_containers: list[gr.Column],
    editing_card_id: gr.State,
    editing_reload_trigger: gr.State | None,
    create_heading_md: gr.Markdown,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    is_replicable: gr.Checkbox,
    armies: gr.Textbox,
    table_preset: gr.Radio | None,
    deployment: gr.Textbox,
    layout: gr.Textbox,
    objectives: gr.Textbox,
    initial_priority: gr.Textbox,
    objectives_with_vp_toggle: gr.Checkbox | None,
    vp_state: gr.State | None,
    visibility: gr.Radio | None,
    shared_with: gr.Textbox | None,
    special_rules_state: gr.State | None,
    scenography_state: gr.State | None,
    deployment_zones_state: gr.State | None,
    objective_points_state: gr.State | None,
    svg_preview: gr.HTML | None,
    output: gr.JSON | None,
    # Dropdowns, toggles, and groups for shape sections
    deployment_zones_list: gr.Dropdown | None = None,
    deployment_zones_toggle: gr.Checkbox | None = None,
    zones_group: gr.Group | None = None,
    objective_points_list: gr.Dropdown | None = None,
    objective_points_toggle: gr.Checkbox | None = None,
    objective_points_group: gr.Group | None = None,
    scenography_list: gr.Dropdown | None = None,
    scenography_toggle: gr.Checkbox | None = None,
    scenography_group: gr.Group | None = None,
    # VP section
    vp_list: gr.Dropdown | None = None,
    vp_group: gr.Group | None = None,
    # Special rules section
    rules_list: gr.Dropdown | None = None,
    special_rules_toggle: gr.Checkbox | None = None,
    rules_group: gr.Group | None = None,
) -> None:
    """Wire the Edit button to populate Create form and navigate there."""

    # Collect all outputs that will be populated
    _form_outputs: list[gr.components.Component] = [
        page_state,
        *page_containers,
        editing_card_id,
        create_heading_md,
        scenario_name,
        mode,
        is_replicable,
        armies,
    ]
    # Optional form fields
    _opt: list[gr.components.Component | None] = [
        table_preset,
        deployment,
        layout,
        objectives,
        initial_priority,
        objectives_with_vp_toggle,
        vp_state,
        visibility,
        shared_with,
        special_rules_state,
        scenography_state,
        deployment_zones_state,
        objective_points_state,
        svg_preview,
        output,
        # Dropdowns, toggles, groups
        deployment_zones_list,
        deployment_zones_toggle,
        zones_group,
        objective_points_list,
        objective_points_toggle,
        objective_points_group,
        scenography_list,
        scenography_toggle,
        scenography_group,
        # VP section
        vp_list,
        vp_group,
        # Special rules section
        rules_list,
        special_rules_toggle,
        rules_group,
    ]
    _all_outputs = _form_outputs + [c for c in _opt if c is not None]

    def _go_edit_form(card_id: str) -> tuple:  # noqa: C901
        """Fetch card data and navigate to Create page in edit mode."""
        # Navigate to EDIT page (shows create_container via page_visibility)
        nav = navigate_to(PAGE_EDIT)

        if not card_id:
            # No card selected — just navigate with defaults
            return (
                *nav,  # page_state + visibilities
                "",  # editing_card_id
                "## Create New Scenario",
                "",
                "casual",
                True,
                "",  # name, mode, is_replicable, armies
                *([gr.update()] * len([c for c in _opt if c is not None])),
            )

        card_data, svg_wrapped = fetch_card_and_svg(card_id)
        if card_data.get("status") == "error":
            return (
                *nav,
                "",
                "## Create New Scenario",
                "",
                "casual",
                True,
                "",
                *([gr.update()] * len([c for c in _opt if c is not None])),
            )

        name = card_data.get("name", "")
        heading = f"## Edit: {escape_html(name)}" if name else "## Edit Scenario"

        # Extract objectives components
        obj_raw = card_data.get("objectives")
        obj_text, vp_enabled, vp_items = _extract_objectives_text_for_form(obj_raw)

        # Extract special rules
        rules_raw = card_data.get("special_rules")
        rules_state_val = (
            _api_special_rules_to_state(rules_raw)
            if isinstance(rules_raw, list) and rules_raw
            else []
        )

        # Extract shapes from card data
        shapes = card_data.get("shapes", {})
        if not isinstance(shapes, dict):
            shapes = {}
        scen_specs = shapes.get("scenography_specs", [])
        depl_shapes = shapes.get("deployment_shapes", [])
        obj_shapes = shapes.get("objective_shapes", [])

        # Shared with
        shared_list = card_data.get("shared_with", [])
        shared_val = ", ".join(shared_list) if isinstance(shared_list, list) else ""

        # Build the full return tuple
        values: list[Any] = [
            *nav,  # navigation
            card_id,  # editing_card_id
            heading,  # create_heading_md
            gr.update(value=name or ""),  # scenario_name
            gr.update(value=card_data.get("mode", "casual")),  # mode
            gr.update(value=card_data.get("is_replicable", True)),  # is_replicable
            gr.update(value=card_data.get("armies", "") or ""),  # armies
        ]
        # Optional fields (must match _opt order)
        opt_values: list[Any] = []
        if table_preset is not None:
            opt_values.append(
                gr.update(value=card_data.get("table_preset", "standard"))
            )
        if deployment is not None:
            opt_values.append(gr.update(value=card_data.get("deployment", "") or ""))
        if layout is not None:
            opt_values.append(gr.update(value=card_data.get("layout", "") or ""))
        if objectives is not None:
            opt_values.append(gr.update(value=obj_text))
        if initial_priority is not None:
            opt_values.append(
                gr.update(value=card_data.get("initial_priority", "") or "")
            )
        if objectives_with_vp_toggle is not None:
            opt_values.append(gr.update(value=vp_enabled))
        if vp_state is not None:
            opt_values.append(vp_items)
        if visibility is not None:
            opt_values.append(gr.update(value=card_data.get("visibility", "public")))
        if shared_with is not None:
            opt_values.append(gr.update(value=shared_val))
        if special_rules_state is not None:
            opt_values.append(rules_state_val)

        # Convert API shapes to UI state format
        scen_state_val: list[dict[str, Any]] = (
            _api_scenography_to_state(scen_specs) if scen_specs else []
        )
        depl_state_val: list[dict[str, Any]] = (
            _api_deployment_to_state(depl_shapes) if depl_shapes else []
        )
        obj_state_val: list[dict[str, Any]] = (
            _api_objectives_to_state(obj_shapes) if obj_shapes else []
        )

        if scenography_state is not None:
            opt_values.append(scen_state_val)
        if deployment_zones_state is not None:
            opt_values.append(depl_state_val)
        if objective_points_state is not None:
            opt_values.append(obj_state_val)
        if svg_preview is not None:
            opt_values.append(gr.update(value=svg_wrapped))
        if output is not None:
            opt_values.append(gr.update(value=None))

        # -- Dropdowns, toggles, and groups for shape sections --
        if deployment_zones_list is not None:
            choices = get_deployment_zones_choices(depl_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if deployment_zones_toggle is not None:
            has_depl = bool(depl_shapes)
            opt_values.append(gr.update(value=has_depl))
        if zones_group is not None:
            opt_values.append(gr.update(visible=bool(depl_shapes)))
        if objective_points_list is not None:
            choices = get_objective_points_choices(obj_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if objective_points_toggle is not None:
            has_obj = bool(obj_shapes)
            opt_values.append(gr.update(value=has_obj))
        if objective_points_group is not None:
            opt_values.append(gr.update(visible=bool(obj_shapes)))
        if scenography_list is not None:
            choices = get_scenography_choices(scen_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if scenography_toggle is not None:
            has_scen = bool(scen_specs)
            opt_values.append(gr.update(value=has_scen))
        if scenography_group is not None:
            opt_values.append(gr.update(visible=bool(scen_specs)))

        # -- Dropdowns, toggles, and groups for VP / special rules --
        if vp_list is not None:
            choices = get_victory_points_choices(vp_items)
            opt_values.append(gr.update(choices=choices, value=None))
        if vp_group is not None:
            opt_values.append(gr.update(visible=vp_enabled))
        if rules_list is not None:
            choices = get_special_rules_choices(rules_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if special_rules_toggle is not None:
            opt_values.append(gr.update(value=bool(rules_state_val)))
        if rules_group is not None:
            opt_values.append(gr.update(visible=bool(rules_state_val)))

        values.extend(opt_values)
        return tuple(values)

    detail_edit_btn.click(
        fn=_go_edit_form,
        inputs=[detail_card_id_state],
        outputs=_all_outputs,
    )

    # ── F5 edit restore: when editing_reload_trigger fires, repopulate
    # the form from editing_card_id (set by _check_auth on page load).
    if editing_reload_trigger is not None:

        def _reload_edit_form(_trigger: int, card_id: str) -> tuple:
            """Repopulate edit form from card_id on page reload (F5)."""
            if not card_id:
                return tuple(gr.update() for _ in _all_outputs)
            return _go_edit_form(card_id)

        editing_reload_trigger.change(
            fn=_reload_edit_form,
            inputs=[editing_reload_trigger, editing_card_id],
            outputs=_all_outputs,
        )
