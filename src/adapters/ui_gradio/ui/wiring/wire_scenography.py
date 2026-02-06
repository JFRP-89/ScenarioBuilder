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
)
from adapters.ui_gradio.units import convert_to_cm


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
    output: gr.JSON,
) -> None:
    """Wire scenography add/remove/toggle events."""

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

    def _add_scenography_wrapper(  # noqa: C901
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
    ) -> dict[Any, Any]:
        description_stripped = (description or "").strip()
        if not description_stripped:
            return {
                scenography_state: current_state,
                scenography_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Scenography Element requires Description to be filled.",
                },
            }
        if not elem_type or not elem_type.strip():
            return {
                scenography_state: current_state,
                scenography_list: gr.update(),
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
                    output: {
                        "status": "error",
                        "message": "Circle requires Center X >= 0.",
                    },
                }
            if cy is None or cy < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Circle requires Center Y >= 0.",
                    },
                }
            if r is None or r <= 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Circle requires Radius > 0.",
                    },
                }
            form_data: dict[str, Any] = {"cx": int(cx), "cy": int(cy), "r": int(r)}
        elif elem_type == "rect":
            if x is None or x < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires X >= 0.",
                    },
                }
            if y is None or y < 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires Y >= 0.",
                    },
                }
            if width is None or width <= 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires Width > 0.",
                    },
                }
            if height is None or height <= 0:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": "Rectangle requires Height > 0.",
                    },
                }
            form_data = {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            }
        else:
            # polygon
            points_list: list[dict[str, int]] = []
            if points_data is None:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
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
                    points_list.append({"x": int(x_val), "y": int(y_val)})
                except (ValueError, TypeError, AttributeError):
                    continue

            if len(points_list) < 3:
                return {
                    scenography_state: current_state,
                    scenography_list: gr.update(),
                    output: {
                        "status": "error",
                        "message": (
                            f"Polygon needs at least 3 valid points. "
                            f"Found: {len(points_list)}"
                        ),
                    },
                }
            form_data = cast(dict[str, Any], {"points": points_list})

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
                output: {"status": "error", "message": error_msg},
            }
        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices),
            output: {"status": "ok", "message": f"Added {elem_type}"},
        }

    def _remove_last_scenography_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_scenography_element(current_state)
        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices),
        }

    def _remove_selected_scenography_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {scenography_state: current_state, scenography_list: gr.update()}
        new_state = remove_selected_scenography_element(current_state, selected_id)
        choices = get_scenography_choices(new_state)
        return {
            scenography_state: new_state,
            scenography_list: gr.update(choices=choices),
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
    add_scenography_btn.click(
        fn=_add_scenography_wrapper,
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
        ],
        outputs=[scenography_state, scenography_list, output],
    )
    remove_last_scenography_btn.click(
        fn=_remove_last_scenography_wrapper,
        inputs=[scenography_state],
        outputs=[scenography_state, scenography_list],
    )
    remove_selected_scenography_btn.click(
        fn=_remove_selected_scenography_wrapper,
        inputs=[scenography_list, scenography_state],
        outputs=[scenography_state, scenography_list],
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
