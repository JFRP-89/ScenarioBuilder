"""RED tests for infrastructure bootstrap / service wiring.

Tests the composition root that builds and wires all use cases
with their infrastructure dependencies.
"""

from __future__ import annotations

import pytest


# =============================================================================
# SMOKE TESTS
# =============================================================================
class TestBootstrapServicesSmoke:
    """Smoke tests for build_services construction."""

    def test_build_services_constructs_services_object(self) -> None:
        """build_services returns a Services object with use cases."""
        from infrastructure.bootstrap import build_services

        # Act
        services = build_services()

        # Assert - basic use cases exist
        assert hasattr(services, "generate_scenario_card")
        assert hasattr(services, "save_card")
        assert hasattr(services, "get_card")
        assert services.generate_scenario_card is not None
        assert services.save_card is not None
        assert services.get_card is not None


# =============================================================================
# INTEGRATION FLOW TESTS
# =============================================================================
class TestBootstrapServicesIntegrationFlow:
    """Tests for complete use case flows."""

    def test_generate_save_get_flow(self) -> None:
        """Complete flow: generate card → save → get retrieves same card."""
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

        # Arrange
        services = build_services()
        actor_id = "u1"

        # Generate a card with deterministic seed
        gen_request = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode="matched",
            table_preset="standard",
            seed=None,  # Will be calculated based on is_replicable
            is_replicable=True,  # Enable deterministic seed generation
            visibility="private",
            shared_with=None,
        )
        gen_response = services.generate_scenario_card.execute(gen_request)

        # Capture the generated seed (it's deterministic based on config)
        generated_seed = gen_response.seed

        # Build Card from response
        from application.use_cases._shape_normalization import (
            normalize_shapes_for_map_spec,
        )

        table = TableSize(
            width_mm=gen_response.table_mm["width_mm"],
            height_mm=gen_response.table_mm["height_mm"],
        )
        # Normalize shapes for MapSpec
        all_shapes, response_objective_shapes = normalize_shapes_for_map_spec(
            gen_response.shapes
        )
        map_spec = MapSpec(
            table=table, shapes=all_shapes, objective_shapes=response_objective_shapes
        )
        card = Card(
            card_id=gen_response.card_id,
            owner_id=gen_response.owner_id,
            visibility=Visibility(gen_response.visibility),
            shared_with=None,
            mode=GameMode(gen_response.mode),
            seed=gen_response.seed,
            table=table,
            map_spec=map_spec,
        )

        # Save the card
        save_request = SaveCardRequest(actor_id=actor_id, card=card)
        save_response = services.save_card.execute(save_request)
        assert save_response.card_id == card.card_id

        # Get the card back
        get_request = GetCardRequest(actor_id=actor_id, card_id=card.card_id)
        get_response = services.get_card.execute(get_request)

        card_out = getattr(get_response, "card", get_response)

        # Assert - retrieved card matches
        assert card_out.card_id == card.card_id
        assert card_out.owner_id == "u1"
        assert card_out.seed == generated_seed  # Seed should be preserved

    def test_services_share_repository_state(self) -> None:
        """Use cases share the same repository instance (state is preserved)."""
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

        # Arrange
        services = build_services()
        actor_id = "u1"

        # Generate and save a card
        gen_request = GenerateScenarioCardRequest(
            actor_id=actor_id,
            mode="matched",
            table_preset="standard",
            seed=456,
            visibility="private",
            shared_with=None,
        )
        gen_response = services.generate_scenario_card.execute(gen_request)

        # Build Card from response
        from application.use_cases._shape_normalization import (
            normalize_shapes_for_map_spec,
        )

        table = TableSize(
            width_mm=gen_response.table_mm["width_mm"],
            height_mm=gen_response.table_mm["height_mm"],
        )
        # Normalize shapes for MapSpec
        all_shapes, response_objective_shapes = normalize_shapes_for_map_spec(
            gen_response.shapes
        )
        map_spec = MapSpec(
            table=table, shapes=all_shapes, objective_shapes=response_objective_shapes
        )
        card = Card(
            card_id=gen_response.card_id,
            owner_id=gen_response.owner_id,
            visibility=Visibility(gen_response.visibility),
            shared_with=None,
            mode=GameMode(gen_response.mode),
            seed=gen_response.seed,
            table=table,
            map_spec=map_spec,
        )

        save_request = SaveCardRequest(actor_id=actor_id, card=card)
        services.save_card.execute(save_request)

        # Act - retrieve using get_card
        get_request = GetCardRequest(actor_id=actor_id, card_id=card.card_id)
        get_response = services.get_card.execute(get_request)

        card_out = getattr(get_response, "card", get_response)

        # Assert - card is found (repository state was preserved)
        assert card_out.card_id == card.card_id
        assert card_out.owner_id == actor_id

    def test_multiple_calls_to_build_services_create_independent_instances(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Multiple calls to build_services create independent service instances.

        Forces in-memory repositories via DATABASE_URL="" so each
        build_services() call creates truly independent repo instances.
        """
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

        # Force in-memory repos so instances are truly independent
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.delenv("DATABASE_URL_TEST", raising=False)

        # Arrange
        services1 = build_services()
        services2 = build_services()

        # Generate and save card in services1
        gen_request = GenerateScenarioCardRequest(
            actor_id="u1",
            mode="matched",
            table_preset="standard",
            seed=789,
            visibility="private",
            shared_with=None,
        )
        gen_response = services1.generate_scenario_card.execute(gen_request)

        # Build Card from response
        from application.use_cases._shape_normalization import (
            normalize_shapes_for_map_spec,
        )

        table = TableSize(
            width_mm=gen_response.table_mm["width_mm"],
            height_mm=gen_response.table_mm["height_mm"],
        )
        # Normalize shapes for MapSpec
        all_shapes, response_objective_shapes = normalize_shapes_for_map_spec(
            gen_response.shapes
        )
        map_spec = MapSpec(
            table=table, shapes=all_shapes, objective_shapes=response_objective_shapes
        )
        card = Card(
            card_id=gen_response.card_id,
            owner_id=gen_response.owner_id,
            visibility=Visibility(gen_response.visibility),
            shared_with=None,
            mode=GameMode(gen_response.mode),
            seed=gen_response.seed,
            table=table,
            map_spec=map_spec,
        )

        save_request = SaveCardRequest(actor_id="u1", card=card)
        services1.save_card.execute(save_request)

        # Act - try to get card from services2 (different instance)
        get_request = GetCardRequest(actor_id="u1", card_id=card.card_id)

        # Assert - services2 should not have the card (independent repositories)
        with pytest.raises(Exception) as excinfo:
            services2.get_card.execute(get_request)

        assert "not found" in str(excinfo.value).lower()


# =============================================================================
# OPTIONAL USE CASES (if implemented)
# =============================================================================
class TestBootstrapServicesOptionalUseCases:
    """Tests for optional use cases (if already implemented)."""

    def test_services_has_list_cards_if_implemented(self) -> None:
        """Services object has list_cards use case (optional)."""
        from infrastructure.bootstrap import build_services

        # Act
        services = build_services()

        # Assert - only check if attribute exists (may not be implemented yet)
        # This test documents the expected interface
        if hasattr(services, "list_cards"):
            assert services.list_cards is not None

    def test_services_has_favorites_use_cases_if_implemented(self) -> None:
        """Services object has favorites use cases (optional)."""
        from infrastructure.bootstrap import build_services

        # Act
        services = build_services()

        # Assert - document expected interface
        if hasattr(services, "toggle_favorite"):
            assert services.toggle_favorite is not None
        if hasattr(services, "list_favorites"):
            assert services.list_favorites is not None

    def test_services_has_create_variant_if_implemented(self) -> None:
        """Services object has create_variant use case (optional)."""
        from infrastructure.bootstrap import build_services

        # Act
        services = build_services()

        # Assert - document expected interface
        if hasattr(services, "create_variant"):
            assert services.create_variant is not None

    def test_services_has_render_map_svg_if_implemented(self) -> None:
        """Services object has render_map_svg use case (optional)."""
        from infrastructure.bootstrap import build_services

        # Act
        services = build_services()

        # Assert - document expected interface
        if hasattr(services, "render_map_svg"):
            assert services.render_map_svg is not None
