"""Tests for _generate._outputs — build_stay_outputs."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.wiring._generate._outputs import build_stay_outputs


class TestBuildStayOutputsTupleLength:
    """Verify the output tuple has the correct number of elements."""

    @pytest.mark.parametrize(
        ("n_nav", "n_form", "n_dropdowns", "n_extra", "expected_len"),
        [
            # total = n_nav + 1 (home_recent) + n_form + n_dropdowns + n_extra + 1 (status)
            (3, 18, 0, 0, 23),
            (3, 18, 6, 0, 29),
            (3, 18, 6, 2, 31),
            (1, 0, 0, 0, 3),
        ],
    )
    def test_length(
        self,
        n_nav: int,
        n_form: int,
        n_dropdowns: int,
        n_extra: int,
        expected_len: int,
    ) -> None:
        result = build_stay_outputs(
            "error msg",
            n_nav=n_nav,
            n_form=n_form,
            n_dropdowns=n_dropdowns,
            n_extra=n_extra,
        )
        assert len(result) == expected_len


class TestBuildStayOutputsStatusPosition:
    """The final element is always the status textbox update."""

    def test_status_is_last(self) -> None:
        result = build_stay_outputs(
            "Something went wrong",
            n_nav=3,
            n_form=18,
            n_dropdowns=6,
            n_extra=2,
        )
        last = result[-1]
        assert isinstance(last, dict)
        assert last.get("value") == "Something went wrong"
        assert last.get("visible") is True

    def test_status_message_preserved(self) -> None:
        msg = "Generate a card preview first."
        result = build_stay_outputs(msg, n_nav=2, n_form=0, n_dropdowns=0, n_extra=0)
        assert result[-1]["value"] == msg


class TestBuildStayOutputsNoOps:
    """All elements except the last should be gr.update() no-ops."""

    def test_all_intermediate_are_noop(self) -> None:
        import gradio as gr

        noop = gr.update()  # canonical no-op (may contain __type__)
        result = build_stay_outputs("err", n_nav=2, n_form=3, n_dropdowns=1, n_extra=1)
        # Everything except the last element should be a no-op gr.update()
        for i, elem in enumerate(result[:-1]):
            assert isinstance(elem, dict), f"Element {i} should be dict"
            assert elem == noop, f"Element {i} should be gr.update() no-op"


class TestBuildStayOutputsEdgeCases:
    """Edge cases for zero-length segments."""

    def test_zero_form_zero_dropdowns(self) -> None:
        result = build_stay_outputs("test", n_nav=1, n_form=0, n_dropdowns=0, n_extra=0)
        # 1 nav + 1 home_recent + 0 + 0 + 0 + 1 status = 3
        assert len(result) == 3

    def test_all_zeros_except_nav(self) -> None:
        result = build_stay_outputs("x", n_nav=5, n_form=0, n_dropdowns=0, n_extra=0)
        assert len(result) == 7  # 5 + 1 + 1
