"""Central event wiring for the Gradio UI.

This package delegates to per-section wiring modules.  The public API
consists of:

* ``wire_events(**components)`` — hooks up every ``.click`` / ``.change``
  binding by dispatching to the section-level ``wire_*`` functions.
* ``_on_table_preset_change`` / ``_on_table_unit_change`` — thin adapters
  re-exported for backward-compatible test imports via ``app.py`` shims.

Implementation note
-------------------
``wire_events()`` accepts ``**kwargs`` and immediately builds typed
bundle dataclasses for each UI section.  The bundle constructors
validate that all required fields are present at runtime.

The ``_REQUIRED_KEYS`` / ``_ACCEPTED_KEYS`` constants expose the
expected component names so that ``app.py`` and the golden-contract
tests can verify exhaustive coverage without relying on positional
or keyword-only parameter introspection.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.ui.wiring.wire_table import (
    _on_table_preset_change,
    _on_table_unit_change,
)

__all__ = [
    "_ACCEPTED_KEYS",
    "_REQUIRED_KEYS",
    "_on_table_preset_change",
    "_on_table_unit_change",
    "wire_events",
]


# ── Key sets for contract validation ────────────────────────────────
# These mirror the old typed signature so that ``kwargs_for_call`` and
# golden-contract tests can verify exhaustive component coverage.

_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        # Actor / meta
        "actor_id",
        "scenario_name",
        "mode",
        "is_replicable",
        "generate_from_seed",
        "apply_seed_btn",
        "refill_scenario_btn",
        "armies",
        # Table
        "table_preset",
        "prev_unit_state",
        "custom_table_row",
        "table_width",
        "table_height",
        "table_unit",
        # Scenario details
        "deployment",
        "layout",
        "objectives",
        "initial_priority",
        "objectives_with_vp_toggle",
        "vp_group",
        "vp_state",
        "vp_input",
        "add_vp_btn",
        "remove_vp_btn",
        "vp_list",
        "remove_selected_vp_btn",
        "vp_editing_state",
        "cancel_edit_vp_btn",
        # Special rules
        "special_rules_state",
        "special_rules_toggle",
        "rules_group",
        "rule_type_radio",
        "rule_name_input",
        "rule_value_input",
        "add_rule_btn",
        "remove_rule_btn",
        "rules_list",
        "remove_selected_rule_btn",
        "rule_editing_state",
        "cancel_edit_rule_btn",
        # Visibility
        "visibility",
        "shared_with_row",
        "shared_with",
        # Deployment zones
        "deployment_zones_toggle",
        "zones_group",
        "deployment_zones_state",
        "zone_table_width_state",
        "zone_table_height_state",
        "zone_unit_state",
        "zone_type_select",
        "border_row",
        "zone_border_select",
        "corner_row",
        "zone_corner_select",
        "fill_side_row",
        "zone_fill_side_checkbox",
        "perfect_triangle_row",
        "zone_perfect_triangle_checkbox",
        "zone_unit",
        "zone_description",
        "rect_dimensions_row",
        "zone_width",
        "zone_height",
        "triangle_dimensions_row",
        "zone_triangle_side1",
        "zone_triangle_side2",
        "circle_dimensions_row",
        "zone_circle_radius",
        "separation_row",
        "zone_sep_x",
        "zone_sep_y",
        "add_zone_btn",
        "remove_last_zone_btn",
        "deployment_zones_list",
        "remove_selected_zone_btn",
        "zone_editing_state",
        "cancel_edit_zone_btn",
        # Objective points
        "objective_points_toggle",
        "objective_points_group",
        "objective_points_state",
        "objective_unit_state",
        "objective_description",
        "objective_cx_input",
        "objective_cy_input",
        "objective_unit",
        "add_objective_btn",
        "objective_points_list",
        "remove_last_objective_btn",
        "remove_selected_objective_btn",
        "objective_editing_state",
        "cancel_edit_objective_btn",
        # Scenography
        "scenography_toggle",
        "scenography_group",
        "scenography_state",
        "scenography_unit_state",
        "scenography_description",
        "scenography_type",
        "scenography_unit",
        "circle_form_row",
        "circle_cx",
        "circle_cy",
        "circle_r",
        "rect_form_row",
        "rect_x",
        "rect_y",
        "rect_width",
        "rect_height",
        "polygon_form_col",
        "polygon_preset",
        "polygon_points",
        "delete_polygon_row_btn",
        "polygon_delete_msg",
        "allow_overlap_checkbox",
        "add_scenography_btn",
        "remove_last_scenography_btn",
        "scenography_list",
        "remove_selected_scenography_btn",
        "scenography_editing_state",
        "cancel_edit_scenography_btn",
        # Generate
        "generate_btn",
        "svg_preview",
        "output",
        "preview_full_state",
    }
)

_OPTIONAL_KEYS: frozenset[str] = frozenset(
    {
        "create_scenario_btn",
        "create_scenario_status",
        "page_state",
        "page_containers",
        "home_recent_html",
        "home_page_info",
        "home_page_state",
        "home_cards_cache_state",
        "home_fav_ids_cache_state",
        "editing_card_id",
        "create_heading_md",
    }
)

_ACCEPTED_KEYS: frozenset[str] = _REQUIRED_KEYS | _OPTIONAL_KEYS


def wire_events(**kwargs: Any) -> None:
    """Hook every UI event to its handler by dispatching to section wirers.

    Accepts component references as keyword arguments.  The expected
    keys are declared in ``_REQUIRED_KEYS`` and ``_ACCEPTED_KEYS`` so
    that ``app.py`` and the golden-contract tests can verify coverage
    without relying on positional parameter introspection.

    The actual wiring logic lives in ``_orchestrator._wire_all()``.
    """
    from adapters.ui_gradio.ui.wiring._deployment._context import (
        DeploymentZonesCtx,
    )
    from adapters.ui_gradio.ui.wiring._orchestrator import (
        _GenerateBundle,
        _MetaBundle,
        _ObjectivesBundle,
        _SpecialRulesBundle,
        _TableBundle,
        _VisibilityBundle,
        _VPBundle,
        _wire_all,
    )
    from adapters.ui_gradio.ui.wiring._scenography._context import (
        ScenographyCtx,
    )

    _wire_all(
        meta=_MetaBundle(
            actor_id=kwargs["actor_id"],
            scenario_name=kwargs["scenario_name"],
            mode=kwargs["mode"],
            is_replicable=kwargs["is_replicable"],
            generate_from_seed=kwargs["generate_from_seed"],
            apply_seed_btn=kwargs["apply_seed_btn"],
            refill_scenario_btn=kwargs["refill_scenario_btn"],
            armies=kwargs["armies"],
            deployment=kwargs["deployment"],
            layout=kwargs["layout"],
            objectives=kwargs["objectives"],
            initial_priority=kwargs["initial_priority"],
        ),
        table=_TableBundle(
            table_preset=kwargs["table_preset"],
            prev_unit_state=kwargs["prev_unit_state"],
            custom_table_row=kwargs["custom_table_row"],
            table_width=kwargs["table_width"],
            table_height=kwargs["table_height"],
            table_unit=kwargs["table_unit"],
        ),
        vp=_VPBundle(
            objectives_with_vp_toggle=kwargs["objectives_with_vp_toggle"],
            vp_group=kwargs["vp_group"],
            vp_state=kwargs["vp_state"],
            vp_input=kwargs["vp_input"],
            add_vp_btn=kwargs["add_vp_btn"],
            remove_vp_btn=kwargs["remove_vp_btn"],
            vp_list=kwargs["vp_list"],
            remove_selected_vp_btn=kwargs["remove_selected_vp_btn"],
            vp_editing_state=kwargs["vp_editing_state"],
            cancel_edit_vp_btn=kwargs["cancel_edit_vp_btn"],
        ),
        rules=_SpecialRulesBundle(
            special_rules_state=kwargs["special_rules_state"],
            special_rules_toggle=kwargs["special_rules_toggle"],
            rules_group=kwargs["rules_group"],
            rule_type_radio=kwargs["rule_type_radio"],
            rule_name_input=kwargs["rule_name_input"],
            rule_value_input=kwargs["rule_value_input"],
            add_rule_btn=kwargs["add_rule_btn"],
            remove_rule_btn=kwargs["remove_rule_btn"],
            rules_list=kwargs["rules_list"],
            remove_selected_rule_btn=kwargs["remove_selected_rule_btn"],
            rule_editing_state=kwargs["rule_editing_state"],
            cancel_edit_rule_btn=kwargs["cancel_edit_rule_btn"],
        ),
        vis=_VisibilityBundle(
            visibility=kwargs["visibility"],
            shared_with_row=kwargs["shared_with_row"],
            shared_with=kwargs["shared_with"],
        ),
        deployment_ctx=DeploymentZonesCtx(
            deployment_zones_toggle=kwargs["deployment_zones_toggle"],
            zones_group=kwargs["zones_group"],
            deployment_zones_state=kwargs["deployment_zones_state"],
            zone_table_width_state=kwargs["zone_table_width_state"],
            zone_table_height_state=kwargs["zone_table_height_state"],
            zone_unit_state=kwargs["zone_unit_state"],
            zone_type_select=kwargs["zone_type_select"],
            border_row=kwargs["border_row"],
            zone_border_select=kwargs["zone_border_select"],
            corner_row=kwargs["corner_row"],
            zone_corner_select=kwargs["zone_corner_select"],
            fill_side_row=kwargs["fill_side_row"],
            zone_fill_side_checkbox=kwargs["zone_fill_side_checkbox"],
            perfect_triangle_row=kwargs["perfect_triangle_row"],
            zone_perfect_triangle_checkbox=kwargs["zone_perfect_triangle_checkbox"],
            zone_unit=kwargs["zone_unit"],
            zone_description=kwargs["zone_description"],
            rect_dimensions_row=kwargs["rect_dimensions_row"],
            zone_width=kwargs["zone_width"],
            zone_height=kwargs["zone_height"],
            triangle_dimensions_row=kwargs["triangle_dimensions_row"],
            zone_triangle_side1=kwargs["zone_triangle_side1"],
            zone_triangle_side2=kwargs["zone_triangle_side2"],
            circle_dimensions_row=kwargs["circle_dimensions_row"],
            zone_circle_radius=kwargs["zone_circle_radius"],
            separation_row=kwargs["separation_row"],
            zone_sep_x=kwargs["zone_sep_x"],
            zone_sep_y=kwargs["zone_sep_y"],
            add_zone_btn=kwargs["add_zone_btn"],
            remove_last_zone_btn=kwargs["remove_last_zone_btn"],
            deployment_zones_list=kwargs["deployment_zones_list"],
            remove_selected_zone_btn=kwargs["remove_selected_zone_btn"],
            table_preset=kwargs["table_preset"],
            table_width=kwargs["table_width"],
            table_height=kwargs["table_height"],
            table_unit=kwargs["table_unit"],
            zone_editing_state=kwargs["zone_editing_state"],
            cancel_edit_zone_btn=kwargs["cancel_edit_zone_btn"],
            output=kwargs["output"],
        ),
        obj=_ObjectivesBundle(
            objective_points_toggle=kwargs["objective_points_toggle"],
            objective_points_group=kwargs["objective_points_group"],
            objective_points_state=kwargs["objective_points_state"],
            objective_unit_state=kwargs["objective_unit_state"],
            objective_description=kwargs["objective_description"],
            objective_cx_input=kwargs["objective_cx_input"],
            objective_cy_input=kwargs["objective_cy_input"],
            objective_unit=kwargs["objective_unit"],
            add_objective_btn=kwargs["add_objective_btn"],
            objective_points_list=kwargs["objective_points_list"],
            remove_last_objective_btn=kwargs["remove_last_objective_btn"],
            remove_selected_objective_btn=kwargs["remove_selected_objective_btn"],
            objective_editing_state=kwargs["objective_editing_state"],
            cancel_edit_objective_btn=kwargs["cancel_edit_objective_btn"],
        ),
        scenography_ctx=ScenographyCtx(
            scenography_toggle=kwargs["scenography_toggle"],
            scenography_group=kwargs["scenography_group"],
            scenography_state=kwargs["scenography_state"],
            scenography_description=kwargs["scenography_description"],
            scenography_type=kwargs["scenography_type"],
            circle_form_row=kwargs["circle_form_row"],
            circle_cx=kwargs["circle_cx"],
            circle_cy=kwargs["circle_cy"],
            circle_r=kwargs["circle_r"],
            rect_form_row=kwargs["rect_form_row"],
            rect_x=kwargs["rect_x"],
            rect_y=kwargs["rect_y"],
            rect_width=kwargs["rect_width"],
            rect_height=kwargs["rect_height"],
            polygon_form_col=kwargs["polygon_form_col"],
            polygon_preset=kwargs["polygon_preset"],
            polygon_points=kwargs["polygon_points"],
            delete_polygon_row_btn=kwargs["delete_polygon_row_btn"],
            polygon_delete_msg=kwargs["polygon_delete_msg"],
            allow_overlap_checkbox=kwargs["allow_overlap_checkbox"],
            add_scenography_btn=kwargs["add_scenography_btn"],
            remove_last_scenography_btn=kwargs["remove_last_scenography_btn"],
            scenography_list=kwargs["scenography_list"],
            remove_selected_scenography_btn=kwargs["remove_selected_scenography_btn"],
            table_width=kwargs["table_width"],
            table_height=kwargs["table_height"],
            table_unit=kwargs["table_unit"],
            scenography_unit_state=kwargs["scenography_unit_state"],
            scenography_unit=kwargs["scenography_unit"],
            scenography_editing_state=kwargs["scenography_editing_state"],
            cancel_edit_scenography_btn=kwargs["cancel_edit_scenography_btn"],
            output=kwargs["output"],
        ),
        gen=_GenerateBundle(
            generate_btn=kwargs["generate_btn"],
            svg_preview=kwargs["svg_preview"],
            output=kwargs["output"],
            preview_full_state=kwargs["preview_full_state"],
            create_scenario_btn=kwargs.get("create_scenario_btn"),
            create_scenario_status=kwargs.get("create_scenario_status"),
            page_state=kwargs.get("page_state"),
            page_containers=kwargs.get("page_containers"),
            home_recent_html=kwargs.get("home_recent_html"),
            home_page_info=kwargs.get("home_page_info"),
            home_page_state=kwargs.get("home_page_state"),
            home_cards_cache_state=kwargs.get("home_cards_cache_state"),
            home_fav_ids_cache_state=kwargs.get("home_fav_ids_cache_state"),
            editing_card_id=kwargs.get("editing_card_id"),
            create_heading_md=kwargs.get("create_heading_md"),
        ),
    )
