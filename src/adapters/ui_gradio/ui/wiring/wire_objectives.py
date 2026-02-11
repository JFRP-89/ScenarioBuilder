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
    update_objective_point,
)
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
)


def wire_objectives(  # noqa: C901
    *,
    objective_points_toggle: gr.Checkbox,
    objective_points_group: gr.Group,
    objective_points_state: gr.State,
    objective_unit_state: gr.State,
    objective_description: gr.Textbox,
    objective_cx_input: gr.Number,
    objective_cy_input: gr.Number,
    objective_unit: gr.Radio,
    add_objective_btn: gr.Button,
    objective_points_list: gr.Dropdown,
    remove_last_objective_btn: gr.Button,
    remove_selected_objective_btn: gr.Button,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    objective_editing_state: gr.State,
    cancel_edit_objective_btn: gr.Button,
    output: gr.JSON,
) -> None:
    """Wire objective-point add/remove/edit events."""

    # -- closures ----------------------------------------------------------

    def _on_objective_selected(
        selected_id: str | None,
        current_state: list[dict[str, Any]],
        objective_unit_val: str,
    ) -> dict[str, Any]:
        """Populate form when an objective point is selected."""
        if not selected_id:
            return {
                objective_description: gr.update(value=""),
                objective_cx_input: gr.update(value=60),
                objective_cy_input: gr.update(value=60),
                objective_editing_state: None,
                add_objective_btn: gr.update(value="Add Objective Point"),
                cancel_edit_objective_btn: gr.update(visible=False),
            }
        point = next((p for p in current_state if p["id"] == selected_id), None)
        if not point:
            return {
                objective_description: gr.update(),
                objective_cx_input: gr.update(),
                objective_cy_input: gr.update(),
                objective_editing_state: None,
                add_objective_btn: gr.update(value="Add Objective Point"),
                cancel_edit_objective_btn: gr.update(visible=False),
            }
        # Convert mm to user display unit
        cx_cm = float(point["cx"]) / 10.0
        cy_cm = float(point["cy"]) / 10.0
        cx_display = convert_from_cm(cx_cm, objective_unit_val)
        cy_display = convert_from_cm(cy_cm, objective_unit_val)
        return {
            objective_description: gr.update(value=point.get("description", "")),
            objective_cx_input: gr.update(value=round(cx_display, 2)),
            objective_cy_input: gr.update(value=round(cy_display, 2)),
            objective_editing_state: selected_id,
            add_objective_btn: gr.update(value="✏️ Update Objective Point"),
            cancel_edit_objective_btn: gr.update(visible=True),
        }

    def _cancel_edit_objective() -> dict[str, Any]:
        """Cancel editing and return to add mode."""
        return {
            objective_description: gr.update(value=""),
            objective_cx_input: gr.update(value=60),
            objective_cy_input: gr.update(value=60),
            objective_editing_state: None,
            add_objective_btn: gr.update(value="Add Objective Point"),
            cancel_edit_objective_btn: gr.update(visible=False),
            objective_points_list: gr.update(value=None),
        }

    def _add_or_update_objective_point_wrapper(
        desc: str,
        cx: float,
        cy: float,
        current_state: list[dict[str, Any]],
        tw: float,
        th: float,
        tu: str,
        objective_unit_val: str,
        editing_id: str | None,
    ) -> dict[str, Any]:
        description_stripped = (desc or "").strip()
        if not description_stripped:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                objective_editing_state: editing_id,
                add_objective_btn: gr.update(),
                cancel_edit_objective_btn: gr.update(),
                output: {
                    "status": "error",
                    "message": "Objective Point requires Description to be filled.",
                },
            }
        if cx is None or cx < 0:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                objective_editing_state: editing_id,
                add_objective_btn: gr.update(),
                cancel_edit_objective_btn: gr.update(),
                output: {
                    "status": "error",
                    "message": "Objective Point requires X Coordinate >= 0.",
                },
            }
        if cy is None or cy < 0:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                objective_editing_state: editing_id,
                add_objective_btn: gr.update(),
                cancel_edit_objective_btn: gr.update(),
                output: {
                    "status": "error",
                    "message": "Objective Point requires Y Coordinate >= 0.",
                },
            }
        table_width_mm = int(convert_to_cm(tw, tu) * 10)
        table_height_mm = int(convert_to_cm(th, tu) * 10)
        cx_mm = int(convert_to_cm(cx, objective_unit_val) * 10)
        cy_mm = int(convert_to_cm(cy, objective_unit_val) * 10)

        if editing_id:
            new_state, error = update_objective_point(
                current_state,
                editing_id,
                cx_mm,
                cy_mm,
                table_width_mm,
                table_height_mm,
                description_stripped,
            )
        else:
            new_state, error = add_objective_point(
                current_state,
                cx_mm,
                cy_mm,
                table_width_mm,
                table_height_mm,
                description_stripped,
            )

        if error:
            return {
                objective_points_state: current_state,
                objective_points_list: gr.update(),
                objective_editing_state: editing_id,
                add_objective_btn: gr.update(),
                cancel_edit_objective_btn: gr.update(),
                output: {"status": "error", "message": error},
            }
        choices = get_objective_points_choices(new_state)
        return {
            objective_points_state: new_state,
            objective_points_list: gr.update(choices=choices, value=None),
            objective_editing_state: None,
            add_objective_btn: gr.update(value="Add Objective Point"),
            cancel_edit_objective_btn: gr.update(visible=False),
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
            objective_editing_state: None,
            add_objective_btn: gr.update(value="Add Objective Point"),
            cancel_edit_objective_btn: gr.update(visible=False),
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
            objective_editing_state: None,
            add_objective_btn: gr.update(value="Add Objective Point"),
            cancel_edit_objective_btn: gr.update(visible=False),
        }

    # -- bindings ----------------------------------------------------------

    _edit_outputs = [
        objective_description,
        objective_cx_input,
        objective_cy_input,
        objective_editing_state,
        add_objective_btn,
        cancel_edit_objective_btn,
    ]

    objective_points_list.change(
        fn=_on_objective_selected,
        inputs=[
            objective_points_list,
            objective_points_state,
            objective_unit,
        ],
        outputs=_edit_outputs,
    )

    cancel_edit_objective_btn.click(
        fn=_cancel_edit_objective,
        inputs=[],
        outputs=[*_edit_outputs, objective_points_list],
    )

    _add_update_outputs = [
        objective_points_state,
        objective_points_list,
        objective_editing_state,
        add_objective_btn,
        cancel_edit_objective_btn,
        output,
    ]

    add_objective_btn.click(
        fn=_add_or_update_objective_point_wrapper,
        inputs=[
            objective_description,
            objective_cx_input,
            objective_cy_input,
            objective_points_state,
            table_width,
            table_height,
            table_unit,
            objective_unit,
            objective_editing_state,
        ],
        outputs=_add_update_outputs,
    )

    _remove_outputs = [
        objective_points_state,
        objective_points_list,
        objective_editing_state,
        add_objective_btn,
        cancel_edit_objective_btn,
    ]

    remove_last_objective_btn.click(
        fn=_remove_last_objective_point_wrapper,
        inputs=[objective_points_state],
        outputs=_remove_outputs,
    )
    remove_selected_objective_btn.click(
        fn=_remove_selected_objective_point_wrapper,
        inputs=[objective_points_list, objective_points_state],
        outputs=_remove_outputs,
    )

    # Wire toggle for Objective Points section
    def _toggle_objective_points(enabled: bool) -> Any:
        return handlers.toggle_objective_points_section(enabled)

    objective_points_toggle.change(
        fn=_toggle_objective_points,
        inputs=[objective_points_toggle],
        outputs=[objective_points_group],
    )

    # Wire unit change for Objective Points
    def _on_objective_unit_change(
        new_unit: str, cx: float, cy: float, prev_unit: str
    ) -> tuple[float, float, str]:
        """Convert objective coordinates when unit changes."""
        if prev_unit == new_unit:
            return cx, cy, new_unit
        cx_converted = convert_unit_to_unit(cx, prev_unit, new_unit)
        cy_converted = convert_unit_to_unit(cy, prev_unit, new_unit)
        return cx_converted, cy_converted, new_unit

    objective_unit.change(
        fn=_on_objective_unit_change,
        inputs=[
            objective_unit,
            objective_cx_input,
            objective_cy_input,
            objective_unit_state,
        ],
        outputs=[objective_cx_input, objective_cy_input, objective_unit_state],
    )
