"""Scenography-section event wiring."""

from __future__ import annotations

import math
from typing import Any, cast

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
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
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

    # -- closures ----------------------------------------------------------

    def _toggle_scenography_forms(elem_type: str) -> dict[Any, Any]:
        return {
            circle_form_row: gr.update(visible=(elem_type == "circle")),
            rect_form_row: gr.update(visible=(elem_type == "rect")),
            polygon_form_col: gr.update(visible=(elem_type == "polygon")),
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
            return {
                scenography_description: gr.update(value=""),
                scenography_type: gr.update(value="circle"),
                circle_form_row: gr.update(visible=True),
                rect_form_row: gr.update(visible=False),
                polygon_form_col: gr.update(visible=False),
                circle_cx: gr.update(value=90),
                circle_cy: gr.update(value=90),
                circle_r: gr.update(value=15),
                rect_x: gr.update(value=30),
                rect_y: gr.update(value=30),
                rect_width: gr.update(value=40),
                rect_height: gr.update(value=30),
                polygon_points: gr.update(),
                allow_overlap_checkbox: gr.update(value=False),
                scenography_editing_state: None,
                add_scenography_btn: gr.update(value="+ Add Element"),
                cancel_edit_scenography_btn: gr.update(visible=False),
            }
        elem = next((e for e in current_state if e["id"] == selected_id), None)
        if not elem:
            return {
                scenography_description: gr.update(),
                scenography_type: gr.update(),
                circle_form_row: gr.update(),
                rect_form_row: gr.update(),
                polygon_form_col: gr.update(),
                circle_cx: gr.update(),
                circle_cy: gr.update(),
                circle_r: gr.update(),
                rect_x: gr.update(),
                rect_y: gr.update(),
                rect_width: gr.update(),
                rect_height: gr.update(),
                polygon_points: gr.update(),
                allow_overlap_checkbox: gr.update(),
                scenography_editing_state: None,
                add_scenography_btn: gr.update(value="+ Add Element"),
                cancel_edit_scenography_btn: gr.update(visible=False),
            }

        data = elem.get("data", {})
        elem_type = elem.get("type", "circle")
        desc = data.get("description", "")
        overlap = elem.get("allow_overlap", False)

        result: dict[Any, Any] = {
            scenography_description: gr.update(value=desc),
            scenography_type: gr.update(value=elem_type),
            allow_overlap_checkbox: gr.update(value=overlap),
            scenography_editing_state: selected_id,
            add_scenography_btn: gr.update(value="✏️ Update Element"),
            cancel_edit_scenography_btn: gr.update(visible=True),
        }

        is_circle = elem_type == "circle"
        is_rect = elem_type == "rect"
        is_polygon = elem_type == "polygon"

        result[circle_form_row] = gr.update(visible=is_circle)
        result[rect_form_row] = gr.update(visible=is_rect)
        result[polygon_form_col] = gr.update(visible=is_polygon)

        if is_circle:
            cx_cm = float(data.get("cx", 0)) / 10.0
            cy_cm = float(data.get("cy", 0)) / 10.0
            r_cm = float(data.get("r", 0)) / 10.0
            result[circle_cx] = gr.update(
                value=round(convert_from_cm(cx_cm, scenography_unit_val), 2)
            )
            result[circle_cy] = gr.update(
                value=round(convert_from_cm(cy_cm, scenography_unit_val), 2)
            )
            result[circle_r] = gr.update(
                value=round(convert_from_cm(r_cm, scenography_unit_val), 2)
            )
            result[rect_x] = gr.update()
            result[rect_y] = gr.update()
            result[rect_width] = gr.update()
            result[rect_height] = gr.update()
            result[polygon_points] = gr.update()
        elif is_rect:
            x_cm = float(data.get("x", 0)) / 10.0
            y_cm = float(data.get("y", 0)) / 10.0
            w_cm = float(data.get("width", 0)) / 10.0
            h_cm = float(data.get("height", 0)) / 10.0
            result[rect_x] = gr.update(
                value=round(convert_from_cm(x_cm, scenography_unit_val), 2)
            )
            result[rect_y] = gr.update(
                value=round(convert_from_cm(y_cm, scenography_unit_val), 2)
            )
            result[rect_width] = gr.update(
                value=round(convert_from_cm(w_cm, scenography_unit_val), 2)
            )
            result[rect_height] = gr.update(
                value=round(convert_from_cm(h_cm, scenography_unit_val), 2)
            )
            result[circle_cx] = gr.update()
            result[circle_cy] = gr.update()
            result[circle_r] = gr.update()
            result[polygon_points] = gr.update()
        else:
            # polygon — populate dataframe
            points = data.get("points", [])
            points_display = []
            for p in points:
                if isinstance(p, dict):
                    px_cm = float(p.get("x", 0)) / 10.0
                    py_cm = float(p.get("y", 0)) / 10.0
                else:
                    px_cm = float(p[0]) / 10.0
                    py_cm = float(p[1]) / 10.0
                points_display.append(
                    [
                        round(convert_from_cm(px_cm, scenography_unit_val), 2),
                        round(convert_from_cm(py_cm, scenography_unit_val), 2),
                    ]
                )
            result[polygon_points] = gr.update(value=points_display)
            result[circle_cx] = gr.update()
            result[circle_cy] = gr.update()
            result[circle_r] = gr.update()
            result[rect_x] = gr.update()
            result[rect_y] = gr.update()
            result[rect_width] = gr.update()
            result[rect_height] = gr.update()

        return result

    def _cancel_edit_scenography() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        return {
            scenography_description: gr.update(value=""),
            scenography_type: gr.update(value="circle"),
            circle_form_row: gr.update(visible=True),
            rect_form_row: gr.update(visible=False),
            polygon_form_col: gr.update(visible=False),
            circle_cx: gr.update(value=90),
            circle_cy: gr.update(value=90),
            circle_r: gr.update(value=15),
            rect_x: gr.update(value=30),
            rect_y: gr.update(value=30),
            rect_width: gr.update(value=40),
            rect_height: gr.update(value=30),
            polygon_points: gr.update(),
            allow_overlap_checkbox: gr.update(value=False),
            scenography_editing_state: None,
            add_scenography_btn: gr.update(value="+ Add Element"),
            cancel_edit_scenography_btn: gr.update(visible=False),
            scenography_list: gr.update(value=None),
        }

    def _add_or_update_scenography_wrapper(  # noqa: C901
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
        description_stripped = (description or "").strip()
        if not description_stripped:
            return {
                scenography_state: current_state,
                scenography_list: gr.update(),
                scenography_editing_state: editing_id,
                add_scenography_btn: gr.update(),
                cancel_edit_scenography_btn: gr.update(),
                output: {
                    "status": "error",
                    "message": "Scenography Element requires Description to be filled.",
                },
            }
        if not elem_type or not elem_type.strip():
            return {
                scenography_state: current_state,
                scenography_list: gr.update(),
                scenography_editing_state: editing_id,
                add_scenography_btn: gr.update(),
                cancel_edit_scenography_btn: gr.update(),
                output: {
                    "status": "error",
                    "message": "Scenography Element requires Type to be selected.",
                },
            }

        table_w_mm = int(convert_to_cm(table_width_val, table_unit_val) * 10)
        table_h_mm = int(convert_to_cm(table_height_val, table_unit_val) * 10)

        if elem_type == "circle":
            if cx is None or cx < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Circle requires Center X >= 0.",
                    },
                }
            if cy is None or cy < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Circle requires Center Y >= 0.",
                    },
                }
            if r is None or r <= 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Circle requires Radius > 0.",
                    },
                }
            form_data: dict[str, Any] = {
                "cx": int(convert_to_cm(cx, scenography_unit_val) * 10),
                "cy": int(convert_to_cm(cy, scenography_unit_val) * 10),
                "r": int(convert_to_cm(r, scenography_unit_val) * 10),
            }
        elif elem_type == "rect":
            if x is None or x < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires X >= 0.",
                    },
                }
            if y is None or y < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires Y >= 0.",
                    },
                }
            if width is None or width <= 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires Width > 0.",
                    },
                }
            if height is None or height <= 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires Height > 0.",
                    },
                }
            form_data = {
                "x": int(convert_to_cm(x, scenography_unit_val) * 10),
                "y": int(convert_to_cm(y, scenography_unit_val) * 10),
                "width": int(convert_to_cm(width, scenography_unit_val) * 10),
                "height": int(convert_to_cm(height, scenography_unit_val) * 10),
            }
        else:
            # polygon
            points_list: list[dict[str, int]] = []
            if points_data is None:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": "No polygon points provided",
                    },
                }
            if hasattr(points_data, "values"):
                try:
                    points_data = points_data.values.tolist()
                except Exception:
                    points_data = []
            if not hasattr(points_data, "__iter__"):
                points_data = []
            for row in points_data:
                if row is None or (isinstance(row, (list, tuple)) and len(row) == 0):
                    continue
                if isinstance(row, (list, tuple)):
                    if len(row) < 2:
                        continue
                    x_raw, y_raw = row[0], row[1]
                else:
                    continue
                if x_raw is None or y_raw is None:
                    continue
                try:
                    x_val = (
                        float(str(x_raw).strip())
                        if isinstance(x_raw, str)
                        else float(x_raw)
                    )
                    y_val = (
                        float(str(y_raw).strip())
                        if isinstance(y_raw, str)
                        else float(y_raw)
                    )
                    if (
                        math.isnan(x_val)
                        or math.isnan(y_val)
                        or math.isinf(x_val)
                        or math.isinf(y_val)
                    ):
                        continue
                    x_mm = int(convert_to_cm(x_val, scenography_unit_val) * 10)
                    y_mm = int(convert_to_cm(y_val, scenography_unit_val) * 10)
                    points_list.append({"x": x_mm, "y": y_mm})
                except (ValueError, TypeError, AttributeError):
                    continue

            if len(points_list) < 3:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    scenography_editing_state: editing_id,
                    add_scenography_btn: gr.update(),
                    cancel_edit_scenography_btn: gr.update(),
                    output: {
                        "status": "error",
                        "message": (
                            f"Polygon needs at least 3 valid points. "
                            f"Found: {len(points_list)}"
                        ),
                    },
                }
            form_data = cast(dict[str, Any], {"points": points_list})

        if editing_id:
            new_state, error_msg = update_scenography_element(
                current_state,
                editing_id,
                elem_type,
                form_data,
                allow_overlap,
                table_w_mm,
                table_h_mm,
                description_stripped,
            )
        else:
            new_state, error_msg = add_scenography_element(
                current_state,
                elem_type,
                form_data,
                allow_overlap,
                table_w_mm,
                table_h_mm,
                description_stripped,
            )

        if error_msg:
            return {
                scenography_state: current_state,
                scenography_list: gr.update(),
                scenography_editing_state: editing_id,
                add_scenography_btn: gr.update(),
                cancel_edit_scenography_btn: gr.update(),
                output: {"status": "error", "message": error_msg},
            }
        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices, value=None),
            scenography_editing_state: None,
            add_scenography_btn: gr.update(value="+ Add Element"),
            cancel_edit_scenography_btn: gr.update(visible=False),
            output: {
                "status": "ok",
                "message": f"{'Updated' if editing_id else 'Added'} {elem_type}",
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
    ) -> tuple[float, float, float, float, float, float, float, list[list[float]], str]:
        """Convert scenography coordinates when unit changes."""
        if prev_unit == new_unit:
            return cx, cy, r, x, y, width, height, polygon_data, new_unit

        cx_converted = convert_unit_to_unit(cx, prev_unit, new_unit)
        cy_converted = convert_unit_to_unit(cy, prev_unit, new_unit)
        r_converted = convert_unit_to_unit(r, prev_unit, new_unit)
        x_converted = convert_unit_to_unit(x, prev_unit, new_unit)
        y_converted = convert_unit_to_unit(y, prev_unit, new_unit)
        width_converted = convert_unit_to_unit(width, prev_unit, new_unit)
        height_converted = convert_unit_to_unit(height, prev_unit, new_unit)

        polygon_converted = polygon_data
        if polygon_data is not None:
            try:
                if hasattr(polygon_data, "values"):
                    points_list = polygon_data.values.tolist()
                elif isinstance(polygon_data, list):
                    points_list = polygon_data
                else:
                    points_list = []

                converted_points = []
                for row in points_list:
                    if (
                        row is not None
                        and isinstance(row, (list, tuple))
                        and len(row) >= 2
                    ):
                        try:
                            x_val = float(row[0])
                            y_val = float(row[1])
                            x_converted_pt = convert_unit_to_unit(
                                x_val, prev_unit, new_unit
                            )
                            y_converted_pt = convert_unit_to_unit(
                                y_val, prev_unit, new_unit
                            )
                            converted_points.append([x_converted_pt, y_converted_pt])
                        except (ValueError, TypeError):
                            pass
                polygon_converted = (
                    converted_points if converted_points else polygon_data
                )
            except Exception:
                polygon_converted = polygon_data

        return (
            cx_converted,
            cy_converted,
            r_converted,
            x_converted,
            y_converted,
            width_converted,
            height_converted,
            polygon_converted,
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
