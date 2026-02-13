"""Scenography-section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.constants import POLYGON_PRESETS
from adapters.ui_gradio.state_helpers import (
    add_scenography_element,
    delete_polygon_row,
    get_scenography_choices,
    remove_last_scenography_element,
    remove_selected_scenography_element,
    update_scenography_element,
)

from ._scenography._builder import build_scenography_data
from ._scenography._form_state import (
    UNCHANGED,
    default_scenography_form,
    selected_scenography_form,
)
from ._scenography._ui_updates import (
    convert_scenography_coordinates,
    scenography_type_visibility,
)


def wire_scenography(  # noqa: C901
    *,
    scenography_toggle: gr.Checkbox,
    scenography_group: gr.Group,
    scenography_state: gr.State,
    scenography_description: gr.Textbox,
    scenography_type: gr.Radio,
    circle_form_row: gr.Row,
    circle_cx: gr.Number,
    circle_cy: gr.Number,
    circle_r: gr.Number,
    rect_form_row: gr.Row,
    rect_x: gr.Number,
    rect_y: gr.Number,
    rect_width: gr.Number,
    rect_height: gr.Number,
    polygon_form_col: gr.Column,
    polygon_preset: gr.Dropdown,
    polygon_points: gr.Dataframe,
    delete_polygon_row_btn: gr.Button,
    polygon_delete_msg: gr.Textbox,
    allow_overlap_checkbox: gr.Checkbox,
    add_scenography_btn: gr.Button,
    remove_last_scenography_btn: gr.Button,
    scenography_list: gr.Dropdown,
    remove_selected_scenography_btn: gr.Button,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    scenography_unit_state: gr.State,
    scenography_unit: gr.Radio,
    scenography_editing_state: gr.State,
    cancel_edit_scenography_btn: gr.Button,
    output: gr.JSON,
) -> None:
    """Wire scenography add/remove/toggle/edit events."""

    # -- helpers -----------------------------------------------------------

    def _form_to_updates(form: dict[str, Any]) -> dict[Any, Any]:
        """Map flat form dict to ``{widget: gr.update(...)}``."""
        vis = scenography_type_visibility(form["type"])
        editing = form["editing_id"] is not None

        def _val(key: str) -> Any:
            v = form[key]
            return gr.update() if v is UNCHANGED else gr.update(value=v)

        return {
            scenography_description: _val("description"),
            scenography_type: _val("type"),
            circle_form_row: gr.update(visible=vis["circle"]),
            rect_form_row: gr.update(visible=vis["rect"]),
            polygon_form_col: gr.update(visible=vis["polygon"]),
            circle_cx: _val("cx"),
            circle_cy: _val("cy"),
            circle_r: _val("r"),
            rect_x: _val("x"),
            rect_y: _val("y"),
            rect_width: _val("width"),
            rect_height: _val("height"),
            polygon_points: _val("polygon_points"),
            allow_overlap_checkbox: _val("allow_overlap"),
            scenography_editing_state: form["editing_id"],
            add_scenography_btn: gr.update(
                value="\u270f\ufe0f Update Element" if editing else "+ Add Element"
            ),
            cancel_edit_scenography_btn: gr.update(visible=editing),
        }

    def _build_error_result(
        current_state: list[dict[str, Any]],
        editing_id: str | None,
        message: str,
    ) -> dict[Any, Any]:
        return {
            scenography_state: current_state,
            scenography_list: gr.update(),
            scenography_editing_state: editing_id,
            add_scenography_btn: gr.update(),
            cancel_edit_scenography_btn: gr.update(),
            output: {"status": "error", "message": message},
        }

    _unchanged_widgets = [
        scenography_description,
        scenography_type,
        circle_form_row,
        rect_form_row,
        polygon_form_col,
        circle_cx,
        circle_cy,
        circle_r,
        rect_x,
        rect_y,
        rect_width,
        rect_height,
        polygon_points,
        allow_overlap_checkbox,
    ]

    # -- closures ----------------------------------------------------------

    def _toggle_scenography_forms(elem_type: str) -> dict[Any, Any]:
        vis = scenography_type_visibility(elem_type)
        return {
            circle_form_row: gr.update(visible=vis["circle"]),
            rect_form_row: gr.update(visible=vis["rect"]),
            polygon_form_col: gr.update(visible=vis["polygon"]),
        }

    def _on_polygon_preset_change(preset: str) -> list[list[float]]:
        result: list[list[float]] = handlers.on_polygon_preset_change(
            preset, POLYGON_PRESETS
        )
        return result

    def _on_scenography_selected(
        selected_id: str | None,
        current_state: list[dict[str, Any]],
        scenography_unit_val: str,
    ) -> dict[Any, Any]:
        """Populate form when a scenography element is selected."""
        if not selected_id:
            return _form_to_updates(default_scenography_form())

        elem = next((e for e in current_state if e["id"] == selected_id), None)
        if not elem:
            result: dict[Any, Any] = {w: gr.update() for w in _unchanged_widgets}
            result[scenography_editing_state] = None
            result[add_scenography_btn] = gr.update(value="+ Add Element")
            result[cancel_edit_scenography_btn] = gr.update(visible=False)
            return result

        return _form_to_updates(selected_scenography_form(elem, scenography_unit_val))

    def _cancel_edit_scenography() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        result = _form_to_updates(default_scenography_form())
        result[scenography_list] = gr.update(value=None)
        return result

    def _add_or_update_scenography_wrapper(
        description: str,
        elem_type: str,
        cx: float,
        cy: float,
        r: float,
        x: float,
        y: float,
        width: float,
        height: float,
        points_data: list[list[Any]],
        allow_overlap: bool,
        current_state: list[dict[str, Any]],
        table_width_val: float,
        table_height_val: float,
        table_unit_val: str,
        scenography_unit_val: str,
        editing_id: str | None,
    ) -> dict[Any, Any]:
        built = build_scenography_data(
            description,
            elem_type,
            cx,
            cy,
            r,
            x,
            y,
            width,
            height,
            points_data,
            allow_overlap,
            table_width_val,
            table_height_val,
            table_unit_val,
            scenography_unit_val,
        )
        if not built["ok"]:
            return _build_error_result(current_state, editing_id, built["message"])

        if editing_id:
            new_state, error_msg = update_scenography_element(
                current_state,
                editing_id,
                built["elem_type"],
                built["data"],
                built["allow_overlap"],
                built["table_w_mm"],
                built["table_h_mm"],
                built["description"],
            )
        else:
            new_state, error_msg = add_scenography_element(
                current_state,
                built["elem_type"],
                built["data"],
                built["allow_overlap"],
                built["table_w_mm"],
                built["table_h_mm"],
                built["description"],
            )

        if error_msg:
            return _build_error_result(current_state, editing_id, error_msg)

        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices, value=None),
            scenography_editing_state: None,
            add_scenography_btn: gr.update(value="+ Add Element"),
            cancel_edit_scenography_btn: gr.update(visible=False),
            output: {
                "status": "ok",
                "message": (f"{'Updated' if editing_id else 'Added'} {elem_type}"),
            },
        }

    def _remove_last_scenography_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_scenography_element(current_state)
        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices, value=None),
            scenography_editing_state: None,
            add_scenography_btn: gr.update(value="+ Add Element"),
            cancel_edit_scenography_btn: gr.update(visible=False),
        }

    def _remove_selected_scenography_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                scenography_state: current_state,
                scenography_list: gr.update(),
                scenography_editing_state: None,
                add_scenography_btn: gr.update(value="+ Add Element"),
                cancel_edit_scenography_btn: gr.update(visible=False),
            }
        new_state = remove_selected_scenography_element(current_state, selected_id)
        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices, value=None),
            scenography_editing_state: None,
            add_scenography_btn: gr.update(value="+ Add Element"),
            cancel_edit_scenography_btn: gr.update(visible=False),
        }

    def _delete_polygon_row_wrapper(
        current_polygon_rows: list[list[float]],
    ) -> dict[Any, Any]:
        updated_rows, error_msg = delete_polygon_row(current_polygon_rows)
        msg = error_msg if error_msg else "Row deleted successfully"
        return {
            polygon_points: updated_rows,
            polygon_delete_msg: gr.update(value=msg),
        }

    # -- bindings ----------------------------------------------------------

    _select_outputs = [
        scenography_description,
        scenography_type,
        circle_form_row,
        rect_form_row,
        polygon_form_col,
        circle_cx,
        circle_cy,
        circle_r,
        rect_x,
        rect_y,
        rect_width,
        rect_height,
        polygon_points,
        allow_overlap_checkbox,
        scenography_editing_state,
        add_scenography_btn,
        cancel_edit_scenography_btn,
    ]

    scenography_list.change(
        fn=_on_scenography_selected,
        inputs=[scenography_list, scenography_state, scenography_unit],
        outputs=_select_outputs,
    )

    _cancel_outputs = [*_select_outputs, scenography_list]

    cancel_edit_scenography_btn.click(
        fn=_cancel_edit_scenography,
        inputs=[],
        outputs=_cancel_outputs,
    )

    scenography_type.change(
        fn=_toggle_scenography_forms,
        inputs=[scenography_type],
        outputs=[circle_form_row, rect_form_row, polygon_form_col],
    )
    polygon_preset.change(
        fn=_on_polygon_preset_change,
        inputs=[polygon_preset],
        outputs=[polygon_points],
    )

    _add_update_outputs = [
        scenography_state,
        scenography_list,
        scenography_editing_state,
        add_scenography_btn,
        cancel_edit_scenography_btn,
        output,
    ]

    add_scenography_btn.click(
        fn=_add_or_update_scenography_wrapper,
        inputs=[
            scenography_description,
            scenography_type,
            circle_cx,
            circle_cy,
            circle_r,
            rect_x,
            rect_y,
            rect_width,
            rect_height,
            polygon_points,
            allow_overlap_checkbox,
            scenography_state,
            table_width,
            table_height,
            table_unit,
            scenography_unit,
            scenography_editing_state,
        ],
        outputs=_add_update_outputs,
    )

    _remove_outputs = [
        scenography_state,
        scenography_list,
        scenography_editing_state,
        add_scenography_btn,
        cancel_edit_scenography_btn,
    ]

    remove_last_scenography_btn.click(
        fn=_remove_last_scenography_wrapper,
        inputs=[scenography_state],
        outputs=_remove_outputs,
    )
    remove_selected_scenography_btn.click(
        fn=_remove_selected_scenography_wrapper,
        inputs=[scenography_list, scenography_state],
        outputs=_remove_outputs,
    )
    delete_polygon_row_btn.click(
        fn=_delete_polygon_row_wrapper,
        inputs=[polygon_points],
        outputs=[polygon_points, polygon_delete_msg],
    )

    # Wire toggle for Scenography section
    def _toggle_scenography(enabled: bool) -> Any:
        return handlers.toggle_scenography_section(enabled)

    scenography_toggle.change(
        fn=_toggle_scenography,
        inputs=[scenography_toggle],
        outputs=[scenography_group],
    )

    # Wire unit change for Scenography
    def _on_scenography_unit_change(
        new_unit: str,
        cx: float,
        cy: float,
        r: float,
        x: float,
        y: float,
        width: float,
        height: float,
        polygon_data: list[list[Any]],
        prev_unit: str,
    ) -> tuple[float, float, float, float, float, float, float, Any, str]:
        """Convert scenography coordinates when unit changes."""
        return convert_scenography_coordinates(
            cx,
            cy,
            r,
            x,
            y,
            width,
            height,
            polygon_data,
            prev_unit,
            new_unit,
        )

    scenography_unit.change(
        fn=_on_scenography_unit_change,
        inputs=[
            scenography_unit,
            circle_cx,
            circle_cy,
            circle_r,
            rect_x,
            rect_y,
            rect_width,
            rect_height,
            polygon_points,
            scenography_unit_state,
        ],
        outputs=[
            circle_cx,
            circle_cy,
            circle_r,
            rect_x,
            rect_y,
            rect_width,
            rect_height,
            polygon_points,
            scenography_unit_state,
        ],
    )
