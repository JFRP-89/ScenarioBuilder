"""Objective-points section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.state_helpers import (
    add_objective_point,
    get_objective_points_choices,
    remove_last_objective_point,
    remove_selected_objective_point,
)
from adapters.ui_gradio.units import convert_to_cm


def wire_objectives(
    *,
    objective_points_toggle: gr.Checkbox,
    objective_points_group: gr.Group,
    objective_points_state: gr.State,
    objective_description: gr.Textbox,
    objective_cx_input: gr.Number,
    objective_cy_input: gr.Number,
    add_objective_btn: gr.Button,
    objective_points_list: gr.Dropdown,
    remove_last_objective_btn: gr.Button,
    remove_selected_objective_btn: gr.Button,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    output: gr.JSON,
) -> None:
    """Wire objective-point add/remove events."""

    # -- closures ----------------------------------------------------------

    def _add_objective_point_wrapper(
        desc: str,
        cx: float,
        cy: float,
        current_state: list[dict[str, Any]],
        tw: float,
        th: float,
        tu: str,
    ) -> dict[str, Any]:
        description_stripped = (desc or "").strip()
        if not description_stripped:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Objective Point requires Description to be filled.",
                },
            }
        if cx is None or cx < 0:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Objective Point requires X Coordinate >= 0.",
                },
            }
        if cy is None or cy < 0:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Objective Point requires Y Coordinate >= 0.",
                },
            }
        table_width_mm = int(convert_to_cm(tw, tu) * 10)
        table_height_mm = int(convert_to_cm(th, tu) * 10)
        new_state, error = add_objective_point(
            current_state,
            cx,
            cy,
            table_width_mm,
            table_height_mm,
            description_stripped,
        )
        if error:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                output: {"status": "error", "message": error},
            }
        choices = get_objective_points_choices(new_state)
        dropdown_value = new_state[0]["id"] if new_state else ""
        return {
            objective_points_state: new_state,
            objective_points_list: gr.update(choices=choices, value=dropdown_value),
            output: {"status": "success"},
        }

    def _remove_last_objective_point_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[str, Any]:
        new_state = remove_last_objective_point(current_state)
        choices = get_objective_points_choices(new_state)
        dropdown_value = new_state[0]["id"] if new_state else ""
        return {
            objective_points_state: new_state,
            objective_points_list: gr.update(choices=choices, value=dropdown_value),
        }

    def _remove_selected_objective_point_wrapper(
        selected_id: str,
        current_state: list[dict[str, Any]],
    ) -> dict[str, Any]:
        new_state = remove_selected_objective_point(current_state, selected_id)
        choices = get_objective_points_choices(new_state)
        dropdown_value = new_state[0]["id"] if new_state else ""
        return {
            objective_points_state: new_state,
            objective_points_list: gr.update(choices=choices, value=dropdown_value),
        }

    # -- bindings ----------------------------------------------------------

    add_objective_btn.click(
        fn=_add_objective_point_wrapper,
        inputs=[
            objective_description,
            objective_cx_input,
            objective_cy_input,
            objective_points_state,
            table_width,
            table_height,
            table_unit,
        ],
        outputs=[objective_points_state, objective_points_list, output],
    )
    remove_last_objective_btn.click(
        fn=_remove_last_objective_point_wrapper,
        inputs=[objective_points_state],
        outputs=[objective_points_state, objective_points_list],
    )
    remove_selected_objective_btn.click(
        fn=_remove_selected_objective_point_wrapper,
        inputs=[objective_points_list, objective_points_state],
        outputs=[objective_points_state, objective_points_list],
    )

    # Wire toggle for Objective Points section
    def _toggle_objective_points(enabled: bool) -> Any:
        return handlers.toggle_objective_points_section(enabled)

    objective_points_toggle.change(
        fn=_toggle_objective_points,
        inputs=[objective_points_toggle],
        outputs=[objective_points_group],
    )
