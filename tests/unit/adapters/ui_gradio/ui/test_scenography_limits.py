"""Unit tests for scenography count limits in Gradio state helpers."""

from __future__ import annotations

from adapters.ui_gradio._state._scenography import (
    _MAX_PASSABLE,
    _MAX_SCENOGRAPHY,
    _MAX_SOLID,
    add_scenography_element,
    update_scenography_element,
)

_TABLE_W = 1200
_TABLE_H = 1200


def _make_elem(elem_id: str, *, allow_overlap: bool = False, cx: int = 100) -> dict:
    return {
        "id": elem_id,
        "type": "circle",
        "label": f"Circle {elem_id}",
        "data": {"type": "circle", "cx": cx, "cy": 100, "r": 20},
        "allow_overlap": allow_overlap,
    }


def _form_circle(cx: int = 100) -> dict:
    return {"cx": cx, "cy": 100, "r": 20}


# ── add_scenography_element limits ──────────────────────────────────────────


class TestAddScenographyLimits:
    def test_add_first_element_ok(self):
        state, err = add_scenography_element(
            [],
            "circle",
            _form_circle(200),
            False,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is None
        assert len(state) == 1

    def test_add_up_to_six_ok(self):
        """Fill 3 solid + 3 passable → all accepted."""
        state: list = []
        for i in range(3):
            state, err = add_scenography_element(
                state,
                "circle",
                _form_circle(100 + 60 * i),
                False,
                _TABLE_W,
                _TABLE_H,
            )
            assert err is None
        for i in range(3):
            state, err = add_scenography_element(
                state,
                "circle",
                _form_circle(400 + 60 * i),
                True,
                _TABLE_W,
                _TABLE_H,
            )
            assert err is None
        assert len(state) == 6

    def test_seventh_element_rejected(self):
        """After 6 elements, a 7th must be rejected."""
        state = [
            _make_elem(f"s{i}", allow_overlap=False, cx=100 + 60 * i) for i in range(3)
        ] + [_make_elem(f"p{i}", allow_overlap=True, cx=400 + 60 * i) for i in range(3)]
        new_state, err = add_scenography_element(
            state,
            "circle",
            _form_circle(700),
            False,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is not None
        assert str(_MAX_SCENOGRAPHY) in err
        assert new_state is state  # unchanged

    def test_fourth_solid_rejected(self):
        """After 3 solid, a 4th solid is rejected (even if total < 6)."""
        state = [
            _make_elem(f"s{i}", allow_overlap=False, cx=100 + 60 * i) for i in range(3)
        ]
        new_state, err = add_scenography_element(
            state,
            "circle",
            _form_circle(400),
            False,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is not None
        assert "solid" in err.lower() or str(_MAX_SOLID) in err
        assert new_state is state

    def test_fourth_passable_rejected(self):
        """After 3 passable, a 4th passable is rejected (even if total < 6)."""
        state = [
            _make_elem(f"p{i}", allow_overlap=True, cx=100 + 60 * i) for i in range(3)
        ]
        new_state, err = add_scenography_element(
            state,
            "circle",
            _form_circle(400),
            True,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is not None
        assert "passable" in err.lower() or str(_MAX_PASSABLE) in err
        assert new_state is state

    def test_passable_ok_when_only_solid_at_max(self):
        """3 solid + 0 passable → can still add passable."""
        state = [
            _make_elem(f"s{i}", allow_overlap=False, cx=100 + 60 * i) for i in range(3)
        ]
        new_state, err = add_scenography_element(
            state,
            "circle",
            _form_circle(400),
            True,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is None
        assert len(new_state) == 4

    def test_solid_ok_when_only_passable_at_max(self):
        """0 solid + 3 passable → can still add solid."""
        state = [
            _make_elem(f"p{i}", allow_overlap=True, cx=100 + 60 * i) for i in range(3)
        ]
        new_state, err = add_scenography_element(
            state,
            "circle",
            _form_circle(400),
            False,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is None
        assert len(new_state) == 4


# ── update_scenography_element limits ───────────────────────────────────────


class TestUpdateScenographyLimits:
    def test_update_same_category_ok(self):
        """Updating a solid element to stay solid → always ok."""
        state = [
            _make_elem("s0", allow_overlap=False, cx=100),
            _make_elem("s1", allow_overlap=False, cx=200),
            _make_elem("s2", allow_overlap=False, cx=300),
        ]
        new_state, err = update_scenography_element(
            state,
            "s0",
            "circle",
            _form_circle(150),
            False,
            _TABLE_W,
            _TABLE_H,
            "Updated",
        )
        assert err is None
        assert new_state[0]["data"]["cx"] == 150

    def test_switch_solid_to_passable_ok(self):
        """Switching a solid to passable when passable < max → ok."""
        state = [
            _make_elem("s0", allow_overlap=False, cx=100),
            _make_elem("s1", allow_overlap=False, cx=200),
            _make_elem("p0", allow_overlap=True, cx=400),
        ]
        new_state, err = update_scenography_element(
            state,
            "s0",
            "circle",
            _form_circle(150),
            True,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is None
        assert new_state[0]["allow_overlap"] is True

    def test_switch_to_passable_rejected_when_passable_full(self):
        """Can't switch solid→passable if passable already at 3."""
        state = [
            _make_elem("s0", allow_overlap=False, cx=100),
            _make_elem("p0", allow_overlap=True, cx=300),
            _make_elem("p1", allow_overlap=True, cx=400),
            _make_elem("p2", allow_overlap=True, cx=500),
        ]
        new_state, err = update_scenography_element(
            state,
            "s0",
            "circle",
            _form_circle(150),
            True,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is not None
        assert "passable" in err.lower() or str(_MAX_PASSABLE) in err
        assert new_state is state

    def test_switch_to_solid_rejected_when_solid_full(self):
        """Can't switch passable→solid if solid already at 3."""
        state = [
            _make_elem("s0", allow_overlap=False, cx=100),
            _make_elem("s1", allow_overlap=False, cx=200),
            _make_elem("s2", allow_overlap=False, cx=300),
            _make_elem("p0", allow_overlap=True, cx=500),
        ]
        new_state, err = update_scenography_element(
            state,
            "p0",
            "circle",
            _form_circle(550),
            False,
            _TABLE_W,
            _TABLE_H,
        )
        assert err is not None
        assert "solid" in err.lower() or str(_MAX_SOLID) in err
        assert new_state is state

    def test_constants_match(self):
        assert _MAX_SCENOGRAPHY == 6
        assert _MAX_SOLID == 3
        assert _MAX_PASSABLE == 3
