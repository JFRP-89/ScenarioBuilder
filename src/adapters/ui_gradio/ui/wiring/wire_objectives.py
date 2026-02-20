"""Objective-points section event wiring."""

from __future__ import annotations

from dataclasses import dataclass
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
    convert_unit_to_unit,
    to_mm,
)

_BTN_ADD_OBJECTIVE = "Add Objective Point"


def _validate_objective_inputs(
    desc: str,
    cx: float | None,
    cy: float | None,
) -> str | None:
    """Return an error message if inputs are invalid, else ``None``."""
    if not (desc or "").strip():
        return "Objective Point requires Description to be filled."
    if cx is None or cx < 0:
        return "Objective Point requires X Coordinate >= 0."
    if cy is None or cy < 0:
        return "Objective Point requires Y Coordinate >= 0."
    return None


def _apply_objective_mutation(
    desc: str,
    cx: float,
    cy: float,
    current_state: list[dict[str, Any]],
    editing_id: str | None,
    objective_unit_val: str,
    table_w_mm: int,
    table_h_mm: int,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Validate inputs and add/update objective point.

    Returns ``(new_state, error_msg)`` — *new_state* is ``None`` on error.
    """
    validation_err = _validate_objective_inputs(desc, cx, cy)
    if validation_err:
        return None, validation_err

    description_stripped = (desc or "").strip()
    cx_mm = to_mm(cx, objective_unit_val)
    cy_mm = to_mm(cy, objective_unit_val)

    if editing_id:
        new_state, error = update_objective_point(
            current_state,
            editing_id,
            cx_mm,
            cy_mm,
            table_w_mm,
            table_h_mm,
            description_stripped,
        )
    else:
        new_state, error = add_objective_point(
            current_state,
            cx_mm,
            cy_mm,
            table_w_mm,
            table_h_mm,
            description_stripped,
        )

    if error:
        return None, error
    return new_state, None


def _convert_objective_units(
    new_unit: str,
    cx: float,
    cy: float,
    prev_unit: str,
) -> tuple[float, float, str]:
    """Convert objective coordinates when unit changes."""
    if prev_unit == new_unit:
        return cx, cy, new_unit
    return (
        convert_unit_to_unit(cx, prev_unit, new_unit),
        convert_unit_to_unit(cy, prev_unit, new_unit),
        new_unit,
    )


@dataclass(frozen=True)
class ObjectivesCtx:
    """Widget references for objective-points wiring."""

    objective_points_toggle: gr.Checkbox
    objective_points_group: gr.Group
    objective_points_state: gr.State
    objective_unit_state: gr.State
    objective_description: gr.Textbox
    objective_cx_input: gr.Number
    objective_cy_input: gr.Number
    objective_unit: gr.Radio
    add_objective_btn: gr.Button
    objective_points_list: gr.Dropdown
    remove_last_objective_btn: gr.Button
    remove_selected_objective_btn: gr.Button
    table_width: gr.Number
    table_height: gr.Number
    table_unit: gr.Radio
    objective_editing_state: gr.State
    cancel_edit_objective_btn: gr.Button
    output: gr.JSON


def wire_objectives(*, ctx: ObjectivesCtx) -> None:  # noqa: C901
    """Wire objective-point add/remove/edit events."""
    c = ctx

    # -- closures ----------------------------------------------------------

    def _on_objective_selected(
        selected_id: str | None,
        current_state: list[dict[str, Any]],
        objective_unit_val: str,
    ) -> dict[str, Any]:
        """Populate form when an objective point is selected."""
        if not selected_id:
            return {
                c.objective_description: gr.update(value=""),
                c.objective_cx_input: gr.update(value=60),
                c.objective_cy_input: gr.update(value=60),
                c.objective_editing_state: None,
                c.add_objective_btn: gr.update(value=_BTN_ADD_OBJECTIVE),
                c.cancel_edit_objective_btn: gr.update(visible=False),
            }
        point = next((p for p in current_state if p["id"] == selected_id), None)
        if not point:
            return {
                c.objective_description: gr.update(),
                c.objective_cx_input: gr.update(),
                c.objective_cy_input: gr.update(),
                c.objective_editing_state: None,
                c.add_objective_btn: gr.update(value=_BTN_ADD_OBJECTIVE),
                c.cancel_edit_objective_btn: gr.update(visible=False),
            }
        # Convert mm to user display unit
        cx_cm = float(point["cx"]) / 10.0
        cy_cm = float(point["cy"]) / 10.0
        cx_display = convert_from_cm(cx_cm, objective_unit_val)
        cy_display = convert_from_cm(cy_cm, objective_unit_val)
        return {
            c.objective_description: gr.update(value=point.get("description", "")),
            c.objective_cx_input: gr.update(value=round(cx_display, 2)),
            c.objective_cy_input: gr.update(value=round(cy_display, 2)),
            c.objective_editing_state: selected_id,
            c.add_objective_btn: gr.update(value="✏️ Update Objective Point"),
            c.cancel_edit_objective_btn: gr.update(visible=True),
        }

    def _cancel_edit_objective() -> dict[str, Any]:
        """Cancel editing and return to add mode."""
        return {
            c.objective_description: gr.update(value=""),
            c.objective_cx_input: gr.update(value=60),
            c.objective_cy_input: gr.update(value=60),
            c.objective_editing_state: None,
            c.add_objective_btn: gr.update(value=_BTN_ADD_OBJECTIVE),
            c.cancel_edit_objective_btn: gr.update(visible=False),
            c.objective_points_list: gr.update(value=None),
        }

    def _build_obj_error(
        current_state: list[dict[str, Any]],
        editing_id: str | None,
        message: str,
    ) -> dict[str, Any]:
        """Build a standard error result dict."""
        return {
            c.objective_points_state: current_state,
            c.objective_points_list: gr.update(),
            c.objective_editing_state: editing_id,
            c.add_objective_btn: gr.update(),
            c.cancel_edit_objective_btn: gr.update(),
            c.output: {"status": "error", "message": message},
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
        table_w_mm = to_mm(tw, tu)
        table_h_mm = to_mm(th, tu)

        new_state, err = _apply_objective_mutation(
            desc,
            cx,
            cy,
            current_state,
            editing_id,
            objective_unit_val,
            table_w_mm,
            table_h_mm,
        )
        if err:
            return _build_obj_error(current_state, editing_id, err)

        choices = get_objective_points_choices(new_state)  # type: ignore[arg-type]
        return {
            c.objective_points_state: new_state,
            c.objective_points_list: gr.update(choices=choices, value=None),
            c.objective_editing_state: None,
            c.add_objective_btn: gr.update(value=_BTN_ADD_OBJECTIVE),
            c.cancel_edit_objective_btn: gr.update(visible=False),
            c.output: {"status": "success"},
        }

    def _remove_last_objective_point_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[str, Any]:
        new_state = remove_last_objective_point(current_state)
        choices = get_objective_points_choices(new_state)
        dropdown_value = new_state[0]["id"] if new_state else ""
        return {
            c.objective_points_state: new_state,
            c.objective_points_list: gr.update(choices=choices, value=dropdown_value),
            c.objective_editing_state: None,
            c.add_objective_btn: gr.update(value=_BTN_ADD_OBJECTIVE),
            c.cancel_edit_objective_btn: gr.update(visible=False),
        }

    def _remove_selected_objective_point_wrapper(
        selected_id: str,
        current_state: list[dict[str, Any]],
    ) -> dict[str, Any]:
        new_state = remove_selected_objective_point(current_state, selected_id)
        choices = get_objective_points_choices(new_state)
        dropdown_value = new_state[0]["id"] if new_state else ""
        return {
            c.objective_points_state: new_state,
            c.objective_points_list: gr.update(choices=choices, value=dropdown_value),
            c.objective_editing_state: None,
            c.add_objective_btn: gr.update(value=_BTN_ADD_OBJECTIVE),
            c.cancel_edit_objective_btn: gr.update(visible=False),
        }

    # -- bindings ----------------------------------------------------------

    _edit_outputs = [
        c.objective_description,
        c.objective_cx_input,
        c.objective_cy_input,
        c.objective_editing_state,
        c.add_objective_btn,
        c.cancel_edit_objective_btn,
    ]

    c.objective_points_list.change(
        fn=_on_objective_selected,
        inputs=[
            c.objective_points_list,
            c.objective_points_state,
            c.objective_unit,
        ],
        outputs=_edit_outputs,
    )

    c.cancel_edit_objective_btn.click(
        fn=_cancel_edit_objective,
        inputs=[],
        outputs=[*_edit_outputs, c.objective_points_list],
    )

    _add_update_outputs = [
        c.objective_points_state,
        c.objective_points_list,
        c.objective_editing_state,
        c.add_objective_btn,
        c.cancel_edit_objective_btn,
        c.output,
    ]

    c.add_objective_btn.click(
        fn=_add_or_update_objective_point_wrapper,
        inputs=[
            c.objective_description,
            c.objective_cx_input,
            c.objective_cy_input,
            c.objective_points_state,
            c.table_width,
            c.table_height,
            c.table_unit,
            c.objective_unit,
            c.objective_editing_state,
        ],
        outputs=_add_update_outputs,
    )

    _remove_outputs = [
        c.objective_points_state,
        c.objective_points_list,
        c.objective_editing_state,
        c.add_objective_btn,
        c.cancel_edit_objective_btn,
    ]

    c.remove_last_objective_btn.click(
        fn=_remove_last_objective_point_wrapper,
        inputs=[c.objective_points_state],
        outputs=_remove_outputs,
    )
    c.remove_selected_objective_btn.click(
        fn=_remove_selected_objective_point_wrapper,
        inputs=[c.objective_points_list, c.objective_points_state],
        outputs=_remove_outputs,
    )

    # Wire toggle for Objective Points section
    def _toggle_objective_points(enabled: bool) -> Any:
        return handlers.toggle_objective_points_section(enabled)

    c.objective_points_toggle.change(
        fn=_toggle_objective_points,
        inputs=[c.objective_points_toggle],
        outputs=[c.objective_points_group],
    )

    # Wire unit change for Objective Points
    c.objective_unit.change(
        fn=_convert_objective_units,
        inputs=[
            c.objective_unit,
            c.objective_cx_input,
            c.objective_cy_input,
            c.objective_unit_state,
        ],
        outputs=[c.objective_cx_input, c.objective_cy_input, c.objective_unit_state],
    )
