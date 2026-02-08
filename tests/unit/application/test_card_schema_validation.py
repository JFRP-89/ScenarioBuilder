"""
Integration tests for the full card schema (min/max JSON examples).

Tests that the GenerateScenarioCard use case accepts both the minimum
and maximum card structures as described in the production schema.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from application.use_cases.generate_scenario_card import (
    GenerateScenarioCard,
    GenerateScenarioCardRequest,
)
from domain.cards.card import GameMode
from domain.errors import ValidationError
from domain.maps.table_size import TableSize


# =============================================================================
# TEST DOUBLES
# =============================================================================
class FakeIdGenerator:
    def __init__(self, card_id: str = "test-card-001") -> None:
        self._card_id = card_id

    def generate_card_id(self) -> str:
        return self._card_id


class FakeSeedGenerator:
    def __init__(self, seed: int = 999) -> None:
        self._seed = seed

    def generate_seed(self) -> int:
        return self._seed


@dataclass
class StubScenarioGenerator:
    shapes: list[dict]

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        return self.shapes


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def use_case():
    return GenerateScenarioCard(
        id_generator=FakeIdGenerator(),
        seed_generator=FakeSeedGenerator(),
        scenario_generator=StubScenarioGenerator(shapes=[]),
    )


# =============================================================================
# MINIMUM JSON SCHEMA
# =============================================================================
class TestMinimumJsonSchema:
    """The minimum valid card should be accepted."""

    def test_minimum_card_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="demo-user",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility="private",
            shared_with=None,
            name="a",
            armies="a",
            layout="a",
            deployment="a",
            initial_priority="a",
            objectives="a",
            special_rules=None,
        )

        response = use_case.execute(request)

        assert response.card_id == "test-card-001"
        assert response.seed == 1
        assert response.owner_id == "demo-user"
        assert response.name == "a"
        assert response.mode == "casual"
        assert response.visibility == "private"
        assert response.table_mm == {"width_mm": 1200, "height_mm": 1200}
        assert response.table_preset == "standard"
        assert response.shapes == {
            "deployment_shapes": [],
            "objective_shapes": [],
            "scenography_specs": [],
        }
        assert response.special_rules is None
        assert response.shared_with == []
        assert response.objectives == "a"

    def test_minimum_card_with_defaults(self, use_case):
        """Minimum with only required fields — defaults applied."""
        request = GenerateScenarioCardRequest(
            actor_id="demo-user",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
        )

        response = use_case.execute(request)
        assert response.visibility == "private"
        assert response.name == "Battle Scenario"


# =============================================================================
# MAXIMUM JSON SCHEMA
# =============================================================================
class TestMaximumJsonSchema:
    """A fully-loaded card with all features should be accepted."""

    def test_maximum_card_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="demo-user",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility="shared",
            shared_with=["age1", "oli", "aoe02"],
            name="Reliquia de eras pasadas",
            armies="Se siguen las reglas para llevar a cabo ejércitos equilibrados",
            layout="El campo de batalla se enfoca en un mapa de ruinas",
            deployment="Cada ejército despliega en uno de los dos laterales",
            initial_priority="Se siguen las reglas habituales",
            objectives={
                "objective": "El objetivo es poseer la reliquia",
                "victory_points": [
                    "Se gana 1 de victoria por haber herido al general",
                    "Si se muere el general del ejército, se ganan 3 puntos",
                ],
            },
            special_rules=[
                {
                    "name": "Lluvia potente",
                    "description": "El alcance de las armas a distancia se ve reducida",
                },
                {
                    "name": "Un tiempo de héroes",
                    "source": "Consulta la página 30 del suplemento",
                },
            ],
            deployment_shapes=[
                {
                    "type": "rect",
                    "border": "north",
                    "description": "Ejército A",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 200,
                },
                {
                    "type": "polygon",
                    "corner": "south-west",
                    "description": "Ejército B",
                    "points": [
                        {"x": 0, "y": 1200},
                        {"x": 0, "y": 900},
                        {"x": 300, "y": 1200},
                    ],
                },
                {
                    "type": "polygon",
                    "corner": "south-east",
                    "description": "Ejército C",
                    "points": [
                        {"x": 1200, "y": 1200},
                        {"x": 1200, "y": 900},
                        {"x": 900, "y": 1200},
                    ],
                },
            ],
            objective_shapes=[
                {"cx": 600, "cy": 600, "description": "Reliquia"},
            ],
            scenography_specs=[
                {
                    "type": "polygon",
                    "description": "Escombros",
                    "points": [
                        {"x": 600, "y": 300},
                        {"x": 1000, "y": 700},
                        {"x": 200, "y": 700},
                    ],
                },
                {
                    "type": "circle",
                    "description": "Ruinas 01",
                    "cx": 900,
                    "cy": 900,
                    "r": 150,
                },
                {
                    "type": "rect",
                    "description": "Ruinas 02",
                    "x": 300,
                    "y": 300,
                    "width": 400,
                    "height": 300,
                },
            ],
        )

        response = use_case.execute(request)

        # Core fields
        assert response.owner_id == "demo-user"
        assert response.name == "Reliquia de eras pasadas"
        assert response.mode == "casual"
        assert response.visibility == "shared"
        assert response.shared_with == ["age1", "oli", "aoe02"]

        # Objectives pass-through
        assert response.objectives == {
            "objective": "El objetivo es poseer la reliquia",
            "victory_points": [
                "Se gana 1 de victoria por haber herido al general",
                "Si se muere el general del ejército, se ganan 3 puntos",
            ],
        }

        # Special rules pass-through
        assert response.special_rules == [
            {
                "name": "Lluvia potente",
                "description": "El alcance de las armas a distancia se ve reducida",
            },
            {
                "name": "Un tiempo de héroes",
                "source": "Consulta la página 30 del suplemento",
            },
        ]

        # Shapes structure
        assert len(response.shapes["deployment_shapes"]) == 3
        assert len(response.shapes["objective_shapes"]) == 1
        assert len(response.shapes["scenography_specs"]) == 3


# =============================================================================
# DEPLOYMENT SHAPES LIMITS
# =============================================================================
class TestDeploymentShapesLimits:
    """Deployment shapes: max 4, border XOR corner."""

    def test_five_deployment_shapes_rejected(self, use_case):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "x": 0,
                "y": i * 200,
                "width": 1200,
                "height": 100,
            }
            for i in range(5)
        ]
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            deployment_shapes=shapes,
        )
        with pytest.raises(ValidationError, match="(?i)too many deployment"):
            use_case.execute(request)

    def test_deployment_shape_with_both_border_and_corner_rejected(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            deployment_shapes=[
                {
                    "type": "rect",
                    "border": "north",
                    "corner": "south-east",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 200,
                },
            ],
        )
        with pytest.raises(ValidationError, match="(?i)not both"):
            use_case.execute(request)

    def test_deployment_shape_without_border_or_corner_rejected(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            deployment_shapes=[
                {
                    "type": "rect",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 200,
                },
            ],
        )
        with pytest.raises(ValidationError, match="(?i)either.*border.*corner"):
            use_case.execute(request)


# =============================================================================
# OBJECTIVE SHAPES LIMIT (MAX 10)
# =============================================================================
class TestObjectiveShapesLimit:
    """Objective shapes: max 10."""

    def test_ten_objective_shapes_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objective_shapes=[{"cx": 100 + i * 50, "cy": 100} for i in range(10)],
        )
        response = use_case.execute(request)
        assert len(response.shapes["objective_shapes"]) == 10

    def test_eleven_objective_shapes_rejected(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objective_shapes=[{"cx": 100 + i * 50, "cy": 100} for i in range(11)],
        )
        with pytest.raises(ValidationError, match="(?i)too many objective"):
            use_case.execute(request)


# =============================================================================
# OBJECTIVES VALIDATION VIA USE CASE
# =============================================================================
class TestObjectivesValidation:
    """Objectives validated in the use case."""

    def test_objectives_as_string_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objectives="Destroy the enemy",
        )
        response = use_case.execute(request)
        assert response.objectives == "Destroy the enemy"

    def test_objectives_as_dict_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objectives={
                "objective": "Hold the relic",
                "victory_points": ["1 VP for wound", "3 VP for kill"],
            },
        )
        response = use_case.execute(request)
        assert response.objectives["objective"] == "Hold the relic"

    def test_invalid_objectives_type_rejected(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            objectives=42,
        )
        with pytest.raises(
            ValidationError, match="(?i)objectives must be a string or dict"
        ):
            use_case.execute(request)


# =============================================================================
# SPECIAL RULES VALIDATION VIA USE CASE
# =============================================================================
class TestSpecialRulesValidation:
    """Special rules validated in the use case."""

    def test_special_rules_as_list_of_dicts_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            special_rules=[
                {"name": "Heavy Rain", "description": "Range halved"},
            ],
        )
        response = use_case.execute(request)
        assert len(response.special_rules) == 1
        assert response.special_rules[0]["name"] == "Heavy Rain"

    def test_special_rules_missing_name_rejected(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility=None,
            shared_with=None,
            special_rules=[{"description": "No name provided"}],
        )
        with pytest.raises(ValidationError, match="(?i)must have.*name"):
            use_case.execute(request)


# =============================================================================
# SHARED_WITH VISIBILITY COHERENCE VIA USE CASE
# =============================================================================
class TestSharedWithVisibilityCoherence:
    """shared_with requires visibility='shared'."""

    def test_shared_with_and_shared_visibility_accepted(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility="shared",
            shared_with=["user2", "user3"],
        )
        response = use_case.execute(request)
        assert response.visibility == "shared"
        assert response.shared_with == ["user2", "user3"]

    def test_shared_with_and_private_visibility_rejected(self, use_case):
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility="private",
            shared_with=["user2"],
        )
        with pytest.raises(
            ValidationError,
            match="(?i)shared_with requires visibility to be.*shared",
        ):
            use_case.execute(request)

    def test_empty_shared_with_and_private_visibility_accepted(self, use_case):
        """Empty shared_with should not force shared visibility."""
        request = GenerateScenarioCardRequest(
            actor_id="user-1",
            mode="casual",
            seed=1,
            table_preset="standard",
            visibility="private",
            shared_with=[],
        )
        response = use_case.execute(request)
        assert response.visibility == "private"
