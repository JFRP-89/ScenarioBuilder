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
    update_deployment_zone,
)
from adapters.ui_gradio.ui.wiring._deployment._context import DeploymentZonesCtx
from adapters.ui_gradio.ui.wiring._deployment._form_state import (
    UNCHANGED,
    default_zone_form,
    selected_zone_form,
)
from adapters.ui_gradio.ui.wiring._deployment._ui_updates import (
    border_fill_field_states,
    perfect_triangle_side2,
    zone_type_visibility,
)
from adapters.ui_gradio.ui.wiring._deployment._zone_builder import build_zone_data
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
)


def wire_deployment_zones(ctx: DeploymentZonesCtx) -> None:  # noqa: C901
    """Wire deployment-zone add/remove/border-fill/edit events."""

    # Unpack widget references for local access (preserves closure patterns)
    deployment_zones_toggle = ctx.deployment_zones_toggle
    zones_group = ctx.zones_group
    deployment_zones_state = ctx.deployment_zones_state
    zone_unit_state = ctx.zone_unit_state
    zone_type_select = ctx.zone_type_select
    border_row = ctx.border_row
    zone_border_select = ctx.zone_border_select
    corner_row = ctx.corner_row
    zone_corner_select = ctx.zone_corner_select
    fill_side_row = ctx.fill_side_row
    zone_fill_side_checkbox = ctx.zone_fill_side_checkbox
    perfect_triangle_row = ctx.perfect_triangle_row
    zone_perfect_triangle_checkbox = ctx.zone_perfect_triangle_checkbox
    zone_unit = ctx.zone_unit
    zone_description = ctx.zone_description
    rect_dimensions_row = ctx.rect_dimensions_row
    zone_width = ctx.zone_width
    zone_height = ctx.zone_height
    triangle_dimensions_row = ctx.triangle_dimensions_row
    zone_triangle_side1 = ctx.zone_triangle_side1
    zone_triangle_side2 = ctx.zone_triangle_side2
    circle_dimensions_row = ctx.circle_dimensions_row
    zone_circle_radius = ctx.zone_circle_radius
    separation_row = ctx.separation_row
    zone_sep_x = ctx.zone_sep_x
    zone_sep_y = ctx.zone_sep_y
    add_zone_btn = ctx.add_zone_btn
    remove_last_zone_btn = ctx.remove_last_zone_btn
    deployment_zones_list = ctx.deployment_zones_list
    remove_selected_zone_btn = ctx.remove_selected_zone_btn
    table_preset = ctx.table_preset
    table_width = ctx.table_width
    table_height = ctx.table_height
    table_unit = ctx.table_unit
    zone_editing_state = ctx.zone_editing_state
    cancel_edit_zone_btn = ctx.cancel_edit_zone_btn
    output = ctx.output

    # -- closures ----------------------------------------------------------

    def _build_error_result(
        current_state: list[dict[str, Any]],
        message: str,
        editing_id: str | None = None,
    ) -> dict[Any, Any]:
        """Build a standard error result dict."""
        return {
            deployment_zones_state: current_state,
            deployment_zones_list: gr.update(),
            zone_editing_state: editing_id,
            add_zone_btn: gr.update(),
            cancel_edit_zone_btn: gr.update(),
            output: {"status": "error", "message": message},
        }

    # -- form-state → widget-update mapper --------------------------------

    _VALUE_WIDGETS: dict[str, Any] = {
        "zone_type": zone_type_select,
        "border": zone_border_select,
        "corner": zone_corner_select,
        "fill_side": zone_fill_side_checkbox,
        "perfect_triangle": zone_perfect_triangle_checkbox,
        "description": zone_description,
        "width": zone_width,
        "height": zone_height,
        "triangle_side1": zone_triangle_side1,
        "triangle_side2": zone_triangle_side2,
        "circle_radius": zone_circle_radius,
        "sep_x": zone_sep_x,
        "sep_y": zone_sep_y,
    }
    _VIS_WIDGETS: dict[str, Any] = {
        "border_row_visible": border_row,
        "corner_row_visible": corner_row,
        "fill_side_row_visible": fill_side_row,
        "perfect_triangle_row_visible": perfect_triangle_row,
        "rect_dimensions_row_visible": rect_dimensions_row,
        "triangle_dimensions_row_visible": triangle_dimensions_row,
        "circle_dimensions_row_visible": circle_dimensions_row,
        "separation_row_visible": separation_row,
    }

    def _form_to_updates(form: dict[str, Any]) -> dict[Any, Any]:
        """Map a plain form-state dict to ``{widget: gr.update(...)}``."""
        result: dict[Any, Any] = {}
        for key, widget in _VALUE_WIDGETS.items():
            v = form.get(key, UNCHANGED)
            result[widget] = gr.update() if v is UNCHANGED else gr.update(value=v)
        for key, widget in _VIS_WIDGETS.items():
            v = form.get(key)
            if v is not None:
                result[widget] = gr.update(visible=v)
        result[zone_editing_state] = form.get("editing_id")
        result[add_zone_btn] = gr.update(value=form.get("add_btn_text", "+ Add Zone"))
        result[cancel_edit_zone_btn] = gr.update(
            visible=form.get("cancel_btn_visible", False)
        )
        return result

    # -- closures ----------------------------------------------------------

    def _on_zone_selected(
        selected_id: str | None,
        current_state: list[dict[str, Any]],
        zone_unit_val: str,
    ) -> dict[Any, Any]:
        """Populate form when a zone is selected from dropdown."""
        if not selected_id:
            return _form_to_updates(default_zone_form())
        zone = next((z for z in current_state if z["id"] == selected_id), None)
        if not zone:
            return _form_to_updates(default_zone_form())
        return _form_to_updates(selected_zone_form(zone, zone_unit=zone_unit_val))

    def _cancel_edit_zone() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        result = _form_to_updates(default_zone_form())
        result[deployment_zones_list] = gr.update(value=None)
        return result

    def _add_or_update_deployment_zone_wrapper(
        zone_type: str,
        border: str,
        corner: str,
        fill_side: bool,
        desc: str,
        w: float,
        h: float,
        tri_side1: float,
        tri_side2: float,
        circle_radius: float,
        sx: float,
        sy: float,
        current_state: list[dict[str, Any]],
        tw: float,
        th: float,
        tu: str,
        zone_unit_val: str,
        editing_id: str | None = None,
    ) -> dict[Any, Any]:
        """Add or update deployment zone (rectangle, triangle, or circle)."""
        table_w_mm = int(convert_to_cm(tw, tu) * 10)
        table_h_mm = int(convert_to_cm(th, tu) * 10)

        zone_data, form_params, error_msg = build_zone_data(
            zone_type=zone_type,
            description=desc,
            border=border,
            corner=corner,
            fill_side=fill_side,
            width=w,
            height=h,
            tri_side1=tri_side1,
            tri_side2=tri_side2,
            circle_radius=circle_radius,
            sep_x=sx,
            sep_y=sy,
            zone_unit=zone_unit_val,
            table_w_mm=table_w_mm,
            table_h_mm=table_h_mm,
        )
        if error_msg:
            return _build_error_result(current_state, error_msg, editing_id)

        assert zone_data is not None  # guaranteed when error_msg is None

        if editing_id:
            new_state, state_err = update_deployment_zone(
                current_state, editing_id, zone_data, table_w_mm, table_h_mm
            )
        else:
            new_state, state_err = add_deployment_zone(
                current_state, zone_data, table_w_mm, table_h_mm
            )

        if state_err:
            return _build_error_result(current_state, state_err, editing_id)

        # Store form_type and form_params in the state entry
        if editing_id:
            for z in new_state:
                if z["id"] == editing_id:
                    z["form_type"] = zone_type
                    z["form_params"] = form_params
                    break
        else:
            new_state[-1]["form_type"] = zone_type
            new_state[-1]["form_params"] = form_params

        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices, value=None),
            zone_editing_state: None,
            add_zone_btn: gr.update(value="+ Add Zone"),
            cancel_edit_zone_btn: gr.update(visible=False),
            output: {"status": "success"},
        }

    def _remove_last_deployment_zone_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_deployment_zone(current_state)
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices, value=None),
            zone_editing_state: None,
            add_zone_btn: gr.update(value="+ Add Zone"),
            cancel_edit_zone_btn: gr.update(visible=False),
        }

    def _remove_selected_deployment_zone_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                zone_editing_state: None,
                add_zone_btn: gr.update(value="+ Add Zone"),
                cancel_edit_zone_btn: gr.update(visible=False),
            }
        new_state = remove_selected_deployment_zone(current_state, selected_id)
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices, value=None),
            zone_editing_state: None,
            add_zone_btn: gr.update(value="+ Add Zone"),
            cancel_edit_zone_btn: gr.update(visible=False),
        }

    def _on_zone_border_or_fill_change(
        border_val: str,
        fill_side: bool,
        tw: float,
        th: float,
        tu: str,
        zone_unit_val: str,
    ) -> dict[str, Any]:
        """Update zone dimensions when border or fill_side changes."""
        table_w_cm = convert_to_cm(tw, tu)
        table_h_cm = convert_to_cm(th, tu)
        w_unit = convert_from_cm(table_w_cm, zone_unit_val)
        h_unit = convert_from_cm(table_h_cm, zone_unit_val)

        field_states = border_fill_field_states(
            border_val, fill_side, w_unit, h_unit, zone_unit_val
        )
        _field_widgets = {
            "width": zone_width,
            "height": zone_height,
            "sep_x": zone_sep_x,
            "sep_y": zone_sep_y,
        }
        return {
            _field_widgets[name]: gr.update(**spec)
            for name, spec in field_states.items()
        }

    def _on_zone_type_change(zone_type: str) -> dict[Any, Any]:
        """Toggle visibility of rectangle/triangle/circle UI elements."""
        vis = zone_type_visibility(zone_type)
        _row_widgets = {
            "border_row": border_row,
            "corner_row": corner_row,
            "fill_side_row": fill_side_row,
            "perfect_triangle_row": perfect_triangle_row,
            "rect_dimensions_row": rect_dimensions_row,
            "triangle_dimensions_row": triangle_dimensions_row,
            "circle_dimensions_row": circle_dimensions_row,
            "separation_row": separation_row,
        }
        return {_row_widgets[k]: gr.update(visible=v) for k, v in vis.items()}

    def _on_perfect_triangle_change(
        is_perfect: bool, side1: float, zone_unit_val: str
    ) -> dict[Any, Any]:
        """Lock/unlock side2 based on perfect triangle checkbox."""
        state = perfect_triangle_side2(is_perfect, side1, zone_unit_val)
        return {zone_triangle_side2: gr.update(**state)}

    # -- bindings ----------------------------------------------------------

    # Wire zone selection (edit mode)
    _zone_select_outputs = [
        zone_type_select,
        zone_border_select,
        zone_corner_select,
        zone_fill_side_checkbox,
        zone_perfect_triangle_checkbox,
        zone_description,
        zone_width,
        zone_height,
        zone_triangle_side1,
        zone_triangle_side2,
        zone_circle_radius,
        zone_sep_x,
        zone_sep_y,
        border_row,
        corner_row,
        fill_side_row,
        perfect_triangle_row,
        rect_dimensions_row,
        triangle_dimensions_row,
        circle_dimensions_row,
        separation_row,
        zone_editing_state,
        add_zone_btn,
        cancel_edit_zone_btn,
    ]
    deployment_zones_list.change(
        fn=_on_zone_selected,
        inputs=[deployment_zones_list, deployment_zones_state, zone_unit],
        outputs=_zone_select_outputs,
    )

    # Wire cancel edit
    cancel_edit_zone_btn.click(
        fn=_cancel_edit_zone,
        inputs=[],
        outputs=[*_zone_select_outputs, deployment_zones_list],
    )

    # Wire zone type selection
    zone_type_select.change(
        fn=_on_zone_type_change,
        inputs=[zone_type_select],
        outputs=[
            border_row,
            corner_row,
            fill_side_row,
            perfect_triangle_row,
            rect_dimensions_row,
            triangle_dimensions_row,
            circle_dimensions_row,
            separation_row,
        ],
    )

    # Wire perfect triangle checkbox
    zone_perfect_triangle_checkbox.change(
        fn=_on_perfect_triangle_change,
        inputs=[zone_perfect_triangle_checkbox, zone_triangle_side1, zone_unit],
        outputs=[zone_triangle_side2],
    )

    # Also sync side2 when side1 changes if perfect triangle is enabled
    zone_triangle_side1.change(
        fn=_on_perfect_triangle_change,
        inputs=[zone_perfect_triangle_checkbox, zone_triangle_side1, zone_unit],
        outputs=[zone_triangle_side2],
    )

    _zone_inputs = [
        zone_border_select,
        zone_fill_side_checkbox,
        table_width,
        table_height,
        table_unit,
        zone_unit,
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
        fn=_add_or_update_deployment_zone_wrapper,
        inputs=[
            zone_type_select,
            zone_border_select,
            zone_corner_select,
            zone_fill_side_checkbox,
            zone_description,
            zone_width,
            zone_height,
            zone_triangle_side1,
            zone_triangle_side2,
            zone_circle_radius,
            zone_sep_x,
            zone_sep_y,
            deployment_zones_state,
            table_width,
            table_height,
            table_unit,
            zone_unit,
            zone_editing_state,
        ],
        outputs=[
            deployment_zones_state,
            deployment_zones_list,
            zone_editing_state,
            add_zone_btn,
            cancel_edit_zone_btn,
            output,
        ],
    )
    _remove_outputs = [
        deployment_zones_state,
        deployment_zones_list,
        zone_editing_state,
        add_zone_btn,
        cancel_edit_zone_btn,
    ]
    remove_last_zone_btn.click(
        fn=_remove_last_deployment_zone_wrapper,
        inputs=[deployment_zones_state],
        outputs=_remove_outputs,
    )
    remove_selected_zone_btn.click(
        fn=_remove_selected_deployment_zone_wrapper,
        inputs=[deployment_zones_list, deployment_zones_state],
        outputs=_remove_outputs,
    )

    # Wire toggle for Deployment Zones section
    def _toggle_deployment_zones(enabled: bool) -> Any:
        return handlers.toggle_deployment_zones_section(enabled)

    deployment_zones_toggle.change(
        fn=_toggle_deployment_zones,
        inputs=[deployment_zones_toggle],
        outputs=[zones_group],
    )

    # Wire unit change for Deployment Zones
    def _on_zone_unit_change(
        new_unit: str,
        w: float,
        h: float,
        sx: float,
        sy: float,
        tri_side1: float,
        tri_side2: float,
        circle_radius: float,
        prev_unit: str,
    ) -> tuple[float, float, float, float, float, float, float, str]:
        """Convert zone dimensions when unit changes."""
        if prev_unit == new_unit:
            return w, h, sx, sy, tri_side1, tri_side2, circle_radius, new_unit
        w_converted = convert_unit_to_unit(w, prev_unit, new_unit)
        h_converted = convert_unit_to_unit(h, prev_unit, new_unit)
        sx_converted = convert_unit_to_unit(sx, prev_unit, new_unit) if sx else 0
        sy_converted = convert_unit_to_unit(sy, prev_unit, new_unit) if sy else 0
        tri_side1_converted = (
            convert_unit_to_unit(tri_side1, prev_unit, new_unit) if tri_side1 else 0
        )
        tri_side2_converted = (
            convert_unit_to_unit(tri_side2, prev_unit, new_unit) if tri_side2 else 0
        )
        circle_radius_converted = (
            convert_unit_to_unit(circle_radius, prev_unit, new_unit)
            if circle_radius
            else 0
        )
        return (
            w_converted,
            h_converted,
            sx_converted,
            sy_converted,
            tri_side1_converted,
            tri_side2_converted,
            circle_radius_converted,
            new_unit,
        )

    zone_unit.change(
        fn=_on_zone_unit_change,
        inputs=[
            zone_unit,
            zone_width,
            zone_height,
            zone_sep_x,
            zone_sep_y,
            zone_triangle_side1,
            zone_triangle_side2,
            zone_circle_radius,
            zone_unit_state,
        ],
        outputs=[
            zone_width,
            zone_height,
            zone_sep_x,
            zone_sep_y,
            zone_triangle_side1,
            zone_triangle_side2,
            zone_circle_radius,
            zone_unit_state,
        ],
    )
