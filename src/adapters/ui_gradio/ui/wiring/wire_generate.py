"""Generate-button and create-scenario event wiring.

Facade — delegates to ``_generate/`` sub-modules for testability.
"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class GenerateCtx:
    """Widget references for generate/create-scenario wiring."""

    actor_id: gr.Textbox
    scenario_name: gr.Textbox
    mode: gr.Radio
    is_replicable: gr.Checkbox
    generate_from_seed: gr.Number
    armies: gr.Textbox
    table_preset: gr.Radio
    table_width: gr.Number
    table_height: gr.Number
    table_unit: gr.Radio
    deployment: gr.Textbox
    layout: gr.Textbox
    objectives: gr.Textbox
    initial_priority: gr.Textbox
    special_rules_state: gr.State
    visibility: gr.Radio
    shared_with: gr.Textbox
    scenography_state: gr.State
    deployment_zones_state: gr.State
    objective_points_state: gr.State
    objectives_with_vp_toggle: gr.Checkbox
    vp_state: gr.State
    generate_btn: gr.Button
    svg_preview: gr.HTML
    output: gr.JSON
    preview_full_state: gr.State
    create_scenario_btn: gr.Button | None = None
    create_scenario_status: gr.Textbox | None = None
    page_state: gr.State | None = None
    page_containers: list[gr.Column] | None = None
    home_recent_html: gr.HTML | None = None
    home_page_info: gr.HTML | None = None
    home_page_state: gr.State | None = None
    home_cards_cache_state: gr.State | None = None
    home_fav_ids_cache_state: gr.State | None = None
    vp_input: gr.Textbox | None = None
    vp_list: gr.Dropdown | None = None
    rules_list: gr.Dropdown | None = None
    scenography_list: gr.Dropdown | None = None
    deployment_zones_list: gr.Dropdown | None = None
    objective_points_list: gr.Dropdown | None = None
    editing_card_id: gr.Textbox | None = None
    create_heading_md: gr.Markdown | None = None


@dataclass(frozen=True)
class _CreateScenarioCtx:
    """Widget references for the create/update scenario button wiring."""

    output: gr.JSON
    preview_full_state: gr.State
    create_scenario_btn: gr.Button
    create_scenario_status: gr.Textbox
    svg_preview: gr.HTML
    page_state: gr.State
    page_containers: list[gr.Column]
    home_recent_html: gr.HTML
    scenario_name: gr.Textbox
    mode: gr.Radio
    is_replicable: gr.Checkbox
    generate_from_seed: gr.Number
    armies: gr.Textbox
    deployment: gr.Textbox
    layout: gr.Textbox
    objectives: gr.Textbox
    initial_priority: gr.Textbox
    visibility: gr.Radio
    shared_with: gr.Textbox
    special_rules_state: gr.State
    objectives_with_vp_toggle: gr.Checkbox
    vp_state: gr.State
    scenography_state: gr.State
    deployment_zones_state: gr.State
    objective_points_state: gr.State
    home_page_info: gr.HTML | None = None
    home_page_state: gr.State | None = None
    home_cards_cache_state: gr.State | None = None
    home_fav_ids_cache_state: gr.State | None = None
    vp_input: gr.Textbox | None = None
    vp_list: gr.Dropdown | None = None
    rules_list: gr.Dropdown | None = None
    scenography_list: gr.Dropdown | None = None
    deployment_zones_list: gr.Dropdown | None = None
    objective_points_list: gr.Dropdown | None = None
    editing_card_id: gr.Textbox | None = None
    create_heading_md: gr.Markdown | None = None


def wire_generate(*, ctx: GenerateCtx) -> None:
    """Wire generate-preview button and create-scenario confirmation."""
    c = ctx

    # -- Preview (no API call) ------------------------------------------

    # Build outputs: always include core 3, plus shape state/dropdown when available
    preview_outputs: list[gr.components.Component] = [
        c.output,
        c.svg_preview,
        c.preview_full_state,
    ]
    # Shape state + dropdown outputs (positions 3-8 in the return tuple)
    _shape_outputs: list[gr.components.Component | None] = [
        c.deployment_zones_state,
        c.deployment_zones_list,
        c.objective_points_state,
        c.objective_points_list,
        c.scenography_state,
        c.scenography_list,
    ]
    for comp in _shape_outputs:
        if comp is not None:
            preview_outputs.append(comp)

    c.generate_btn.click(
        fn=preview_and_render,
        inputs=[
            c.actor_id,
            c.scenario_name,
            c.mode,
            c.is_replicable,
            c.generate_from_seed,
            c.armies,
            c.table_preset,
            c.table_width,
            c.table_height,
            c.table_unit,
            c.deployment,
            c.layout,
            c.objectives,
            c.initial_priority,
            c.special_rules_state,
            c.visibility,
            c.shared_with,
            c.scenography_state,
            c.deployment_zones_state,
            c.objective_points_state,
            c.objectives_with_vp_toggle,
            c.vp_state,
        ],
        outputs=preview_outputs,
    )

    # -- Create Scenario (calls API + resets form) ----------------------
    if (
        c.create_scenario_btn is not None
        and c.create_scenario_status is not None
        and c.page_state is not None
        and c.page_containers is not None
        and c.home_recent_html is not None
    ):
        _wire_create_scenario(
            ctx=_CreateScenarioCtx(
                output=c.output,
                preview_full_state=c.preview_full_state,
                create_scenario_btn=c.create_scenario_btn,
                create_scenario_status=c.create_scenario_status,
                svg_preview=c.svg_preview,
                page_state=c.page_state,
                page_containers=c.page_containers,
                home_recent_html=c.home_recent_html,
                home_page_info=c.home_page_info,
                home_page_state=c.home_page_state,
                home_cards_cache_state=c.home_cards_cache_state,
                home_fav_ids_cache_state=c.home_fav_ids_cache_state,
                scenario_name=c.scenario_name,
                mode=c.mode,
                is_replicable=c.is_replicable,
                generate_from_seed=c.generate_from_seed,
                armies=c.armies,
                deployment=c.deployment,
                layout=c.layout,
                objectives=c.objectives,
                initial_priority=c.initial_priority,
                visibility=c.visibility,
                shared_with=c.shared_with,
                special_rules_state=c.special_rules_state,
                objectives_with_vp_toggle=c.objectives_with_vp_toggle,
                vp_state=c.vp_state,
                scenography_state=c.scenography_state,
                deployment_zones_state=c.deployment_zones_state,
                objective_points_state=c.objective_points_state,
                vp_input=c.vp_input,
                vp_list=c.vp_list,
                rules_list=c.rules_list,
                scenography_list=c.scenography_list,
                deployment_zones_list=c.deployment_zones_list,
                objective_points_list=c.objective_points_list,
                editing_card_id=c.editing_card_id,
                create_heading_md=c.create_heading_md,
            )
        )


def _wire_create_scenario(  # noqa: C901
    *,
    ctx: _CreateScenarioCtx,
) -> None:
    """Wire the Create / Update Scenario button.

    In create mode (editing_card_id is empty): POST /cards.
    In edit mode (editing_card_id is set): PUT /cards/<card_id>.
    On success, resets the entire form and navigates to Home.
    """
    c = ctx

    # Collect all resettable form components
    _form_components: list[gr.components.Component] = [
        c.scenario_name,
        c.mode,
        c.is_replicable,
        c.generate_from_seed,
        c.armies,
        c.deployment,
        c.layout,
        c.objectives,
        c.initial_priority,
        c.visibility,
        c.shared_with,
        c.special_rules_state,
        c.objectives_with_vp_toggle,
        c.vp_state,
        c.scenography_state,
        c.deployment_zones_state,
        c.objective_points_state,
        c.svg_preview,
        c.output,
    ]
    _dropdown_lists: list[gr.components.Component] = [
        w
        for w in [
            c.vp_input,
            c.vp_list,
            c.rules_list,
            c.scenography_list,
            c.deployment_zones_list,
            c.objective_points_list,
        ]
        if w is not None
    ]

    # Extra outputs for edit mode
    _extra_outputs: list[gr.components.Component] = []
    if c.editing_card_id is not None:
        _extra_outputs.append(c.editing_card_id)
    if c.create_heading_md is not None:
        _extra_outputs.append(c.create_heading_md)
    _extra_outputs.append(c.create_scenario_btn)

    # Additional home-page outputs (page_info, page/cache states)
    _home_extra_outputs: list[gr.components.Component] = [
        w
        for w in [
            c.home_page_info,
            c.home_page_state,
            c.home_cards_cache_state,
            c.home_fav_ids_cache_state,
        ]
        if w is not None
    ]

    def _on_create_scenario(preview_data: Any, edit_id: str = "") -> Any:
        n_form = len(_form_components)
        n_dropdowns = len(_dropdown_lists)
        n_extra = len(_extra_outputs)
        n_nav = 1 + len(c.page_containers)

        def _stay(msg: str) -> tuple[Any, ...]:
            """Stay on the current page, show error status."""
            return build_stay_outputs(
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
        nav = navigate_to(PAGE_HOME)

        form_resets = build_form_resets()
        dropdown_resets = build_dropdown_resets(_dropdown_lists)
        extra_resets = build_extra_resets(
            has_editing_card_id=c.editing_card_id is not None,
            has_create_heading_md=c.create_heading_md is not None,
            has_create_scenario_btn=True,
        )

        return (
            *nav,
            *form_resets,
            *dropdown_resets,
            *extra_resets,
            gr.update(value=status_msg, visible=True),
        )

    # Build inputs
    _inputs: list[gr.components.Component] = [c.preview_full_state]
    if c.editing_card_id is not None:
        _inputs.append(c.editing_card_id)

    _outputs = [
        c.page_state,
        *c.page_containers,
        *_form_components,
        *_dropdown_lists,
        *_extra_outputs,
        c.create_scenario_status,
    ]

    _home_all_outputs = [c.home_recent_html, *_home_extra_outputs]

    event = c.create_scenario_btn.click(
        fn=_on_create_scenario,
        inputs=_inputs,
        outputs=_outputs,
    )
    if _home_all_outputs:
        event.then(
            fn=load_recent_cards,
            inputs=[],
            outputs=_home_all_outputs,
        )
