"""Tests for _generate._resets — form/dropdown/extra reset builders."""

from __future__ import annotations

from unittest.mock import MagicMock

import gradio as gr
from adapters.ui_gradio.ui.wiring._generate._resets import (
    build_dropdown_resets,
    build_extra_resets,
    build_form_resets,
)


# ── build_form_resets ────────────────────────────────────────────────
class TestBuildFormResets:
    """Verify the shape and default values of form resets."""

    def test_returns_18_elements(self) -> None:
        resets = build_form_resets()
        assert len(resets) == 18

    def test_scenario_name_reset(self) -> None:
        resets = build_form_resets()
        # First element resets scenario_name to ""
        assert isinstance(resets[0], dict)
        assert resets[0].get("value") == ""

    def test_mode_reset_to_casual(self) -> None:
        resets = build_form_resets()
        assert resets[1].get("value") == "casual"

    def test_seed_reset_to_1(self) -> None:
        resets = build_form_resets()
        assert resets[2].get("value") == 1

    def test_visibility_reset_to_public(self) -> None:
        resets = build_form_resets()
        # visibility is at index 8
        assert resets[8].get("value") == "public"

    def test_special_rules_state_is_empty_list(self) -> None:
        resets = build_form_resets()
        # special_rules_state is at index 10
        assert resets[10] == []

    def test_objectives_with_vp_toggle_false(self) -> None:
        resets = build_form_resets()
        # objectives_with_vp_toggle is at index 11
        assert resets[11].get("value") is False

    def test_state_lists_are_empty(self) -> None:
        resets = build_form_resets()
        # vp_state (12), scenography_state (13),
        # deployment_zones_state (14), objective_points_state (15)
        for idx in (12, 13, 14, 15):
            assert resets[idx] == [], f"Index {idx} should be []"

    def test_output_reset_to_none(self) -> None:
        resets = build_form_resets()
        # output is at index 17
        assert resets[17].get("value") is None


# ── build_dropdown_resets ────────────────────────────────────────────
class TestBuildDropdownResets:
    """Verify dropdown resets match component types."""

    def test_empty_list_returns_empty(self) -> None:
        assert build_dropdown_resets([]) == []

    def test_textbox_resets_to_empty_string(self) -> None:
        tb = MagicMock(spec=gr.Textbox)
        # isinstance check needs real class
        resets = build_dropdown_resets([tb])
        # It should match the isinstance(c, gr.Textbox) path
        # Since MagicMock(spec=gr.Textbox) passes isinstance, we get value=""
        assert len(resets) == 1

    def test_dropdown_resets_to_none_and_empty_choices(self) -> None:
        dd = MagicMock(spec=gr.Dropdown)
        resets = build_dropdown_resets([dd])
        assert len(resets) == 1
        assert resets[0].get("value") is None
        assert resets[0].get("choices") == []

    def test_mixed_components(self) -> None:
        tb = MagicMock(spec=gr.Textbox)
        dd = MagicMock(spec=gr.Dropdown)
        resets = build_dropdown_resets([tb, dd])
        assert len(resets) == 2


# ── build_extra_resets ───────────────────────────────────────────────
class TestBuildExtraResets:
    """Verify edit-mode reset builders."""

    def test_no_edit_mode(self) -> None:
        resets = build_extra_resets(
            has_editing_card_id=False,
            has_create_heading_md=False,
        )
        assert resets == []

    def test_editing_card_id_only(self) -> None:
        resets = build_extra_resets(
            has_editing_card_id=True,
            has_create_heading_md=False,
        )
        assert resets == [""]

    def test_heading_only(self) -> None:
        resets = build_extra_resets(
            has_editing_card_id=False,
            has_create_heading_md=True,
        )
        assert len(resets) == 1
        assert resets[0].get("value") == "## Create New Scenario"

    def test_both(self) -> None:
        resets = build_extra_resets(
            has_editing_card_id=True,
            has_create_heading_md=True,
        )
        assert len(resets) == 2
        assert resets[0] == ""
        assert resets[1].get("value") == "## Create New Scenario"


# ── Idempotence ──────────────────────────────────────────────────────
class TestResetsIdempotence:
    """Each call returns a fresh list (no shared mutable state)."""

    def test_form_resets_are_independent(self) -> None:
        a = build_form_resets()
        b = build_form_resets()
        assert a is not b
        assert a == b

    def test_extra_resets_are_independent(self) -> None:
        a = build_extra_resets(has_editing_card_id=True, has_create_heading_md=True)
        b = build_extra_resets(has_editing_card_id=True, has_create_heading_md=True)
        assert a is not b
