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
from adapters.ui_gradio.ui.wiring._scenography._builder import (
    ScenographyFormInput,
    build_scenography_data,
)
from adapters.ui_gradio.ui.wiring._scenography._context import ScenographyCtx
from adapters.ui_gradio.ui.wiring._scenography._form_state import (
    UNCHANGED,
    default_scenography_form,
    selected_scenography_form,
)
from adapters.ui_gradio.ui.wiring._scenography._ui_updates import (
    convert_scenography_coordinates,
    scenography_type_visibility,
)

_BTN_ADD_ELEMENT = "+ Add Element"


# ── Module-level helpers (outside wire function to reduce nesting CC) ──


def _form_upd(form: dict[str, Any], key: str) -> Any:
    """Return ``gr.update()`` (unchanged) or ``gr.update(value=v)``."""
    v = form[key]
    return gr.update() if v is UNCHANGED else gr.update(value=v)


def _apply_scenography_mutation(
    built: dict[str, Any],
    current_state: list[dict[str, Any]],
    editing_id: str | None,
) -> tuple[list[dict[str, Any]] | None, str | None, str]:
    """Apply a validated scenography build result.

    Returns ``(new_state | None, error_msg | None, action_label)``.
    """
    if not built["ok"]:
        return None, built["message"], ""

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
        action = "Updated"
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
        action = "Added"

    if error_msg:
        return None, error_msg, ""

    return new_state, None, f"{action} {built['elem_type']}"


def _on_toggle_scenography(enabled: bool) -> Any:
    """Toggle visibility of the scenography section."""
    return handlers.toggle_scenography_section(enabled)


def _on_unit_change(
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


def _bind_events(
    ctx: ScenographyCtx,
    *,
    on_selected: Any,
    on_cancel: Any,
    on_toggle_forms: Any,
    on_preset_change: Any,
    on_add_or_update: Any,
    on_remove_last: Any,
    on_remove_selected: Any,
    on_delete_polygon_row: Any,
) -> None:
    """Connect Gradio widgets to event handler functions."""
    _select_outputs = [
        ctx.scenography_description,
        ctx.scenography_type,
        ctx.circle_form_row,
        ctx.rect_form_row,
        ctx.polygon_form_col,
        ctx.circle_cx,
        ctx.circle_cy,
        ctx.circle_r,
        ctx.rect_x,
        ctx.rect_y,
        ctx.rect_width,
        ctx.rect_height,
        ctx.polygon_points,
        ctx.allow_overlap_checkbox,
        ctx.scenography_editing_state,
        ctx.add_scenography_btn,
        ctx.cancel_edit_scenography_btn,
    ]

    ctx.scenography_list.change(
        fn=on_selected,
        inputs=[ctx.scenography_list, ctx.scenography_state, ctx.scenography_unit],
        outputs=_select_outputs,
    )

    ctx.cancel_edit_scenography_btn.click(
        fn=on_cancel,
        inputs=[],
        outputs=[*_select_outputs, ctx.scenography_list],
    )

    ctx.scenography_type.change(
        fn=on_toggle_forms,
        inputs=[ctx.scenography_type],
        outputs=[ctx.circle_form_row, ctx.rect_form_row, ctx.polygon_form_col],
    )
    ctx.polygon_preset.change(
        fn=on_preset_change,
        inputs=[ctx.polygon_preset],
        outputs=[ctx.polygon_points],
    )

    _add_update_outputs = [
        ctx.scenography_state,
        ctx.scenography_list,
        ctx.scenography_editing_state,
        ctx.add_scenography_btn,
        ctx.cancel_edit_scenography_btn,
        ctx.output,
    ]

    ctx.add_scenography_btn.click(
        fn=on_add_or_update,
        inputs=[
            ctx.scenography_description,
            ctx.scenography_type,
            ctx.circle_cx,
            ctx.circle_cy,
            ctx.circle_r,
            ctx.rect_x,
            ctx.rect_y,
            ctx.rect_width,
            ctx.rect_height,
            ctx.polygon_points,
            ctx.allow_overlap_checkbox,
            ctx.scenography_state,
            ctx.table_width,
            ctx.table_height,
            ctx.table_unit,
            ctx.scenography_unit,
            ctx.scenography_editing_state,
        ],
        outputs=_add_update_outputs,
    )

    _remove_outputs = [
        ctx.scenography_state,
        ctx.scenography_list,
        ctx.scenography_editing_state,
        ctx.add_scenography_btn,
        ctx.cancel_edit_scenography_btn,
    ]

    ctx.remove_last_scenography_btn.click(
        fn=on_remove_last,
        inputs=[ctx.scenography_state],
        outputs=_remove_outputs,
    )
    ctx.remove_selected_scenography_btn.click(
        fn=on_remove_selected,
        inputs=[ctx.scenography_list, ctx.scenography_state],
        outputs=_remove_outputs,
    )
    ctx.delete_polygon_row_btn.click(
        fn=on_delete_polygon_row,
        inputs=[ctx.polygon_points],
        outputs=[ctx.polygon_points, ctx.polygon_delete_msg],
    )

    ctx.scenography_toggle.change(
        fn=_on_toggle_scenography,
        inputs=[ctx.scenography_toggle],
        outputs=[ctx.scenography_group],
    )

    ctx.scenography_unit.change(
        fn=_on_unit_change,
        inputs=[
            ctx.scenography_unit,
            ctx.circle_cx,
            ctx.circle_cy,
            ctx.circle_r,
            ctx.rect_x,
            ctx.rect_y,
            ctx.rect_width,
            ctx.rect_height,
            ctx.polygon_points,
            ctx.scenography_unit_state,
        ],
        outputs=[
            ctx.circle_cx,
            ctx.circle_cy,
            ctx.circle_r,
            ctx.rect_x,
            ctx.rect_y,
            ctx.rect_width,
            ctx.rect_height,
            ctx.polygon_points,
            ctx.scenography_unit_state,
        ],
    )


def wire_scenography(ctx: ScenographyCtx) -> None:  # noqa: C901
    """Wire scenography add/remove/toggle/edit events."""

    # -- helpers -----------------------------------------------------------

    def _form_to_updates(form: dict[str, Any]) -> dict[Any, Any]:
        """Map flat form dict to ``{widget: gr.update(...)}``."""
        vis = scenography_type_visibility(form["type"])
        editing = form["editing_id"] is not None
        return {
            ctx.scenography_description: _form_upd(form, "description"),
            ctx.scenography_type: _form_upd(form, "type"),
            ctx.circle_form_row: gr.update(visible=vis["circle"]),
            ctx.rect_form_row: gr.update(visible=vis["rect"]),
            ctx.polygon_form_col: gr.update(visible=vis["polygon"]),
            ctx.circle_cx: _form_upd(form, "cx"),
            ctx.circle_cy: _form_upd(form, "cy"),
            ctx.circle_r: _form_upd(form, "r"),
            ctx.rect_x: _form_upd(form, "x"),
            ctx.rect_y: _form_upd(form, "y"),
            ctx.rect_width: _form_upd(form, "width"),
            ctx.rect_height: _form_upd(form, "height"),
            ctx.polygon_points: _form_upd(form, "polygon_points"),
            ctx.allow_overlap_checkbox: _form_upd(form, "allow_overlap"),
            ctx.scenography_editing_state: form["editing_id"],
            ctx.add_scenography_btn: gr.update(
                value="\u270f\ufe0f Update Element" if editing else _BTN_ADD_ELEMENT
            ),
            ctx.cancel_edit_scenography_btn: gr.update(visible=editing),
        }

    def _build_error_result(
        current_state: list[dict[str, Any]],
        editing_id: str | None,
        message: str,
    ) -> dict[Any, Any]:
        return {
            ctx.scenography_state: current_state,
            ctx.scenography_list: gr.update(),
            ctx.scenography_editing_state: editing_id,
            ctx.add_scenography_btn: gr.update(),
            ctx.cancel_edit_scenography_btn: gr.update(),
            ctx.output: {"status": "error", "message": message},
        }

    _unchanged_widgets = [
        ctx.scenography_description,
        ctx.scenography_type,
        ctx.circle_form_row,
        ctx.rect_form_row,
        ctx.polygon_form_col,
        ctx.circle_cx,
        ctx.circle_cy,
        ctx.circle_r,
        ctx.rect_x,
        ctx.rect_y,
        ctx.rect_width,
        ctx.rect_height,
        ctx.polygon_points,
        ctx.allow_overlap_checkbox,
    ]

    # -- closures ----------------------------------------------------------

    def _toggle_scenography_forms(elem_type: str) -> dict[Any, Any]:
        vis = scenography_type_visibility(elem_type)
        return {
            ctx.circle_form_row: gr.update(visible=vis["circle"]),
            ctx.rect_form_row: gr.update(visible=vis["rect"]),
            ctx.polygon_form_col: gr.update(visible=vis["polygon"]),
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
            result[ctx.scenography_editing_state] = None
            result[ctx.add_scenography_btn] = gr.update(value=_BTN_ADD_ELEMENT)
            result[ctx.cancel_edit_scenography_btn] = gr.update(visible=False)
            return result

        return _form_to_updates(selected_scenography_form(elem, scenography_unit_val))

    def _cancel_edit_scenography() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        result = _form_to_updates(default_scenography_form())
        result[ctx.scenography_list] = gr.update(value=None)
        return result

    def _add_or_update_scenography_wrapper(*args: Any) -> dict[Any, Any]:
        # Build form directly from positional args (mirrors Gradio inputs order)
        current_state = args[11]
        editing_id = args[16]
        form = ScenographyFormInput(
            description=args[0],
            elem_type=args[1],
            cx=args[2],
            cy=args[3],
            r=args[4],
            x=args[5],
            y=args[6],
            width=args[7],
            height=args[8],
            points_data=args[9],
            allow_overlap=args[10],
            table_width_val=args[12],
            table_height_val=args[13],
            table_unit_val=args[14],
            scenography_unit_val=args[15],
        )
        built = build_scenography_data(form)
        new_state, error_msg, action = _apply_scenography_mutation(
            built,
            current_state,
            editing_id,
        )
        if error_msg:
            return _build_error_result(current_state, editing_id, error_msg)

        choices = get_scenography_choices(new_state)  # type: ignore[arg-type]
        return {
            ctx.scenography_state: new_state,
            ctx.scenography_list: gr.update(choices=choices, value=None),
            ctx.scenography_editing_state: None,
            ctx.add_scenography_btn: gr.update(value=_BTN_ADD_ELEMENT),
            ctx.cancel_edit_scenography_btn: gr.update(visible=False),
            ctx.output: {"status": "ok", "message": action},
        }

    def _remove_last_scenography_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_scenography_element(current_state)
        choices = get_scenography_choices(new_state)
        return {
            ctx.scenography_state: new_state,
            ctx.scenography_list: gr.update(choices=choices, value=None),
            ctx.scenography_editing_state: None,
            ctx.add_scenography_btn: gr.update(value=_BTN_ADD_ELEMENT),
            ctx.cancel_edit_scenography_btn: gr.update(visible=False),
        }

    def _remove_selected_scenography_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                ctx.scenography_state: current_state,
                ctx.scenography_list: gr.update(),
                ctx.scenography_editing_state: None,
                ctx.add_scenography_btn: gr.update(value=_BTN_ADD_ELEMENT),
                ctx.cancel_edit_scenography_btn: gr.update(visible=False),
            }
        new_state = remove_selected_scenography_element(current_state, selected_id)
        choices = get_scenography_choices(new_state)
        return {
            ctx.scenography_state: new_state,
            ctx.scenography_list: gr.update(choices=choices, value=None),
            ctx.scenography_editing_state: None,
            ctx.add_scenography_btn: gr.update(value=_BTN_ADD_ELEMENT),
            ctx.cancel_edit_scenography_btn: gr.update(visible=False),
        }

    def _delete_polygon_row_wrapper(
        current_polygon_rows: list[list[float]],
    ) -> dict[Any, Any]:
        updated_rows, error_msg = delete_polygon_row(current_polygon_rows)
        return {
            ctx.polygon_points: updated_rows,
            ctx.polygon_delete_msg: gr.update(
                value=error_msg or "Row deleted successfully"
            ),
        }

    # -- bindings (delegated to reduce statement count) --------------------

    _bind_events(
        ctx,
        on_selected=_on_scenography_selected,
        on_cancel=_cancel_edit_scenography,
        on_toggle_forms=_toggle_scenography_forms,
        on_preset_change=_on_polygon_preset_change,
        on_add_or_update=_add_or_update_scenography_wrapper,
        on_remove_last=_remove_last_scenography_wrapper,
        on_remove_selected=_remove_selected_scenography_wrapper,
        on_delete_polygon_row=_delete_polygon_row_wrapper,
    )
