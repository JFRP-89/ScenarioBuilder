"""
Unit tests for card content validation (objectives, special_rules, shared_with).

Tests for:
- validate_objectives: None, str, dict with objective + victory_points
- validate_special_rules: None, list of dicts with name + description/source
- validate_shared_with_visibility: shared_with coherence with visibility
"""

from __future__ import annotations

import pytest

from domain.cards.card_content_validation import (
    validate_objectives,
    validate_shared_with_visibility,
    validate_special_rules,
)
from domain.errors import ValidationError
from domain.security.authz import Visibility


# =============================================================================
# OBJECTIVES VALIDATION
# =============================================================================
class TestValidateObjectives:
    """Tests for validate_objectives()."""

    def test_none_is_valid(self):
        validate_objectives(None)

    def test_string_is_valid(self):
        validate_objectives("Simple objective description")

    def test_empty_string_is_valid(self):
        validate_objectives("")

    def test_dict_with_objective_only(self):
        validate_objectives({"objective": "Get the relic"})

    def test_dict_with_objective_and_victory_points(self):
        validate_objectives(
            {
                "objective": "Get the relic",
                "victory_points": [
                    "1 VP for wounding enemy general",
                    "3 VP for killing enemy general",
                ],
            }
        )

    def test_dict_with_objective_and_empty_victory_points(self):
        validate_objectives({"objective": "Get the relic", "victory_points": []})

    def test_dict_with_objective_and_none_victory_points(self):
        validate_objectives({"objective": "Get the relic", "victory_points": None})

    def test_dict_missing_objective_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)objectives dict must have.*objective.*key"
        ):
            validate_objectives({"victory_points": ["1 VP"]})

    def test_dict_objective_not_string_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)objectives.objective must be a string"
        ):
            validate_objectives({"objective": 123})

    def test_victory_points_not_list_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)victory_points must be a list"
        ):
            validate_objectives(
                {"objective": "Get it", "victory_points": "not a list"}
            )

    def test_victory_points_item_not_string_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)victory_points must contain only strings"
        ):
            validate_objectives({"objective": "Get it", "victory_points": [123]})

    def test_invalid_type_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)objectives must be a string or dict"
        ):
            validate_objectives(42)

    def test_list_type_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)objectives must be a string or dict"
        ):
            validate_objectives(["not", "valid"])


# =============================================================================
# SPECIAL RULES VALIDATION
# =============================================================================
class TestValidateSpecialRules:
    """Tests for validate_special_rules()."""

    def test_none_is_valid(self):
        validate_special_rules(None)

    def test_empty_list_is_valid(self):
        validate_special_rules([])

    def test_single_rule_with_description(self):
        validate_special_rules(
            [{"name": "Heavy Rain", "description": "Range halved"}]
        )

    def test_single_rule_with_source(self):
        validate_special_rules(
            [{"name": "A Time of Heroes", "source": "Matched Play Guide p.30"}]
        )

    def test_rule_with_name_only(self):
        validate_special_rules([{"name": "Custom Rule"}])

    def test_rule_with_both_description_and_source(self):
        validate_special_rules(
            [
                {
                    "name": "Heavy Rain",
                    "description": "Range halved",
                    "source": "Core Rules p.12",
                }
            ]
        )

    def test_multiple_rules(self):
        validate_special_rules(
            [
                {"name": "Heavy Rain", "description": "Range halved"},
                {"name": "A Time of Heroes", "source": "MPG p.30"},
            ]
        )

    def test_not_list_raises(self):
        with pytest.raises(
            ValidationError, match="(?i)special_rules must be a list or null"
        ):
            validate_special_rules("not a list")

    def test_element_not_dict_raises(self):
        with pytest.raises(
            ValidationError, match=r"special_rules\[0\] must be a dict"
        ):
            validate_special_rules(["not a dict"])

    def test_missing_name_raises(self):
        with pytest.raises(
            ValidationError, match=r"special_rules\[0\] must have 'name'"
        ):
            validate_special_rules([{"description": "No name"}])

    def test_name_not_string_raises(self):
        with pytest.raises(
            ValidationError, match=r"special_rules\[0\]\.name must be a string"
        ):
            validate_special_rules([{"name": 123}])

    def test_empty_name_raises(self):
        with pytest.raises(
            ValidationError, match=r"special_rules\[0\]\.name cannot be empty"
        ):
            validate_special_rules([{"name": "   "}])

    def test_description_not_string_raises(self):
        with pytest.raises(
            ValidationError,
            match=r"special_rules\[0\]\.description must be a string",
        ):
            validate_special_rules([{"name": "Rule", "description": 123}])

    def test_source_not_string_raises(self):
        with pytest.raises(
            ValidationError, match=r"special_rules\[0\]\.source must be a string"
        ):
            validate_special_rules([{"name": "Rule", "source": 123}])


# =============================================================================
# SHARED_WITH / VISIBILITY COHERENCE
# =============================================================================
class TestValidateSharedWithVisibility:
    """Tests for validate_shared_with_visibility()."""

    def test_none_shared_with_is_valid_for_any_visibility(self):
        for vis in Visibility:
            validate_shared_with_visibility(vis, None)

    def test_empty_shared_with_is_valid_for_any_visibility(self):
        for vis in Visibility:
            validate_shared_with_visibility(vis, [])

    def test_shared_with_entries_and_shared_visibility_is_valid(self):
        validate_shared_with_visibility(Visibility.SHARED, ["user1", "user2"])

    def test_shared_with_entries_and_private_visibility_raises(self):
        with pytest.raises(
            ValidationError,
            match="(?i)shared_with requires visibility to be.*shared",
        ):
            validate_shared_with_visibility(Visibility.PRIVATE, ["user1"])

    def test_shared_with_entries_and_public_visibility_raises(self):
        with pytest.raises(
            ValidationError,
            match="(?i)shared_with requires visibility to be.*shared",
        ):
            validate_shared_with_visibility(Visibility.PUBLIC, ["user1"])
