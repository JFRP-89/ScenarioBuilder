"""Generate-button and create-scenario event wiring.

Facade — delegates to ``_generate/`` sub-modules for testability.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services.generate import (
    handle_create_scenario,
    handle_update_scenario,
)
from adapters.ui_gradio.ui.router import PAGE_HOME, navigate_to
from adapters.ui_gradio.ui.wiring._generate._create_logic import validate_preview_data
from adapters.ui_gradio.ui.wiring._generate._outputs import build_stay_outputs
from adapters.ui_gradio.ui.wiring._generate._preview import preview_and_render
from adapters.ui_gradio.ui.wiring._generate._resets import (
    build_dropdown_resets,
    build_extra_resets,
    build_form_resets,
)
from adapters.ui_gradio.ui.wiring.wire_home import load_recent_cards


def wire_generate(
    *,
    actor_id: gr.Textbox,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    is_replicable: gr.Checkbox,
    generate_from_seed: gr.Number,
    armies: gr.Textbox,
    table_preset: gr.Radio,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    deployment: gr.Textbox,
    layout: gr.Textbox,
    objectives: gr.Textbox,
    initial_priority: gr.Textbox,
    special_rules_state: gr.State,
    visibility: gr.Radio,
    shared_with: gr.Textbox,
    scenography_state: gr.State,
    deployment_zones_state: gr.State,
    objective_points_state: gr.State,
    objectives_with_vp_toggle: gr.Checkbox,
    vp_state: gr.State,
    generate_btn: gr.Button,
    svg_preview: gr.HTML,
    output: gr.JSON,
    preview_full_state: gr.State,
    create_scenario_btn: gr.Button | None = None,
    create_scenario_status: gr.Textbox | None = None,
    # Navigation widgets (needed to go Home after create)
    page_state: gr.State | None = None,
    page_containers: list[gr.Column] | None = None,
    home_recent_html: gr.HTML | None = None,
    # Form components for reset after successful create
    vp_input: gr.Textbox | None = None,
    vp_list: gr.Dropdown | None = None,
    rules_list: gr.Dropdown | None = None,
    scenography_list: gr.Dropdown | None = None,
    deployment_zones_list: gr.Dropdown | None = None,
    objective_points_list: gr.Dropdown | None = None,
    # Edit mode state
    editing_card_id: gr.State | None = None,
    create_heading_md: gr.Markdown | None = None,
) -> None:
    """Wire generate-preview button and create-scenario confirmation."""

    # -- Preview (no API call) ------------------------------------------

    # Build outputs: always include core 3, plus shape state/dropdown when available
    preview_outputs: list[gr.components.Component] = [
        output,
        svg_preview,
        preview_full_state,
    ]
    # Shape state + dropdown outputs (positions 3-8 in the return tuple)
    _shape_outputs: list[gr.components.Component | None] = [
        deployment_zones_state,
        deployment_zones_list,
        objective_points_state,
        objective_points_list,
        scenography_state,
        scenography_list,
    ]
    for comp in _shape_outputs:
        if comp is not None:
            preview_outputs.append(comp)

    generate_btn.click(
        fn=preview_and_render,
        inputs=[
            actor_id,
            scenario_name,
            mode,
            is_replicable,
            generate_from_seed,
            armies,
            table_preset,
            table_width,
            table_height,
            table_unit,
            deployment,
            layout,
            objectives,
            initial_priority,
            special_rules_state,
            visibility,
            shared_with,
            scenography_state,
            deployment_zones_state,
            objective_points_state,
            objectives_with_vp_toggle,
            vp_state,
        ],
        outputs=preview_outputs,
    )

    # -- Create Scenario (calls API + resets form) ----------------------
    if (
        create_scenario_btn is not None
        and create_scenario_status is not None
        and page_state is not None
        and page_containers is not None
        and home_recent_html is not None
    ):
        _wire_create_scenario(
            output=output,
            preview_full_state=preview_full_state,
            create_scenario_btn=create_scenario_btn,
            create_scenario_status=create_scenario_status,
            svg_preview=svg_preview,
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home_recent_html,
            # Form fields for reset
            scenario_name=scenario_name,
            mode=mode,
            is_replicable=is_replicable,
            generate_from_seed=generate_from_seed,
            armies=armies,
            deployment=deployment,
            layout=layout,
            objectives=objectives,
            initial_priority=initial_priority,
            visibility=visibility,
            shared_with=shared_with,
            special_rules_state=special_rules_state,
            objectives_with_vp_toggle=objectives_with_vp_toggle,
            vp_state=vp_state,
            scenography_state=scenography_state,
            deployment_zones_state=deployment_zones_state,
            objective_points_state=objective_points_state,
            vp_input=vp_input,
            vp_list=vp_list,
            rules_list=rules_list,
            scenography_list=scenography_list,
            deployment_zones_list=deployment_zones_list,
            objective_points_list=objective_points_list,
            editing_card_id=editing_card_id,
            create_heading_md=create_heading_md,
        )


def _wire_create_scenario(
    *,
    output: gr.JSON,
    preview_full_state: gr.State,
    create_scenario_btn: gr.Button,
    create_scenario_status: gr.Textbox,
    svg_preview: gr.HTML,
    page_state: gr.State,
    page_containers: list[gr.Column],
    home_recent_html: gr.HTML,
    # Form fields for reset
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    is_replicable: gr.Checkbox,
    generate_from_seed: gr.Number,
    armies: gr.Textbox,
    deployment: gr.Textbox,
    layout: gr.Textbox,
    objectives: gr.Textbox,
    initial_priority: gr.Textbox,
    visibility: gr.Radio,
    shared_with: gr.Textbox,
    special_rules_state: gr.State,
    objectives_with_vp_toggle: gr.Checkbox,
    vp_state: gr.State,
    scenography_state: gr.State,
    deployment_zones_state: gr.State,
    objective_points_state: gr.State,
    vp_input: gr.Textbox | None,
    vp_list: gr.Dropdown | None,
    rules_list: gr.Dropdown | None,
    scenography_list: gr.Dropdown | None,
    deployment_zones_list: gr.Dropdown | None,
    objective_points_list: gr.Dropdown | None,
    # Edit mode
    editing_card_id: gr.State | None = None,
    create_heading_md: gr.Markdown | None = None,
) -> None:
    """Wire the Create / Update Scenario button.

    In create mode (editing_card_id is empty): POST /cards.
    In edit mode (editing_card_id is set): PUT /cards/<card_id>.
    On success, resets the entire form and navigates to Home.
    """

    # Collect all resettable form components
    _form_components: list[gr.components.Component] = [
        scenario_name,
        mode,
        is_replicable,
        generate_from_seed,
        armies,
        deployment,
        layout,
        objectives,
        initial_priority,
        visibility,
        shared_with,
        special_rules_state,
        objectives_with_vp_toggle,
        vp_state,
        scenography_state,
        deployment_zones_state,
        objective_points_state,
        svg_preview,
        output,
    ]
    _dropdown_lists: list[gr.components.Component] = [
        c
        for c in [
            vp_input,
            vp_list,
            rules_list,
            scenography_list,
            deployment_zones_list,
            objective_points_list,
        ]
        if c is not None
    ]

    # Extra outputs for edit mode
    _extra_outputs: list[gr.components.Component] = []
    if editing_card_id is not None:
        _extra_outputs.append(editing_card_id)
    if create_heading_md is not None:
        _extra_outputs.append(create_heading_md)

    def _on_create_scenario(preview_data: Any, edit_id: str = "") -> Any:
        n_form = len(_form_components)
        n_dropdowns = len(_dropdown_lists)
        n_extra = len(_extra_outputs)
        n_nav = 1 + len(page_containers)

        def _stay(msg: str) -> tuple[Any, ...]:
            """Stay on the current page, show error status."""
            return build_stay_outputs(  # type: ignore[no-any-return]
                msg,
                n_nav=n_nav,
                n_form=n_form,
                n_dropdowns=n_dropdowns,
                n_extra=n_extra,
            )

        # --- Validation ---
        ok, err_msg = validate_preview_data(preview_data)
        if not ok:
            return _stay(err_msg)

        # --- Call API: PUT for edit, POST for create ---
        is_edit = bool(edit_id)
        if is_edit:
            result = handle_update_scenario(preview_data, edit_id)
        else:
            result = handle_create_scenario(preview_data)

        if result.get("status") == "error":
            return _stay(f"API Error: {result.get('message', 'Unknown error')}")

        card_id = result.get("card_id", "")
        if is_edit:
            status_msg = f"Scenario updated! ID: {card_id}"
        else:
            status_msg = f"Scenario created! ID: {card_id}"

        # --- Success: navigate home + reset form ---
        nav = navigate_to(PAGE_HOME)  # (page_state, *visibilities)
        recent_html = load_recent_cards()

        form_resets = build_form_resets()
        dropdown_resets = build_dropdown_resets(_dropdown_lists)
        extra_resets = build_extra_resets(
            has_editing_card_id=editing_card_id is not None,
            has_create_heading_md=create_heading_md is not None,
        )

        return (
            *nav,
            recent_html,
            *form_resets,
            *dropdown_resets,
            *extra_resets,
            gr.update(value=status_msg, visible=True),
        )

    # Build inputs — preview_full_state always (contains _payload and _actor_id),
    # plus editing_card_id if available
    _inputs: list[gr.components.Component] = [preview_full_state]
    if editing_card_id is not None:
        _inputs.append(editing_card_id)

    _outputs = [
        page_state,
        *page_containers,
        home_recent_html,
        *_form_components,
        *_dropdown_lists,
        *_extra_outputs,
        create_scenario_status,
    ]

    create_scenario_btn.click(
        fn=_on_create_scenario,
        inputs=_inputs,
        outputs=_outputs,
    )
