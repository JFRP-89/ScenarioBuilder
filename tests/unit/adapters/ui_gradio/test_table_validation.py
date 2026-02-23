"""Unit tests for _state._table_validation.check_all_shapes_fit_table."""

from __future__ import annotations

from adapters.ui_gradio._state._table_validation import check_all_shapes_fit_table

# ── helpers ──────────────────────────────────────────────────────────────────


def _rect_zone(x: int, y: int, w: int, h: int, label: str = "") -> dict:
    """Build a deployment-zone dict wrapping a rect data payload."""
    return {
        "id": "z1",
        "label": label or f"Zone ({x},{y},{w},{h})",
        "data": {"type": "rect", "x": x, "y": y, "width": w, "height": h},
    }


def _poly_zone(points: list[dict], label: str = "") -> dict:
    return {
        "id": "z2",
        "label": label or "Polygon zone",
        "data": {"type": "polygon", "points": points},
    }


def _obj_point(cx: float, cy: float, desc: str = "") -> dict:
    pt: dict = {"id": "o1", "cx": cx, "cy": cy}
    if desc:
        pt["description"] = desc
    return pt


def _scen_rect(x: int, y: int, w: int, h: int, label: str = "") -> dict:
    return {
        "id": "s1",
        "label": label or "Rect scenography",
        "data": {"type": "rect", "x": x, "y": y, "width": w, "height": h},
    }


def _scen_circle(cx: int, cy: int, r: int, label: str = "") -> dict:
    return {
        "id": "s2",
        "label": label or "Circle scenography",
        "data": {"type": "circle", "cx": cx, "cy": cy, "r": r},
    }


def _scen_polygon(points: list[dict], label: str = "") -> dict:
    return {
        "id": "s3",
        "label": label or "Polygon scenography",
        "data": {"type": "polygon", "points": points},
    }


# ── No shapes → always OK ───────────────────────────────────────────────────


class TestNoShapes:
    def test_empty_states_pass(self):
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[],
                objective_points=[],
                scenography=[],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )


# ── Deployment zones ────────────────────────────────────────────────────────


class TestDeploymentZones:
    def test_rect_fits(self):
        zone = _rect_zone(0, 0, 1200, 200)
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[zone],
                objective_points=[],
                scenography=[],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )

    def test_rect_exceeds_width(self):
        """Rect 1800 wide on a 1200 mm table → error."""
        zone = _rect_zone(0, 1000, 1800, 200, label="South zone")
        err = check_all_shapes_fit_table(
            deployment_zones=[zone],
            objective_points=[],
            scenography=[],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "South zone" in err
        assert "1200" in err

    def test_rect_exceeds_height(self):
        zone = _rect_zone(0, 1100, 1200, 200)
        err = check_all_shapes_fit_table(
            deployment_zones=[zone],
            objective_points=[],
            scenography=[],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None

    def test_polygon_fits(self):
        pts = [{"x": 0, "y": 0}, {"x": 1200, "y": 0}, {"x": 600, "y": 600}]
        zone = _poly_zone(pts)
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[zone],
                objective_points=[],
                scenography=[],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )

    def test_polygon_exceeds(self):
        pts = [{"x": 0, "y": 0}, {"x": 1800, "y": 0}, {"x": 900, "y": 600}]
        zone = _poly_zone(pts, label="Tri zone")
        err = check_all_shapes_fit_table(
            deployment_zones=[zone],
            objective_points=[],
            scenography=[],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "Tri zone" in err


# ── Objective points ────────────────────────────────────────────────────────


class TestObjectivePoints:
    def test_point_fits(self):
        pt = _obj_point(600, 600)
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[],
                objective_points=[pt],
                scenography=[],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )

    def test_point_exceeds_width(self):
        pt = _obj_point(1500, 600, desc="Flag")
        err = check_all_shapes_fit_table(
            deployment_zones=[],
            objective_points=[pt],
            scenography=[],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "1200" in err

    def test_point_exceeds_height(self):
        pt = _obj_point(600, 1500)
        err = check_all_shapes_fit_table(
            deployment_zones=[],
            objective_points=[pt],
            scenography=[],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None


# ── Scenography ─────────────────────────────────────────────────────────────


class TestScenography:
    def test_rect_fits(self):
        s = _scen_rect(100, 100, 200, 200)
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[],
                objective_points=[],
                scenography=[s],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )

    def test_rect_exceeds(self):
        s = _scen_rect(1000, 1000, 300, 300, label="Ruin")
        err = check_all_shapes_fit_table(
            deployment_zones=[],
            objective_points=[],
            scenography=[s],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "Ruin" in err

    def test_circle_fits(self):
        s = _scen_circle(600, 600, 100)
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[],
                objective_points=[],
                scenography=[s],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )

    def test_circle_exceeds(self):
        s = _scen_circle(1150, 600, 100, label="Pool")
        err = check_all_shapes_fit_table(
            deployment_zones=[],
            objective_points=[],
            scenography=[s],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "Pool" in err

    def test_polygon_fits(self):
        pts = [{"x": 100, "y": 100}, {"x": 300, "y": 100}, {"x": 200, "y": 300}]
        s = _scen_polygon(pts)
        assert (
            check_all_shapes_fit_table(
                deployment_zones=[],
                objective_points=[],
                scenography=[s],
                table_width_mm=1200,
                table_height_mm=1200,
            )
            is None
        )

    def test_polygon_exceeds(self):
        pts = [{"x": 100, "y": 100}, {"x": 1500, "y": 100}, {"x": 800, "y": 800}]
        s = _scen_polygon(pts, label="Forest")
        err = check_all_shapes_fit_table(
            deployment_zones=[],
            objective_points=[],
            scenography=[s],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "Forest" in err


# ── Priority order ──────────────────────────────────────────────────────────


class TestPriorityOrder:
    """Validation stops at the first failing category."""

    def test_deployment_reported_before_objectives(self):
        zone = _rect_zone(0, 0, 1800, 200, label="Wide zone")
        pt = _obj_point(1500, 600)
        err = check_all_shapes_fit_table(
            deployment_zones=[zone],
            objective_points=[pt],
            scenography=[],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "Wide zone" in err

    def test_objectives_reported_before_scenography(self):
        pt = _obj_point(1500, 600, desc="Flag")
        s = _scen_rect(1000, 1000, 300, 300, label="Ruin")
        err = check_all_shapes_fit_table(
            deployment_zones=[],
            objective_points=[pt],
            scenography=[s],
            table_width_mm=1200,
            table_height_mm=1200,
        )
        assert err is not None
        assert "Flag" in err


# ── Exact user scenario from the bug report ─────────────────────────────────


class TestUserScenario:
    """Reproduces the exact bug: massive→standard with 1800mm-wide zones."""

    def test_massive_zones_on_standard_table_rejected(self):
        zones = [
            _rect_zone(0, 1000, 1800, 200, label="South deployment"),
            _rect_zone(0, 0, 1800, 200, label="North deployment"),
        ]
        err = check_all_shapes_fit_table(
            deployment_zones=zones,
            objective_points=[],
            scenography=[],
            table_width_mm=1200,  # standard
            table_height_mm=1200,
        )
        assert err is not None
        assert "1200" in err

    def test_massive_zones_on_massive_table_accepted(self):
        zones = [
            _rect_zone(0, 1000, 1800, 200),
            _rect_zone(0, 0, 1800, 200),
        ]
        assert (
            check_all_shapes_fit_table(
                deployment_zones=zones,
                objective_points=[],
                scenography=[],
                table_width_mm=1800,
                table_height_mm=1200,
            )
            is None
        )
