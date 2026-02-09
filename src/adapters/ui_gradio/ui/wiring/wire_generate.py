"""Generate-button and create-scenario event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.services.generate import handle_generate
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.svg_preview import render_svg_from_card
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
) -> None:
    """Wire generate button click and create-scenario confirmation."""

    def _generate_and_render(
        *args: Any,
    ) -> tuple[dict[str, Any], str]:
        """Generate card and render SVG preview."""
        card_data = handle_generate(*args)
        svg_html = render_svg_from_card(card_data)
        return card_data, svg_html

    generate_btn.click(
        fn=_generate_and_render,
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

    # ── Create Scenario (verify card persisted in Flask) ─────────
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
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home_recent_html,
        )


def _wire_create_scenario(
    *,
    output: gr.JSON,
    create_scenario_btn: gr.Button,
    create_scenario_status: gr.Textbox,
    page_state: gr.State,
    page_containers: list[gr.Column],
    home_recent_html: gr.HTML,
) -> None:
    """Wire the Create Scenario button.

    Reads the generated card JSON, verifies it exists in Flask memory
    via GET /cards/<card_id>, and on success navigates to Home page
    with a refreshed recent-cards list.
    """

    def _on_create_scenario(card_data: Any) -> Any:
        # Error branches: stay on Create page, show status only
        if not card_data or not isinstance(card_data, dict):
            stay = [gr.update()] * (2 + len(page_containers))
            return (*stay, gr.update(value="Generate a card first.", visible=True))

        if card_data.get("status") == "error":
            msg = card_data.get("message", "Generation failed")
            stay = [gr.update()] * (2 + len(page_containers))
            return (*stay, gr.update(value=f"Error: {msg}", visible=True))

        card_id = card_data.get("card_id")
        if not card_id:
            stay = [gr.update()] * (2 + len(page_containers))
            return (
                *stay,
                gr.update(
                    value="No card_id found. Generate a card first.", visible=True
                ),
            )

        # Verify the card is persisted in Flask memory
        default_actor = get_default_actor_id()
        result = nav_svc.get_card(default_actor, str(card_id))

        if result.get("status") == "error":
            stay = [gr.update()] * (2 + len(page_containers))
            return (
                *stay,
                gr.update(
                    value=(
                        f"Could not verify card in Flask: "
                        f"{result.get('message', 'unknown error')}"
                    ),
                    visible=True,
                ),
            )

        # Success → navigate to Home + refresh recent cards
        nav = navigate_to(PAGE_HOME)  # (page_state, *visibilities)
        recent_html = load_recent_cards()
        status = gr.update(
            value=f"Scenario created! ID: {card_id}",
            visible=True,
        )
        # outputs: page_state, *page_containers, home_recent_html, status
        return (*nav, recent_html, status)

    create_scenario_btn.click(
        fn=_on_create_scenario,
        inputs=[output],
        outputs=[
            page_state,
            *page_containers,
            home_recent_html,
            create_scenario_status,
        ],
    )
