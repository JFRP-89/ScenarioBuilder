"""Generate-button and create-scenario event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services.generate import (
    handle_create_scenario,
    handle_preview,
    handle_update_scenario,
)
from adapters.ui_gradio.ui.components.svg_preview import (
    _PLACEHOLDER_HTML,
    render_svg_from_card,
)
from adapters.ui_gradio.ui.router import PAGE_HOME, navigate_to
from adapters.ui_gradio.ui.wiring.wire_home import load_recent_cards


def wire_generate(
    *,
    actor_id: gr.Textbox,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    seed: gr.Number,
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

    def _preview_and_render(
        *args: Any,
    ) -> tuple[dict[str, Any], str]:
        """Validate form, build preview card, and render SVG locally."""
        preview_data = handle_preview(*args)
        svg_html = render_svg_from_card(preview_data)
        return preview_data, svg_html

    generate_btn.click(
        fn=_preview_and_render,
        inputs=[
            actor_id,
            scenario_name,
            mode,
            seed,
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
        outputs=[output, svg_preview],
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
            create_scenario_btn=create_scenario_btn,
            create_scenario_status=create_scenario_status,
            svg_preview=svg_preview,
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home_recent_html,
            # Form fields for reset
            scenario_name=scenario_name,
            mode=mode,
            seed=seed,
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


def _wire_create_scenario(  # noqa: C901
    *,
    output: gr.JSON,
    create_scenario_btn: gr.Button,
    create_scenario_status: gr.Textbox,
    svg_preview: gr.HTML,
    page_state: gr.State,
    page_containers: list[gr.Column],
    home_recent_html: gr.HTML,
    # Form fields for reset
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    seed: gr.Number,
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
        seed,
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

        def _stay(msg: str) -> tuple[Any, ...]:
            """Stay on the current page, show error status."""
            n_nav = 1 + len(page_containers)
            nav_noop = [gr.update()] * n_nav
            form_noop = [gr.update()] * n_form
            dropdowns_noop = [gr.update()] * n_dropdowns
            extra_noop = [gr.update()] * n_extra
            return (
                *nav_noop,
                gr.update(),  # home_recent_html
                *form_noop,
                *dropdowns_noop,
                *extra_noop,
                gr.update(value=msg, visible=True),
            )

        # --- Validation ---
        if not preview_data or not isinstance(preview_data, dict):
            return _stay("Generate a card preview first.")

        if preview_data.get("status") == "error":
            return _stay(f"Error: {preview_data.get('message', 'Generation failed')}")

        if preview_data.get("status") != "preview":
            return _stay("Generate a card preview first.")

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

        # Form resets
        form_resets: list[Any] = [
            gr.update(value=""),  # scenario_name
            gr.update(value="casual"),  # mode
            gr.update(value=1),  # seed
            gr.update(value=""),  # armies
            gr.update(value=""),  # deployment
            gr.update(value=""),  # layout
            gr.update(value=""),  # objectives
            gr.update(value=""),  # initial_priority
            gr.update(value="public"),  # visibility
            gr.update(value=""),  # shared_with
            [],  # special_rules_state
            gr.update(value=False),  # objectives_with_vp_toggle
            [],  # vp_state
            [],  # scenography_state
            [],  # deployment_zones_state
            [],  # objective_points_state
            gr.update(value=_PLACEHOLDER_HTML),  # svg_preview
            gr.update(value=None),  # output
        ]
        dropdown_resets: list[Any] = [
            (
                gr.update(value="")
                if isinstance(c, gr.Textbox)
                else gr.update(value=None, choices=[])
            )
            for c in _dropdown_lists
        ]

        # Reset edit mode state
        extra_resets: list[Any] = []
        if editing_card_id is not None:
            extra_resets.append("")  # clear editing_card_id
        if create_heading_md is not None:
            extra_resets.append(gr.update(value="## Create New Scenario"))

        return (
            *nav,
            recent_html,
            *form_resets,
            *dropdown_resets,
            *extra_resets,
            gr.update(value=status_msg, visible=True),
        )

    # Build inputs — output always, plus editing_card_id if available
    _inputs: list[gr.components.Component] = [output]
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
