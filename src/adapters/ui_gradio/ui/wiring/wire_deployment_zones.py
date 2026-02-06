"""Deployment-zones section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.state_helpers import (
    add_deployment_zone,
    get_deployment_zones_choices,
    remove_last_deployment_zone,
    remove_selected_deployment_zone,
    validate_separation_coords,
)
from adapters.ui_gradio.units import convert_to_cm


def wire_deployment_zones(  # noqa: C901
    *,
    deployment_zones_toggle: gr.Checkbox,
    zones_group: gr.Group,
    deployment_zones_state: gr.State,
    zone_table_width_state: gr.State,
    zone_table_height_state: gr.State,
    zone_border_select: gr.Radio,
    zone_fill_side_checkbox: gr.Checkbox,
    zone_description: gr.Textbox,
    zone_width: gr.Number,
    zone_height: gr.Number,
    zone_sep_x: gr.Number,
    zone_sep_y: gr.Number,
    add_zone_btn: gr.Button,
    remove_last_zone_btn: gr.Button,
    deployment_zones_list: gr.Dropdown,
    remove_selected_zone_btn: gr.Button,
    table_preset: gr.Radio,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    output: gr.JSON,
) -> None:
    """Wire deployment-zone add/remove/border-fill events."""

    # -- closures ----------------------------------------------------------

    def _add_deployment_zone_wrapper(
        border: str,
        fill_side: bool,
        desc: str,
        w: float,
        h: float,
        sx: float,
        sy: float,
        current_state: list[dict[str, Any]],
        tw: float,
        th: float,
        tu: str,
    ) -> dict[Any, Any]:
        description_stripped = (desc or "").strip()
        if not description_stripped:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Description to be filled.",
                },
            }
        if not border or not border.strip():
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Border to be selected.",
                },
            }
        if not w or w <= 0:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Width > 0.",
                },
            }
        if not h or h <= 0:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Height > 0.",
                },
            }
        table_w_mm = int(convert_to_cm(tw, tu) * 10)
        table_h_mm = int(convert_to_cm(th, tu) * 10)
        if fill_side:
            if border in ("north", "south"):
                w = table_w_mm
                sx = 0
            else:
                h = table_h_mm
                sy = 0
        sx, sy = validate_separation_coords(
            border, int(w), int(h), sx, sy, table_w_mm, table_h_mm
        )
        zone_data = {
            "type": "rect",
            "description": description_stripped,
            "x": int(sx),
            "y": int(sy),
            "width": int(w),
            "height": int(h),
            "border": border,
        }
        new_state, error_msg = add_deployment_zone(
            current_state, zone_data, table_w_mm, table_h_mm
        )
        if error_msg:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {"status": "error", "message": error_msg},
            }
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices),
            output: {"status": "success"},
        }

    def _remove_last_deployment_zone_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_deployment_zone(current_state)
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices),
        }

    def _remove_selected_deployment_zone_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
            }
        new_state = remove_selected_deployment_zone(current_state, selected_id)
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices),
        }

    def _on_zone_border_or_fill_change(
        border_val: str, fill_side: bool, tw: float, th: float, tu: str
    ) -> dict[str, Any]:
        table_w_mm = int(convert_to_cm(tw, tu) * 10)
        table_h_mm = int(convert_to_cm(th, tu) * 10)
        updates: dict[Any, Any] = {}
        if fill_side:
            if border_val in ("north", "south"):
                updates[zone_width] = gr.update(
                    value=table_w_mm, interactive=False, label="Width (mm) [LOCKED]"
                )
                updates[zone_height] = gr.update(interactive=True, label="Height (mm)")
                updates[zone_sep_x] = gr.update(
                    value=0, interactive=False, label="Separation X (mm) [LOCKED]"
                )
                updates[zone_sep_y] = gr.update(
                    interactive=True, label="Separation Y (mm)"
                )
            else:
                updates[zone_width] = gr.update(interactive=True, label="Width (mm)")
                updates[zone_height] = gr.update(
                    value=table_h_mm,
                    interactive=False,
                    label="Height (mm) [LOCKED]",
                )
                updates[zone_sep_x] = gr.update(
                    interactive=True, label="Separation X (mm)"
                )
                updates[zone_sep_y] = gr.update(
                    value=0, interactive=False, label="Separation Y (mm) [LOCKED]"
                )
        else:
            updates[zone_width] = gr.update(interactive=True, label="Width (mm)")
            updates[zone_height] = gr.update(interactive=True, label="Height (mm)")
            updates[zone_sep_x] = gr.update(interactive=True, label="Separation X (mm)")
            updates[zone_sep_y] = gr.update(interactive=True, label="Separation Y (mm)")
        return updates

    # -- bindings ----------------------------------------------------------

    _zone_inputs = [
        zone_border_select,
        zone_fill_side_checkbox,
        table_width,
        table_height,
        table_unit,
    ]
    _zone_outputs = [zone_width, zone_height, zone_sep_x, zone_sep_y]
    for component in (
        zone_border_select,
        zone_fill_side_checkbox,
        table_preset,
        table_width,
        table_height,
        table_unit,
    ):
        component.change(
            fn=_on_zone_border_or_fill_change,
            inputs=_zone_inputs,
            outputs=_zone_outputs,
        )

    add_zone_btn.click(
        fn=_add_deployment_zone_wrapper,
        inputs=[
            zone_border_select,
            zone_fill_side_checkbox,
            zone_description,
            zone_width,
            zone_height,
            zone_sep_x,
            zone_sep_y,
            deployment_zones_state,
            table_width,
            table_height,
            table_unit,
        ],
        outputs=[deployment_zones_state, deployment_zones_list, output],
    )
    remove_last_zone_btn.click(
        fn=_remove_last_deployment_zone_wrapper,
        inputs=[deployment_zones_state],
        outputs=[deployment_zones_state, deployment_zones_list],
    )
    remove_selected_zone_btn.click(
        fn=_remove_selected_deployment_zone_wrapper,
        inputs=[deployment_zones_list, deployment_zones_state],
        outputs=[deployment_zones_state, deployment_zones_list],
    )

    # Wire toggle for Deployment Zones section
    def _toggle_deployment_zones(enabled: bool) -> Any:
        return handlers.toggle_deployment_zones_section(enabled)

    deployment_zones_toggle.change(
        fn=_toggle_deployment_zones,
        inputs=[deployment_zones_toggle],
        outputs=[zones_group],
    )
