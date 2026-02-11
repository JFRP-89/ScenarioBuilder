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
    validate_separation_coords,
)
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
)


def wire_deployment_zones(  # noqa: C901
    *,
    deployment_zones_toggle: gr.Checkbox,
    zones_group: gr.Group,
    deployment_zones_state: gr.State,
    zone_table_width_state: gr.State,
    zone_table_height_state: gr.State,
    zone_unit_state: gr.State,
    zone_type_select: gr.Radio,
    border_row: gr.Row,
    zone_border_select: gr.Radio,
    corner_row: gr.Row,
    zone_corner_select: gr.Radio,
    fill_side_row: gr.Row,
    zone_fill_side_checkbox: gr.Checkbox,
    perfect_triangle_row: gr.Row,
    zone_perfect_triangle_checkbox: gr.Checkbox,
    zone_unit: gr.Radio,
    zone_description: gr.Textbox,
    rect_dimensions_row: gr.Row,
    zone_width: gr.Number,
    zone_height: gr.Number,
    triangle_dimensions_row: gr.Row,
    zone_triangle_side1: gr.Number,
    zone_triangle_side2: gr.Number,
    circle_dimensions_row: gr.Row,
    zone_circle_radius: gr.Number,
    separation_row: gr.Row,
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
    zone_editing_state: gr.State,
    cancel_edit_zone_btn: gr.Button,
    output: gr.JSON,
) -> None:
    """Wire deployment-zone add/remove/border-fill/edit events."""

    # -- helpers -----------------------------------------------------------

    def _calculate_triangle_vertices(
        corner: str, side1_mm: int, side2_mm: int, table_w_mm: int, table_h_mm: int
    ) -> list[tuple[int, int]]:
        """Calculate triangle vertices from corner position and side lengths.

        Creates a right isosceles triangle with one vertex at the specified corner
        and the other two vertices along the adjacent table edges.

        Args:
            corner: One of "north-west", "north-east", "south-west", "south-east"
            side1_mm: Length of first cathetus in mm (vertical from corner)
            side2_mm: Length of second cathetus in mm (horizontal from corner)
            table_w_mm: Table width in mm
            table_h_mm: Table height in mm

        Returns:
            List of 3 (x, y) tuples representing the triangle vertices in mm coordinates
        """
        if corner == "north-west":
            # Corner at (0, 0)
            return [(0, 0), (0, side2_mm), (side1_mm, 0)]
        elif corner == "north-east":
            # Corner at (W, 0)
            return [(table_w_mm, 0), (table_w_mm, side2_mm), (table_w_mm - side1_mm, 0)]
        elif corner == "south-west":
            # Corner at (0, H)
            return [(0, table_h_mm), (0, table_h_mm - side2_mm), (side1_mm, table_h_mm)]
        elif corner == "south-east":
            # Corner at (W, H)
            return [
                (table_w_mm, table_h_mm),
                (table_w_mm, table_h_mm - side2_mm),
                (table_w_mm - side1_mm, table_h_mm),
            ]
        else:
            raise ValueError(f"Invalid corner: {corner}")

    def _calculate_circle_vertices(
        corner: str,
        radius_mm: int,
        table_w_mm: int,
        table_h_mm: int,
        num_points: int = 20,
    ) -> list[tuple[int, int]]:
        """Calculate quarter-circle vertices from corner position and radius.

        Creates a quarter circle anchored at the specified corner,
        approximated as a polygon with num_points vertices.

        Args:
            corner: One of "north-west", "north-east", "south-west", "south-east"
            radius_mm: Radius of the quarter circle in mm
            table_w_mm: Table width in mm
            table_h_mm: Table height in mm
            num_points: Number of points to approximate the arc (default 20)

        Returns:
            List of (x, y) tuples representing the quarter-circle vertices in mm coordinates
        """
        import math

        # Generate arc points (0 to 90 degrees)
        vertices = []

        if corner == "north-west":
            # Quarter circle from (radius, 0) to (0, radius), corner at (0, 0)
            vertices.append((0, 0))
            for i in range(num_points + 1):
                angle = math.pi / 2 * i / num_points  # 0 to 90 degrees
                x = int(radius_mm * math.cos(angle))
                y = int(radius_mm * math.sin(angle))
                vertices.append((x, y))

        elif corner == "north-east":
            # Quarter circle from (W - radius, 0) to (W, radius), corner at (W, 0)
            vertices.append((table_w_mm, 0))
            for i in range(num_points + 1):
                angle = math.pi / 2 * i / num_points
                x = int(table_w_mm - radius_mm * math.cos(angle))
                y = int(radius_mm * math.sin(angle))
                vertices.append((x, y))

        elif corner == "south-west":
            # Quarter circle from (0, H - radius) to (radius, H), corner at (0, H)
            vertices.append((0, table_h_mm))
            for i in range(num_points + 1):
                angle = math.pi / 2 * i / num_points
                x = int(radius_mm * math.cos(angle))
                y = int(table_h_mm - radius_mm * math.sin(angle))
                vertices.append((x, y))

        elif corner == "south-east":
            # Quarter circle from (W, H - radius) to (W - radius, H), corner at (W, H)
            vertices.append((table_w_mm, table_h_mm))
            for i in range(num_points + 1):
                angle = math.pi / 2 * i / num_points
                x = int(table_w_mm - radius_mm * math.cos(angle))
                y = int(table_h_mm - radius_mm * math.sin(angle))
                vertices.append((x, y))
        else:
            raise ValueError(f"Invalid corner: {corner}")

        return vertices

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

    def _on_zone_selected(
        selected_id: str | None,
        current_state: list[dict[str, Any]],
        zone_unit_val: str,
    ) -> dict[Any, Any]:
        """Populate form when a zone is selected from dropdown."""
        _default_reset: dict[Any, Any] = {
            zone_type_select: gr.update(value="rectangle"),
            zone_border_select: gr.update(value="north"),
            zone_corner_select: gr.update(value="north-west"),
            zone_fill_side_checkbox: gr.update(value=True),
            zone_perfect_triangle_checkbox: gr.update(value=True),
            zone_description: gr.update(value=""),
            zone_width: gr.update(value=120),
            zone_height: gr.update(value=20),
            zone_triangle_side1: gr.update(value=30),
            zone_triangle_side2: gr.update(value=30),
            zone_circle_radius: gr.update(value=30),
            zone_sep_x: gr.update(value=0),
            zone_sep_y: gr.update(value=0),
            border_row: gr.update(visible=True),
            corner_row: gr.update(visible=False),
            fill_side_row: gr.update(visible=True),
            perfect_triangle_row: gr.update(visible=False),
            rect_dimensions_row: gr.update(visible=True),
            triangle_dimensions_row: gr.update(visible=False),
            circle_dimensions_row: gr.update(visible=False),
            separation_row: gr.update(visible=True),
            zone_editing_state: None,
            add_zone_btn: gr.update(value="+ Add Zone"),
            cancel_edit_zone_btn: gr.update(visible=False),
        }
        if not selected_id:
            return _default_reset

        zone = next((z for z in current_state if z["id"] == selected_id), None)
        if not zone:
            return _default_reset

        form_params = zone.get("form_params", {})
        form_type = zone.get("form_type", "rectangle")
        data = zone.get("data", {})
        desc = data.get("description", "")

        is_rect = form_type == "rectangle"
        is_triangle = form_type == "triangle"
        is_circle = form_type == "circle"

        result: dict[Any, Any] = {
            zone_description: gr.update(value=desc),
            zone_type_select: gr.update(value=form_type),
            border_row: gr.update(visible=is_rect),
            corner_row: gr.update(visible=is_triangle or is_circle),
            fill_side_row: gr.update(visible=is_rect),
            perfect_triangle_row: gr.update(visible=is_triangle),
            rect_dimensions_row: gr.update(visible=is_rect),
            triangle_dimensions_row: gr.update(visible=is_triangle),
            circle_dimensions_row: gr.update(visible=is_circle),
            separation_row: gr.update(visible=is_rect),
            zone_editing_state: selected_id,
            add_zone_btn: gr.update(value="✏️ Update Zone"),
            cancel_edit_zone_btn: gr.update(visible=True),
        }

        if form_params:
            # Reconstruct form from stored params
            stored_unit = form_params.get("unit", "cm")
            if is_rect:
                w_val = form_params.get("width", 120)
                h_val = form_params.get("height", 20)
                sx_val = form_params.get("sep_x", 0)
                sy_val = form_params.get("sep_y", 0)
                if stored_unit != zone_unit_val:
                    w_val = convert_unit_to_unit(w_val, stored_unit, zone_unit_val)
                    h_val = convert_unit_to_unit(h_val, stored_unit, zone_unit_val)
                    sx_val = convert_unit_to_unit(sx_val, stored_unit, zone_unit_val)
                    sy_val = convert_unit_to_unit(sy_val, stored_unit, zone_unit_val)
                result[zone_border_select] = gr.update(
                    value=form_params.get("border", "north")
                )
                result[zone_fill_side_checkbox] = gr.update(
                    value=form_params.get("fill_side", True)
                )
                result[zone_width] = gr.update(value=round(w_val, 2))
                result[zone_height] = gr.update(value=round(h_val, 2))
                result[zone_sep_x] = gr.update(value=round(sx_val, 2))
                result[zone_sep_y] = gr.update(value=round(sy_val, 2))
                # Set defaults for non-rect fields
                result[zone_corner_select] = gr.update()
                result[zone_perfect_triangle_checkbox] = gr.update()
                result[zone_triangle_side1] = gr.update()
                result[zone_triangle_side2] = gr.update()
                result[zone_circle_radius] = gr.update()
            elif is_triangle:
                s1_val = form_params.get("side1", 30)
                s2_val = form_params.get("side2", 30)
                if stored_unit != zone_unit_val:
                    s1_val = convert_unit_to_unit(s1_val, stored_unit, zone_unit_val)
                    s2_val = convert_unit_to_unit(s2_val, stored_unit, zone_unit_val)
                result[zone_corner_select] = gr.update(
                    value=form_params.get("corner", "north-west")
                )
                result[zone_perfect_triangle_checkbox] = gr.update(
                    value=form_params.get("perfect_triangle", True)
                )
                result[zone_triangle_side1] = gr.update(value=round(s1_val, 2))
                result[zone_triangle_side2] = gr.update(value=round(s2_val, 2))
                # Set defaults for non-triangle fields
                result[zone_border_select] = gr.update()
                result[zone_fill_side_checkbox] = gr.update()
                result[zone_width] = gr.update()
                result[zone_height] = gr.update()
                result[zone_sep_x] = gr.update()
                result[zone_sep_y] = gr.update()
                result[zone_circle_radius] = gr.update()
            elif is_circle:
                r_val = form_params.get("radius", 30)
                if stored_unit != zone_unit_val:
                    r_val = convert_unit_to_unit(r_val, stored_unit, zone_unit_val)
                result[zone_corner_select] = gr.update(
                    value=form_params.get("corner", "north-west")
                )
                result[zone_circle_radius] = gr.update(value=round(r_val, 2))
                # Set defaults for non-circle fields
                result[zone_border_select] = gr.update()
                result[zone_fill_side_checkbox] = gr.update()
                result[zone_perfect_triangle_checkbox] = gr.update()
                result[zone_width] = gr.update()
                result[zone_height] = gr.update()
                result[zone_sep_x] = gr.update()
                result[zone_sep_y] = gr.update()
                result[zone_triangle_side1] = gr.update()
                result[zone_triangle_side2] = gr.update()
        else:
            # No form_params stored — fill from data as best we can
            result[zone_border_select] = gr.update()
            result[zone_corner_select] = gr.update()
            result[zone_fill_side_checkbox] = gr.update()
            result[zone_perfect_triangle_checkbox] = gr.update()
            result[zone_width] = gr.update()
            result[zone_height] = gr.update()
            result[zone_sep_x] = gr.update()
            result[zone_sep_y] = gr.update()
            result[zone_triangle_side1] = gr.update()
            result[zone_triangle_side2] = gr.update()
            result[zone_circle_radius] = gr.update()

        return result

    def _cancel_edit_zone() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        return {
            zone_type_select: gr.update(value="rectangle"),
            zone_border_select: gr.update(value="north"),
            zone_corner_select: gr.update(value="north-west"),
            zone_fill_side_checkbox: gr.update(value=True),
            zone_perfect_triangle_checkbox: gr.update(value=True),
            zone_description: gr.update(value=""),
            zone_width: gr.update(value=120),
            zone_height: gr.update(value=20),
            zone_triangle_side1: gr.update(value=30),
            zone_triangle_side2: gr.update(value=30),
            zone_circle_radius: gr.update(value=30),
            zone_sep_x: gr.update(value=0),
            zone_sep_y: gr.update(value=0),
            border_row: gr.update(visible=True),
            corner_row: gr.update(visible=False),
            fill_side_row: gr.update(visible=True),
            perfect_triangle_row: gr.update(visible=False),
            rect_dimensions_row: gr.update(visible=True),
            triangle_dimensions_row: gr.update(visible=False),
            circle_dimensions_row: gr.update(visible=False),
            separation_row: gr.update(visible=True),
            zone_editing_state: None,
            add_zone_btn: gr.update(value="+ Add Zone"),
            cancel_edit_zone_btn: gr.update(visible=False),
            deployment_zones_list: gr.update(value=None),
        }

    def _add_or_update_deployment_zone_wrapper(  # noqa: C901
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
        description_stripped = (desc or "").strip()
        if not description_stripped:
            return _build_error_result(
                current_state,
                "Deployment Zone requires Description to be filled.",
                editing_id,
            )

        table_w_mm = int(convert_to_cm(tw, tu) * 10)
        table_h_mm = int(convert_to_cm(th, tu) * 10)
        zone_data: dict[str, Any]

        if zone_type == "triangle":
            # Validate triangle parameters
            if not corner or not corner.strip():
                return _build_error_result(
                    current_state,
                    "Triangle requires Corner to be selected.",
                    editing_id,
                )
            if not tri_side1 or tri_side1 <= 0:
                return _build_error_result(
                    current_state, "Triangle requires Side Length 1 > 0.", editing_id
                )
            if not tri_side2 or tri_side2 <= 0:
                return _build_error_result(
                    current_state, "Triangle requires Side Length 2 > 0.", editing_id
                )

            # Convert triangle sides from user unit to mm
            side1_mm = int(convert_to_cm(tri_side1, zone_unit_val) * 10)
            side2_mm = int(convert_to_cm(tri_side2, zone_unit_val) * 10)

            # Calculate triangle vertices
            try:
                vertices = _calculate_triangle_vertices(
                    corner, side1_mm, side2_mm, table_w_mm, table_h_mm
                )
            except ValueError as e:
                return _build_error_result(
                    current_state, f"Invalid triangle configuration: {e}", editing_id
                )

            # Validate all vertices are within table bounds
            for x, y in vertices:
                if x < 0 or x > table_w_mm or y < 0 or y > table_h_mm:
                    return _build_error_result(
                        current_state,
                        f"Triangle extends beyond table bounds: vertex ({x}, {y})",
                        editing_id,
                    )

            # Convert vertices from tuples to dict format required by SVG renderer
            points_dict = [{"x": int(x), "y": int(y)} for x, y in vertices]

            zone_data = {
                "type": "polygon",
                "description": description_stripped,
                "points": points_dict,
                "corner": corner,
            }

        elif zone_type == "circle":
            # Validate circle parameters
            if not corner or not corner.strip():
                return _build_error_result(
                    current_state, "Circle requires Corner to be selected.", editing_id
                )
            if not circle_radius or circle_radius <= 0:
                return _build_error_result(
                    current_state, "Circle requires Radius > 0.", editing_id
                )

            # Convert radius from user unit to mm
            radius_mm = int(convert_to_cm(circle_radius, zone_unit_val) * 10)

            # Calculate quarter-circle vertices
            try:
                vertices = _calculate_circle_vertices(
                    corner, radius_mm, table_w_mm, table_h_mm
                )
            except ValueError as e:
                return _build_error_result(
                    current_state, f"Invalid circle configuration: {e}", editing_id
                )

            # Validate all vertices are within table bounds
            for x, y in vertices:
                if x < 0 or x > table_w_mm or y < 0 or y > table_h_mm:
                    return _build_error_result(
                        current_state,
                        f"Circle extends beyond table bounds: vertex ({x}, {y})",
                        editing_id,
                    )

            # Convert vertices from tuples to dict format required by SVG renderer
            points_dict = [{"x": int(x), "y": int(y)} for x, y in vertices]

            zone_data = {
                "type": "polygon",
                "description": description_stripped,
                "points": points_dict,
                "corner": corner,
            }

        else:  # rectangle
            # Validate rectangle parameters
            if not border or not border.strip():
                return _build_error_result(
                    current_state,
                    "Deployment Zone requires Border to be selected.",
                    editing_id,
                )
            if not w or w <= 0:
                return _build_error_result(
                    current_state, "Deployment Zone requires Width > 0.", editing_id
                )
            if not h or h <= 0:
                return _build_error_result(
                    current_state, "Deployment Zone requires Height > 0.", editing_id
                )

            # Convert zone dimensions from user unit to mm
            w_mm = int(convert_to_cm(w, zone_unit_val) * 10)
            h_mm = int(convert_to_cm(h, zone_unit_val) * 10)
            sx_mm = int(convert_to_cm(sx, zone_unit_val) * 10)
            sy_mm = int(convert_to_cm(sy, zone_unit_val) * 10)

            if fill_side:
                if border in ("north", "south"):
                    w_mm = table_w_mm
                    sx_mm = 0
                else:
                    h_mm = table_h_mm
                    sy_mm = 0

            sx_mm, sy_mm = validate_separation_coords(
                border, w_mm, h_mm, sx_mm, sy_mm, table_w_mm, table_h_mm
            )

            zone_data = {
                "type": "rect",
                "description": description_stripped,
                "x": int(sx_mm),
                "y": int(sy_mm),
                "width": int(w_mm),
                "height": int(h_mm),
                "border": border,
            }

        # Build form_params for later reconstruction during editing
        _form_params: dict[str, Any] = {
            "description": description_stripped,
            "unit": zone_unit_val,
        }
        if zone_type == "triangle":
            _form_params.update(
                corner=corner,
                side1=tri_side1,
                side2=tri_side2,
                perfect_triangle=(tri_side1 == tri_side2),
            )
        elif zone_type == "circle":
            _form_params.update(corner=corner, radius=circle_radius)
        else:  # rectangle
            _form_params.update(
                border=border,
                fill_side=fill_side,
                width=w,
                height=h,
                sep_x=sx,
                sep_y=sy,
            )

        if editing_id:
            # Update existing zone
            new_state, error_msg = update_deployment_zone(
                current_state, editing_id, zone_data, table_w_mm, table_h_mm
            )
        else:
            # Add new zone
            new_state, error_msg = add_deployment_zone(
                current_state, zone_data, table_w_mm, table_h_mm
            )

        if error_msg:
            return _build_error_result(current_state, error_msg, editing_id)

        # Store form_type and form_params in the state entry
        if editing_id:
            for z in new_state:
                if z["id"] == editing_id:
                    z["form_type"] = zone_type
                    z["form_params"] = _form_params
                    break
        else:
            # Newly added zone is always the last entry
            new_state[-1]["form_type"] = zone_type
            new_state[-1]["form_params"] = _form_params

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
        """Update zone dimensions when border or fill_side changes.

        Converts table dimensions to the current zone unit.
        """
        # Convert table dimensions to cm, then to the current zone unit
        table_w_cm = convert_to_cm(tw, tu)
        table_h_cm = convert_to_cm(th, tu)

        width_in_zone_unit = convert_from_cm(table_w_cm, zone_unit_val)
        height_in_zone_unit = convert_from_cm(table_h_cm, zone_unit_val)

        updates: dict[Any, Any] = {}
        if fill_side:
            if border_val in ("north", "south"):
                updates[zone_width] = gr.update(
                    value=round(width_in_zone_unit, 2),
                    interactive=False,
                    label=f"Width ({zone_unit_val}) [LOCKED]",
                )
                updates[zone_height] = gr.update(
                    interactive=True, label=f"Height ({zone_unit_val})"
                )
                updates[zone_sep_x] = gr.update(
                    value=0,
                    interactive=False,
                    label=f"Separation X ({zone_unit_val}) [LOCKED]",
                )
                updates[zone_sep_y] = gr.update(
                    interactive=True, label=f"Separation Y ({zone_unit_val})"
                )
            else:
                updates[zone_width] = gr.update(
                    interactive=True, label=f"Width ({zone_unit_val})"
                )
                updates[zone_height] = gr.update(
                    value=round(height_in_zone_unit, 2),
                    interactive=False,
                    label=f"Height ({zone_unit_val}) [LOCKED]",
                )
                updates[zone_sep_x] = gr.update(
                    interactive=True, label=f"Separation X ({zone_unit_val})"
                )
                updates[zone_sep_y] = gr.update(
                    value=0,
                    interactive=False,
                    label=f"Separation Y ({zone_unit_val}) [LOCKED]",
                )
        else:
            updates[zone_width] = gr.update(
                interactive=True, label=f"Width ({zone_unit_val})"
            )
            updates[zone_height] = gr.update(
                interactive=True, label=f"Height ({zone_unit_val})"
            )
            updates[zone_sep_x] = gr.update(
                interactive=True, label=f"Separation X ({zone_unit_val})"
            )
            updates[zone_sep_y] = gr.update(
                interactive=True, label=f"Separation Y ({zone_unit_val})"
            )
        return updates

    def _on_zone_type_change(zone_type: str) -> dict[Any, Any]:
        """Toggle visibility of rectangle/triangle/circle UI elements."""
        is_rect = zone_type == "rectangle"
        is_triangle = zone_type == "triangle"
        is_circle = zone_type == "circle"
        return {
            border_row: gr.update(visible=is_rect),
            corner_row: gr.update(visible=is_triangle or is_circle),
            fill_side_row: gr.update(visible=is_rect),
            perfect_triangle_row: gr.update(visible=is_triangle),
            rect_dimensions_row: gr.update(visible=is_rect),
            triangle_dimensions_row: gr.update(visible=is_triangle),
            circle_dimensions_row: gr.update(visible=is_circle),
            separation_row: gr.update(visible=is_rect),
        }

    def _on_perfect_triangle_change(
        is_perfect: bool, side1: float, zone_unit_val: str
    ) -> dict[Any, Any]:
        """Lock/unlock side2 based on perfect triangle checkbox."""
        if is_perfect:
            return {
                zone_triangle_side2: gr.update(
                    value=side1,
                    interactive=False,
                    label=f"Y ({zone_unit_val}) [LOCKED]",
                )
            }
        else:
            return {
                zone_triangle_side2: gr.update(
                    interactive=True,
                    label=f"Y ({zone_unit_val})",
                )
            }

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
