"""Integration test: Verify no auto-generation of scenography.

Tests that:
1. Creating a scenario without explicit shapes → no shapes in DB
2. Editing that scenario → no shapes appear automatically
3. Seed is consistent between preview and saved card
"""

import pytest
from application.use_cases._shape_normalization import (
    normalize_shapes_for_map_spec,
)
from application.use_cases.generate_scenario_card import (
    GenerateScenarioCardRequest,
)
from application.use_cases.get_card import GetCardRequest
from application.use_cases.save_card import SaveCardRequest
from domain.cards.card import Card, GameMode
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.bootstrap import build_services


@pytest.fixture
def services():
    """Build all services for integration testing."""
    return build_services()


class TestNoAutoScenography:
    """Verify that scenography is never auto-generated."""

    def test_create_without_shapes_saves_empty_scenography(self, services):
        """Creating scenario without explicit shapes → DB has no shapes."""
        actor_id = "user-123"

        # 1) Generate a scenario with seed but NO explicit shapes
        gen_req = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode=GameMode.CASUAL,
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,  # Replicable → seed > 0
            armies="Test Army",
            deployment="Test Deployment",
            layout="Test Layout",
            objectives="Test Objectives",
            # NO scenography_specs, map_specs, deployment_shapes, etc.
        )

        gen_resp = services.generate_scenario_card.execute(gen_req)

        # Verify preview has NO shapes
        assert gen_resp.shapes["scenography_specs"] == []
        assert gen_resp.shapes["deployment_shapes"] == []
        assert gen_resp.shapes["objective_shapes"] == []

        # 2) Save to DB
        table = TableSize(
            width_mm=gen_resp.table_mm["width_mm"],
            height_mm=gen_resp.table_mm["height_mm"],
        )
        all_shapes, objective_shapes = normalize_shapes_for_map_spec(gen_resp.shapes)
        map_spec = MapSpec(
            table=table, shapes=all_shapes, objective_shapes=objective_shapes
        )

        card = Card(
            card_id=gen_resp.card_id,
            owner_id=gen_resp.owner_id,
            visibility=Visibility(gen_resp.visibility),
            shared_with=None,
            mode=GameMode(gen_resp.mode),
            seed=gen_resp.seed,
            table=table,
            map_spec=map_spec,
        )

        services.save_card.execute(SaveCardRequest(actor_id=actor_id, card=card))

        # 3) Verify DB also has NO shapes
        get_req = GetCardRequest(actor_id=actor_id, card_id=gen_resp.card_id)
        get_resp = services.get_card.execute(get_req)

        assert get_resp.shapes["scenography_specs"] == []
        assert get_resp.shapes["deployment_shapes"] == []
        assert get_resp.shapes["objective_shapes"] == []

    def test_edit_scenario_preserves_no_shapes(self, services):
        """Editing scenario without shapes → shapes stay empty (no phantoms)."""
        actor_id = "user-123"

        # 1) Create initial scenario without shapes
        gen_req = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode=GameMode.CASUAL,
            seed=None,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            is_replicable=True,
            armies="Mordor",
            deployment="Black Gate",
        )

        gen_resp = services.generate_scenario_card.execute(gen_req)
        card_id = gen_resp.card_id

        # Verify initial has NO shapes
        assert gen_resp.shapes["scenography_specs"] == []

        # 2) Save initial card
        table = TableSize(
            width_mm=gen_resp.table_mm["width_mm"],
            height_mm=gen_resp.table_mm["height_mm"],
        )
        all_shapes, objective_shapes = normalize_shapes_for_map_spec(gen_resp.shapes)
        map_spec = MapSpec(
            table=table, shapes=all_shapes, objective_shapes=objective_shapes
        )

        card = Card(
            card_id=gen_resp.card_id,
            owner_id=gen_resp.owner_id,
            visibility=Visibility(gen_resp.visibility),
            shared_with=None,
            mode=GameMode(gen_resp.mode),
            seed=gen_resp.seed,
            table=table,
            map_spec=map_spec,
        )

        services.save_card.execute(SaveCardRequest(actor_id=actor_id, card=card))

        # 3) Verify saved card has NO shapes
        get_req = GetCardRequest(actor_id=actor_id, card_id=card_id)
        db_resp = services.get_card.execute(get_req)
        assert db_resp.shapes["scenography_specs"] == []
        assert db_resp.shapes["deployment_shapes"] == []
        assert db_resp.shapes["objective_shapes"] == []

    def test_seed_consistent_preview_to_db(self, services):
        """Seed remains consistent from preview to database."""
        actor_id = "user-123"

        # Create with replicable=True
        gen_req = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode=GameMode.MATCHED,
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=True,
            armies="Gondor",
            deployment="Minas Tirith",
        )

        # Generate (preview seed calculated)
        gen_resp = services.generate_scenario_card.execute(gen_req)
        preview_seed = gen_resp.seed

        assert preview_seed > 0  # Deterministic, not 0

        # Save to DB
        table = TableSize(
            width_mm=gen_resp.table_mm["width_mm"],
            height_mm=gen_resp.table_mm["height_mm"],
        )
        all_shapes, objective_shapes = normalize_shapes_for_map_spec(gen_resp.shapes)
        map_spec = MapSpec(
            table=table, shapes=all_shapes, objective_shapes=objective_shapes
        )

        card = Card(
            card_id=gen_resp.card_id,
            owner_id=gen_resp.owner_id,
            visibility=Visibility(gen_resp.visibility),
            shared_with=None,
            mode=GameMode(gen_resp.mode),
            seed=gen_resp.seed,
            table=table,
            map_spec=map_spec,
        )

        services.save_card.execute(SaveCardRequest(actor_id=actor_id, card=card))

        # Get from DB
        get_req = GetCardRequest(actor_id=actor_id, card_id=gen_resp.card_id)
        db_resp = services.get_card.execute(get_req)

        # Seeds must match
        assert db_resp.seed == preview_seed

    def test_manual_scenario_has_seed_zero_and_no_shapes(self, services):
        """Manual scenario (is_replicable=False) → seed=0, no shapes."""
        actor_id = "user-123"

        gen_req = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode=GameMode.CASUAL,
            seed=None,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            is_replicable=False,  # Manual = seed 0
            armies="Manual Army",
        )

        gen_resp = services.generate_scenario_card.execute(gen_req)

        # Manual scenarios have seed=0
        assert gen_resp.seed == 0

        # Manual scenarios have NO auto-generated shapes
        assert gen_resp.shapes["scenography_specs"] == []
        assert gen_resp.shapes["deployment_shapes"] == []
        assert gen_resp.shapes["objective_shapes"] == []
