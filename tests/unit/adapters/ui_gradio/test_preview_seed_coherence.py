"""Tests for seed coherence in handle_preview.

Rules (verified logic):
1. ``is_replicable=True`` + ``gfs`` set + form matches Apply-Seed
   output for that gfs → seed = gfs (verified, not forced).
2. ``is_replicable=True`` + ``gfs`` set + form does NOT match
   → seed = hash(form).
3. ``is_replicable=True`` + ``gfs`` NOT set → seed = hash(form).
4. ``is_replicable=False`` → seed = 0.
"""

from __future__ import annotations

from adapters.ui_gradio.services._generate._form_state import FormState
from adapters.ui_gradio.services.generate import handle_preview
from application.use_cases._generate._themes import _resolve_full_seed_defaults
from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


def _make_fs(**overrides: object) -> FormState:
    """Build a FormState with sensible defaults; override as needed."""
    defaults = {
        "actor": "user-1",
        "name": "MyScenario",
        "mode": "casual",
        "is_replicable": True,
        "generate_from_seed": None,
        "armies_val": "ManualArmy",
        "preset": "standard",
        "width": 120.0,
        "height": 120.0,
        "unit": "cm",
        "depl": "ManualDeploy",
        "lay": "ManualLayout",
        "obj": "ManualObjective",
        "init_priority": "ManualPriority",
        "rules_state": [],
        "vis": "private",
        "shared": "",
        "scenography_state_val": [],
        "deployment_zones_state_val": [],
        "objective_points_state_val": [],
        "objectives_with_vp_enabled": False,
        "vp_state": [],
    }
    defaults.update(overrides)
    return FormState(**defaults)  # type: ignore[arg-type]


class TestPreviewSeedCoherence:
    """Preview seed follows the *verified* gfs-or-hash rule."""

    def test_gfs_unmatched_content_seed_is_hash(self):
        """When gfs is set but form doesn't match Apply Seed output,
        seed = hash(form), NOT gfs."""
        fs = _make_fs(
            generate_from_seed=42,
            armies_val="CustomArmy",
            depl="CustomDeploy",
            lay="CustomLayout",
            obj="CustomObjective",
            init_priority="CustomPriority",
        )
        result = handle_preview(fs)

        assert result["status"] == "preview"
        assert result["seed"] != 42  # NOT gfs — form doesn't match
        assert result["seed"] > 0
        assert result["armies"] == "CustomArmy"
        assert result["deployment"] == "CustomDeploy"

    def test_gfs_unmatched_another_value(self):
        """Manual content + gfs → seed = hash(form), NOT gfs."""
        fs = _make_fs(generate_from_seed=125126)
        result = handle_preview(fs)

        assert result["status"] == "preview"
        assert result["seed"] != 125126  # NOT gfs
        assert result["seed"] > 0
        assert result["armies"] == "ManualArmy"

    def test_gfs_verified_match_seed_equals_gfs(self):
        """When form content matches _resolve_full_seed_defaults(gfs),
        seed = gfs (verified, not forced).

        Simulates the full Apply Seed round-trip: API shapes → UI state
        → back to API format, so the hash matches correctly.
        """
        from adapters.ui_gradio._state._seed_sync import (
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
        )

        gfs = 42
        expected = _resolve_full_seed_defaults(gfs)

        # Simulate Apply Seed converting API shapes to Gradio UI state
        dep_ui = api_deployment_to_ui_state(expected["deployment_shapes"])
        obj_ui = api_objectives_to_ui_state(expected["objective_shapes"])
        scen_ui = api_scenography_to_ui_state(expected["scenography_specs"])

        fs = _make_fs(
            generate_from_seed=gfs,
            mode=expected["mode"],
            preset=expected["table_preset"],
            width=expected["table_width_mm"] / 10,
            height=expected["table_height_mm"] / 10,
            armies_val=expected["armies"],
            depl=expected["deployment"],
            lay=expected["layout"],
            obj=expected["objectives"],
            init_priority=expected["initial_priority"],
            rules_state=[],
            deployment_zones_state_val=dep_ui,
            objective_points_state_val=obj_ui,
            scenography_state_val=scen_ui,
        )
        result = handle_preview(fs)

        assert result["seed"] == gfs

    def test_gfs_verified_match_another_seed(self):
        """Verified match works for different seed values."""
        from adapters.ui_gradio._state._seed_sync import (
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
        )

        for gfs in [1, 100, 99999]:
            expected = _resolve_full_seed_defaults(gfs)
            dep_ui = api_deployment_to_ui_state(expected["deployment_shapes"])
            obj_ui = api_objectives_to_ui_state(expected["objective_shapes"])
            scen_ui = api_scenography_to_ui_state(expected["scenography_specs"])

            fs = _make_fs(
                generate_from_seed=gfs,
                mode=expected["mode"],
                preset=expected["table_preset"],
                width=expected["table_width_mm"] / 10,
                height=expected["table_height_mm"] / 10,
                armies_val=expected["armies"],
                depl=expected["deployment"],
                lay=expected["layout"],
                obj=expected["objectives"],
                init_priority=expected["initial_priority"],
                rules_state=[],
                deployment_zones_state_val=dep_ui,
                objective_points_state_val=obj_ui,
                scenography_state_val=scen_ui,
            )
            result = handle_preview(fs)
            assert (
                result["seed"] == gfs
            ), f"gfs={gfs}: expected verified match, got {result['seed']}"

    def test_gfs_with_same_content_different_mode_not_verified(self):
        """If only mode differs from expected → seed ≠ gfs."""
        from adapters.ui_gradio._state._seed_sync import (
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
        )

        gfs = 42
        expected = _resolve_full_seed_defaults(gfs)
        wrong_mode = "matched" if expected["mode"] != "matched" else "casual"

        dep_ui = api_deployment_to_ui_state(expected["deployment_shapes"])
        obj_ui = api_objectives_to_ui_state(expected["objective_shapes"])
        scen_ui = api_scenography_to_ui_state(expected["scenography_specs"])

        fs = _make_fs(
            generate_from_seed=gfs,
            mode=wrong_mode,
            preset=expected["table_preset"],
            width=expected["table_width_mm"] / 10,
            height=expected["table_height_mm"] / 10,
            armies_val=expected["armies"],
            depl=expected["deployment"],
            lay=expected["layout"],
            obj=expected["objectives"],
            init_priority=expected["initial_priority"],
            rules_state=[],
            deployment_zones_state_val=dep_ui,
            objective_points_state_val=obj_ui,
            scenography_state_val=scen_ui,
        )
        result = handle_preview(fs)

        assert result["seed"] != gfs

    def test_same_content_with_and_without_gfs_same_hash(self):
        """Same form content → same hash regardless of gfs (when unmatched)."""
        fs_with_gfs = _make_fs(generate_from_seed=99999)
        result_with = handle_preview(fs_with_gfs)

        fs_without = _make_fs(generate_from_seed=None)
        result_without = handle_preview(fs_without)

        # Both produce hash(form) since 99999 doesn't match manual content
        assert result_with["seed"] == result_without["seed"]
        assert result_with["seed"] > 0

    def test_no_gfs_seed_is_hash(self):
        """Without gfs, preview uses form values + hash seed."""
        fs = _make_fs(generate_from_seed=None, is_replicable=True)
        result = handle_preview(fs)

        assert result["status"] == "preview"
        assert result["seed"] > 0  # hash-based
        assert result["armies"] == "ManualArmy"
        assert result["deployment"] == "ManualDeploy"
        assert result["layout"] == "ManualLayout"
        assert result["initial_priority"] == "ManualPriority"
        assert result["name"] == "MyScenario"

    def test_non_replicable_seed_zero(self):
        """With is_replicable=False → seed=0."""
        fs = _make_fs(is_replicable=False, generate_from_seed=None)
        result = handle_preview(fs)

        assert result["status"] == "preview"
        assert result["seed"] == 0
        assert result["armies"] == "ManualArmy"

    def test_non_replicable_with_gfs_seed_zero(self):
        """Even with gfs set, non-replicable → seed=0."""
        fs = _make_fs(is_replicable=False, generate_from_seed=42)
        result = handle_preview(fs)

        assert result["seed"] == 0

    def test_shapes_always_from_form(self):
        """Shapes always reflect form state, never seed-derived shapes."""
        fs = _make_fs(
            generate_from_seed=42,
            armies_val="SeedArmy",
            depl="SeedDeploy",
            lay="SeedLayout",
            obj="SeedObjective",
            init_priority="SeedPriority",
        )
        result = handle_preview(fs)

        assert result["shapes"]["deployment_shapes"] == []
        assert result["shapes"]["objective_shapes"] == []
        assert result["shapes"]["scenography_specs"] == []

    def test_same_content_no_gfs_same_hash_reproducible(self):
        """Identical form content (no gfs) → same hash seed."""
        fs1 = _make_fs(is_replicable=True)
        fs2 = _make_fs(is_replicable=True)
        r1 = handle_preview(fs1)
        r2 = handle_preview(fs2)

        assert r1["seed"] == r2["seed"]
        assert r1["seed"] > 0

    def test_gfs_equals_content_hash_seed_is_hash(self):
        """When gfs == hash(form), seed = hash = gfs — same value.

        User scenario: create content manually, get hash X, type X
        in seed field → seed = X (actual_hash == gfs in both branches).
        """
        # Step 1: get the hash seed for this content (no gfs)
        fs_no_seed = _make_fs(is_replicable=True)
        result_no_seed = handle_preview(fs_no_seed)
        natural_hash = result_no_seed["seed"]
        assert natural_hash > 0

        # Step 2: type that hash back into the seed field
        fs_with_hash = _make_fs(
            generate_from_seed=natural_hash,
            is_replicable=True,
        )
        result_with_hash = handle_preview(fs_with_hash)

        # seed = gfs = hash — same value regardless of branch
        assert result_with_hash["seed"] == natural_hash
        assert result_with_hash["armies"] == "ManualArmy"

    def test_unmatched_gfs_values_produce_form_hash(self):
        """Each unmatched gfs value produces hash(form), NOT gfs."""
        for gfs in [1, 42, 99999, 219945847]:
            fs = _make_fs(generate_from_seed=gfs)
            result = handle_preview(fs)
            assert (
                result["seed"] != gfs
            ), f"gfs={gfs}: seed should be hash(form), not gfs"
            assert result["seed"] > 0


class TestApplySeedHashMatchConsistency:
    """The seed_config built in _apply_seed must hash identically to the
    one built in handle_preview for the same form content.

    This ensures the hash-match check in _apply_seed correctly detects
    when the form already contains the content for the entered seed,
    preventing unnecessary form replacement.
    """

    @staticmethod
    def _build_apply_seed_config(
        *,
        mode: str = "casual",
        preset: str = "standard",
        tw: float = 120.0,
        th: float = 120.0,
        armies: str | None = "ManualArmy",
        deployment: str | None = "ManualDeploy",
        layout: str | None = "ManualLayout",
        objectives: str | None = "ManualObjective",
        initial_priority: str | None = "ManualPriority",
        rules_state: list | None = None,
        dep_state: list | None = None,
        obj_state: list | None = None,
        scen_state: list | None = None,
    ) -> dict:
        """Build the same seed_config dict that _apply_seed constructs."""
        from adapters.ui_gradio.builders import shapes as shapes_builder

        dep_shapes = (
            shapes_builder.build_deployment_shapes_from_state(dep_state)
            if dep_state
            else []
        )
        obj_shapes = (
            shapes_builder.build_objective_shapes_from_state(obj_state)
            if obj_state
            else []
        )
        scen_specs = (
            shapes_builder.build_map_specs_from_state(scen_state) if scen_state else []
        )

        table_w = int(tw * 10) if tw and tw > 0 else 1200
        table_h = int(th * 10) if th and th > 0 else 1200

        return {
            "mode": mode or "casual",
            "table_preset": preset or "standard",
            "table_width_mm": table_w,
            "table_height_mm": table_h,
            "armies": armies.strip() if armies else None,
            "deployment": deployment.strip() if deployment else None,
            "layout": layout.strip() if layout else None,
            "objectives": objectives.strip() if objectives else None,
            "initial_priority": (
                initial_priority.strip() if initial_priority else None
            ),
            "special_rules": rules_state or None,
            "deployment_shapes": dep_shapes,
            "objective_shapes": obj_shapes,
            "scenography_specs": scen_specs,
        }

    def test_hash_matches_handle_preview_default_content(self):
        """_apply_seed hash matches handle_preview hash for default content."""
        fs = _make_fs(is_replicable=True)
        preview = handle_preview(fs)
        preview_seed = preview["seed"]

        apply_cfg = self._build_apply_seed_config()
        apply_hash = calculate_seed_from_config(apply_cfg)

        assert apply_hash == preview_seed

    def test_hash_matches_handle_preview_custom_content(self):
        """_apply_seed hash matches handle_preview hash for custom content."""
        fs = _make_fs(
            is_replicable=True,
            armies_val="Expedition Guard",
            depl="Tunnel fight",
            lay="Broken Bridge",
            obj="Claim the relic",
            init_priority="Protect the expedition",
        )
        preview = handle_preview(fs)
        preview_seed = preview["seed"]

        apply_cfg = self._build_apply_seed_config(
            armies="Expedition Guard",
            deployment="Tunnel fight",
            layout="Broken Bridge",
            objectives="Claim the relic",
            initial_priority="Protect the expedition",
        )
        apply_hash = calculate_seed_from_config(apply_cfg)

        assert apply_hash == preview_seed

    def test_hash_matches_for_all_test_content(self):
        """User scenario: all fields set to 'Test'."""
        fs = _make_fs(
            is_replicable=True,
            armies_val="Test",
            depl="Test",
            lay="Test",
            obj="Test",
            init_priority="Test",
        )
        preview = handle_preview(fs)
        preview_seed = preview["seed"]

        apply_cfg = self._build_apply_seed_config(
            armies="Test",
            deployment="Test",
            layout="Test",
            objectives="Test",
            initial_priority="Test",
        )
        apply_hash = calculate_seed_from_config(apply_cfg)

        assert apply_hash == preview_seed
        # User's expected behavior: typing this seed back → hash match → no change
        assert apply_hash > 0

    def test_different_content_different_hash(self):
        """Different form content must produce a different hash."""
        cfg_a = self._build_apply_seed_config(armies="Alpha")
        cfg_b = self._build_apply_seed_config(armies="Beta")

        hash_a = calculate_seed_from_config(cfg_a)
        hash_b = calculate_seed_from_config(cfg_b)

        assert hash_a != hash_b

    def test_hash_match_prevents_replacement_scenario(self):
        """Full round-trip: create content → get seed → hash check works.

        Simulates the user scenario:
        1. Fill form with "Test" → preview shows seed X
        2. Type X in Apply Seed field
        3. _apply_seed checks hash(current_form) == X → TRUE → no replacement
        """
        # Step 1: get the seed for "Test" content
        fs = _make_fs(
            is_replicable=True,
            armies_val="Test",
            depl="Test",
            lay="Test",
            obj="Test",
            init_priority="Test",
        )
        preview = handle_preview(fs)
        user_seed = preview["seed"]

        # Step 2: build seed_config same as _apply_seed would
        apply_cfg = self._build_apply_seed_config(
            armies="Test",
            deployment="Test",
            layout="Test",
            objectives="Test",
            initial_priority="Test",
        )

        # Step 3: verify hash match
        current_hash = calculate_seed_from_config(apply_cfg)
        assert current_hash == user_seed, (
            f"Hash mismatch: _apply_seed would compute {current_hash}, "
            f"but handle_preview produced {user_seed}. "
            "This means _apply_seed would NOT detect the match and "
            "would unnecessarily replace form content."
        )
