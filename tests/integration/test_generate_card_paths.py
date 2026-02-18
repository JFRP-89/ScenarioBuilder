"""Integration tests for GenerateScenarioCard — module-level helpers + execute paths.

Targets uncovered lines in generate_scenario_card.py:
- _resolve_visibility (None, str, enum)
- _resolve_special_rules (str, list, None, other)
- _generate_card_name (all branches)
- resolve_seed_preview & resolve_full_seed_scenario (seed ≤ 0, repo-aware)
- execute() — GFS path, replicable with seed, shapes from GFS, name from seed
"""

from __future__ import annotations

import pytest
from application.use_cases.generate_scenario_card import (
    GenerateScenarioCard,
    GenerateScenarioCardRequest,
    _generate_card_name,
    _resolve_mode,
    _resolve_special_rules,
    _resolve_visibility,
)
from domain.cards.card import GameMode
from domain.errors import ValidationError
from domain.security.authz import Visibility
from infrastructure.generators.secure_seed_generator import (
    SecureSeedGenerator,
)
from infrastructure.generators.uuid_id_generator import UuidIdGenerator
from infrastructure.repositories.in_memory_card_repository import (
    InMemoryCardRepository,
)
from infrastructure.scenario_generation.basic_scenario_generator import (
    BasicScenarioGenerator,
)


# ═════════════════════════════════════════════════════════════════════════════
# Module-level helpers
# ═════════════════════════════════════════════════════════════════════════════
class TestResolveVisibility:
    def test_none_returns_private(self) -> None:
        assert _resolve_visibility(None) == Visibility.PRIVATE

    def test_enum_passes_through(self) -> None:
        assert _resolve_visibility(Visibility.PUBLIC) == Visibility.PUBLIC

    def test_string_parsed(self) -> None:
        assert _resolve_visibility("public") == Visibility.PUBLIC


class TestResolveSpecialRules:
    def test_none_returns_none(self) -> None:
        assert _resolve_special_rules(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert _resolve_special_rules("") is None

    def test_string_wraps_in_dict(self) -> None:
        result = _resolve_special_rules("No shooting on turn 1")
        assert result == [
            {"name": "Custom Rule", "description": "No shooting on turn 1"}
        ]

    def test_list_passes_through(self) -> None:
        rules = [{"name": "A", "description": "B"}]
        assert _resolve_special_rules(rules) is rules

    def test_other_type_returns_none(self) -> None:
        assert _resolve_special_rules(42) is None  # type: ignore[arg-type]


class TestResolveMode:
    def test_enum_passes_through(self) -> None:
        assert _resolve_mode(GameMode.MATCHED) == GameMode.MATCHED

    def test_string_parsed(self) -> None:
        assert _resolve_mode("matched") == GameMode.MATCHED


class TestGenerateCardName:
    def test_both_layout_and_deployment(self) -> None:
        assert _generate_card_name("Shire", "Flanking") == "Battle for Shire"

    def test_layout_only(self) -> None:
        assert _generate_card_name("Shire", None) == "Battle for Shire"

    def test_deployment_only(self) -> None:
        assert _generate_card_name(None, "Flanking") == "Battle with Flanking"

    def test_neither(self) -> None:
        assert _generate_card_name(None, None) == "Battle Scenario"


# ═════════════════════════════════════════════════════════════════════════════
# Use case — seed preview & full resolution
# ═════════════════════════════════════════════════════════════════════════════
def _make_uc(repo: InMemoryCardRepository | None = None) -> GenerateScenarioCard:
    """Build use case with real generators and optional in-memory repo."""
    return GenerateScenarioCard(
        id_generator=UuidIdGenerator(),
        seed_generator=SecureSeedGenerator(),
        scenario_generator=BasicScenarioGenerator(),
        card_repository=repo,
    )


class TestResolveSeedPreview:
    def test_seed_zero_returns_empty_fields(self) -> None:
        uc = _make_uc()
        result = uc.resolve_seed_preview(0)
        assert result["armies"] == ""
        assert result["name"] == ""

    def test_negative_seed_returns_empty(self) -> None:
        uc = _make_uc()
        result = uc.resolve_seed_preview(-5)
        assert result["deployment"] == ""

    def test_positive_seed_from_themes(self) -> None:
        uc = _make_uc()
        result = uc.resolve_seed_preview(42)
        assert "name" in result
        assert result["name"] == ""  # themes don't set name


class TestResolveFullSeedScenario:
    def test_seed_zero_returns_empty(self) -> None:
        uc = _make_uc()
        result = uc.resolve_full_seed_scenario(0, 1200, 800)
        assert result["deployment_shapes"] == []
        assert result["name"] == ""

    def test_positive_seed_includes_shapes(self) -> None:
        uc = _make_uc()
        result = uc.resolve_full_seed_scenario(42, 1200, 800)
        assert "deployment_shapes" in result
        assert "scenography_specs" in result


# ═════════════════════════════════════════════════════════════════════════════
# Use case — execute()
# ═════════════════════════════════════════════════════════════════════════════
class TestGenerateScenarioCardExecute:
    def test_basic_non_replicable(self) -> None:
        """Non-replicable card: seed should be 0."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=False,
        )
        resp = uc.execute(req)
        assert resp.seed == 0
        assert resp.card.owner_id == "player1"

    def test_replicable_with_seed(self) -> None:
        """Replicable card with explicit seed."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=12345,
            table_preset="standard",
            visibility="public",
            shared_with=None,
            is_replicable=True,
        )
        resp = uc.execute(req)
        assert resp.seed == 12345
        assert resp.is_replicable is True

    def test_replicable_without_seed_calculates(self) -> None:
        """Replicable card without explicit seed → calculated from content."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=True,
            armies="Gondor vs Mordor",
        )
        resp = uc.execute(req)
        assert resp.seed > 0

    def test_gfs_requires_replicable(self) -> None:
        """generate_from_seed without is_replicable → ValidationError."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=False,
            generate_from_seed=42,
        )
        with pytest.raises(ValidationError, match="Replicable"):
            uc.execute(req)

    def test_gfs_populates_content_from_seed(self) -> None:
        """generate_from_seed populates content fields from themes."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=True,
            generate_from_seed=42,
        )
        resp = uc.execute(req)
        # Should have auto-generated shapes
        assert "deployment_shapes" in resp.shapes

    def test_gfs_with_user_shapes_override(self) -> None:
        """user-provided shapes override GFS shapes."""
        uc = _make_uc()
        user_scenography = [
            {"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}
        ]
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=True,
            generate_from_seed=42,
            scenography_specs=user_scenography,
        )
        resp = uc.execute(req)
        assert resp.shapes["scenography_specs"] == user_scenography

    def test_name_from_request(self) -> None:
        """Request with explicit name uses it."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=False,
            name="My Battle",
        )
        resp = uc.execute(req)
        assert resp.card.name == "My Battle"

    def test_special_rules_from_string(self) -> None:
        """String special_rules gets wrapped into list."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=False,
            special_rules="No magic",
        )
        resp = uc.execute(req)
        assert resp.special_rules == [
            {"name": "Custom Rule", "description": "No magic"}
        ]

    def test_shared_with_visibility(self) -> None:
        """Shared card includes shared_with list."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="shared",
            shared_with=["player2"],
            is_replicable=False,
        )
        resp = uc.execute(req)
        assert resp.shared_with == ["player2"]

    def test_card_id_reused_when_provided(self) -> None:
        """Providing card_id in request reuses it (update flow)."""
        uc = _make_uc()
        req = GenerateScenarioCardRequest(
            actor_id="player1",
            mode="matched",
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=False,
            card_id="custom-id-123",
        )
        resp = uc.execute(req)
        assert resp.card_id == "custom-id-123"
