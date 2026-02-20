"""Victory-points section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.state_helpers import (
    add_victory_point,
    get_victory_points_choices,
    remove_last_victory_point,
    remove_selected_victory_point,
    update_victory_point,
)

_BTN_ADD_VP = "+ Add Victory Point"


def wire_victory_points(  # noqa: C901
    *,
    objectives_with_vp_toggle: gr.Checkbox,
    vp_group: gr.Group,
    vp_state: gr.State,
    vp_input: gr.Textbox,
    add_vp_btn: gr.Button,
    remove_vp_btn: gr.Button,
    vp_list: gr.Dropdown,
    remove_selected_vp_btn: gr.Button,
    vp_editing_state: gr.State,
    cancel_edit_vp_btn: gr.Button,
) -> None:
    """Wire victory-point toggle/add/remove/edit events."""

    # -- closures ----------------------------------------------------------

    def _toggle_vp_section(enabled: bool) -> Any:
        return handlers.toggle_vp_section(enabled)

    def _on_vp_selected(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        """Populate form when a VP is selected from dropdown."""
        if not selected_id:
            return {
                vp_input: gr.update(value=""),
                vp_editing_state: None,
                add_vp_btn: gr.update(value=_BTN_ADD_VP),
                cancel_edit_vp_btn: gr.update(visible=False),
            }
        vp = next((v for v in current_state if v["id"] == selected_id), None)
        if not vp:
            return {
                vp_input: gr.update(),
                vp_editing_state: None,
                add_vp_btn: gr.update(value=_BTN_ADD_VP),
                cancel_edit_vp_btn: gr.update(visible=False),
            }
        return {
            vp_input: gr.update(value=vp.get("description", "")),
            vp_editing_state: selected_id,
            add_vp_btn: gr.update(value="✏️ Update Victory Point"),
            cancel_edit_vp_btn: gr.update(visible=True),
        }

    def _cancel_edit_vp() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        return {
            vp_input: gr.update(value=""),
            vp_editing_state: None,
            add_vp_btn: gr.update(value=_BTN_ADD_VP),
            cancel_edit_vp_btn: gr.update(visible=False),
            vp_list: gr.update(value=None),
        }

    def _add_or_update_vp_wrapper(
        current_state: list[dict[str, Any]],
        description: str,
        editing_id: str | None,
    ) -> dict[Any, Any]:
        desc = description.strip()
        if not desc:
            return {
                vp_state: current_state,
                vp_list: gr.update(),
                vp_input: gr.update(value=""),
                vp_editing_state: editing_id,
                add_vp_btn: gr.update(),
                cancel_edit_vp_btn: gr.update(),
            }
        if editing_id:
            new_state = update_victory_point(current_state, editing_id, desc)
        else:
            new_state = add_victory_point(current_state)
            new_state[-1]["description"] = desc

        choices = get_victory_points_choices(new_state)
        return {
            vp_state: new_state,
            vp_list: gr.update(choices=choices, value=None),
            vp_input: gr.update(value=""),
            vp_editing_state: None,
            add_vp_btn: gr.update(value=_BTN_ADD_VP),
            cancel_edit_vp_btn: gr.update(visible=False),
        }

    def _remove_last_vp_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_victory_point(current_state)
        choices = get_victory_points_choices(new_state)
        return {
            vp_state: new_state,
            vp_list: gr.update(choices=choices, value=None),
            vp_input: gr.update(value=""),
            vp_editing_state: None,
            add_vp_btn: gr.update(value=_BTN_ADD_VP),
            cancel_edit_vp_btn: gr.update(visible=False),
        }

    def _remove_selected_vp_wrapper(
        selected_id: str, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                vp_state: current_state,
                vp_list: gr.update(),
                vp_input: gr.update(value=""),
                vp_editing_state: None,
                add_vp_btn: gr.update(value=_BTN_ADD_VP),
                cancel_edit_vp_btn: gr.update(visible=False),
            }
        new_state = remove_selected_victory_point(current_state, selected_id)
        choices = get_victory_points_choices(new_state)
        return {
            vp_state: new_state,
            vp_list: gr.update(choices=choices, value=None),
            vp_input: gr.update(value=""),
            vp_editing_state: None,
            add_vp_btn: gr.update(value=_BTN_ADD_VP),
            cancel_edit_vp_btn: gr.update(visible=False),
        }

    # -- bindings ----------------------------------------------------------

    _edit_outputs = [
        vp_input,
        vp_editing_state,
        add_vp_btn,
        cancel_edit_vp_btn,
    ]

    vp_list.change(
        fn=_on_vp_selected,
        inputs=[vp_list, vp_state],
        outputs=_edit_outputs,
    )

    cancel_edit_vp_btn.click(
        fn=_cancel_edit_vp,
        inputs=[],
        outputs=[*_edit_outputs, vp_list],
    )

    _all_outputs = [
        vp_state,
        vp_list,
        vp_input,
        vp_editing_state,
        add_vp_btn,
        cancel_edit_vp_btn,
    ]

    objectives_with_vp_toggle.change(
        fn=_toggle_vp_section,
        inputs=[objectives_with_vp_toggle],
        outputs=[vp_group],
    )
    add_vp_btn.click(
        fn=_add_or_update_vp_wrapper,
        inputs=[vp_state, vp_input, vp_editing_state],
        outputs=_all_outputs,
    )
    remove_vp_btn.click(
        fn=_remove_last_vp_wrapper,
        inputs=[vp_state],
        outputs=_all_outputs,
    )
    remove_selected_vp_btn.click(
        fn=_remove_selected_vp_wrapper,
        inputs=[vp_list, vp_state],
        outputs=_all_outputs,
    )
