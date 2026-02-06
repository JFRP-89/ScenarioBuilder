"""
Unit tests for special rules helpers in Gradio UI adapter.

After refactoring:
- _validate_special_rules → builders.payload.apply_special_rules
  (mutates payload in-place, returns ErrorDict | None)
- _add_special_rule → state_helpers.add_special_rule
- _remove_last_special_rule → state_helpers.remove_last_special_rule
"""

from __future__ import annotations


class TestApplySpecialRules:
    """Tests for builders.payload.apply_special_rules()."""

    def test_empty_list_returns_none_and_no_payload_key(self):
        """Empty rules_state returns None (no error) and no special_rules key."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        payload: dict = {}
        error = apply_special_rules(payload, [])
        assert error is None
        assert "special_rules" not in payload

    def test_valid_rule_with_description(self):
        """Valid rule with description type normalizes to payload."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {
                "id": "rule1",
                "name": "Heroic Defence",
                "rule_type": "description",
                "value": "All warriors gain +1 defense",
            }
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is None
        assert payload["special_rules"] == [
            {"name": "Heroic Defence", "description": "All warriors gain +1 defense"}
        ]

    def test_valid_rule_with_source(self):
        """Valid rule with source type normalizes to payload."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {
                "id": "rule2",
                "name": "Close Combat",
                "rule_type": "source",
                "value": "Rulebook p.45",
            }
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is None
        assert payload["special_rules"] == [
            {"name": "Close Combat", "source": "Rulebook p.45"}
        ]

    def test_multiple_valid_rules(self):
        """Multiple valid rules are normalized into payload."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {
                "id": "r1",
                "name": "Rule A",
                "rule_type": "description",
                "value": "Desc A",
            },
            {"id": "r2", "name": "Rule B", "rule_type": "source", "value": "Source B"},
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is None
        assert len(payload["special_rules"]) == 2
        assert payload["special_rules"][0] == {
            "name": "Rule A",
            "description": "Desc A",
        }
        assert payload["special_rules"][1] == {"name": "Rule B", "source": "Source B"}

    def test_missing_name_returns_error(self):
        """Rule without name returns error dict."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {"id": "r1", "name": "", "rule_type": "description", "value": "V"}
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is not None
        assert error["status"] == "error"
        assert error["message"] == "Rule 1: Name is required"

    def test_missing_rule_type_returns_error(self):
        """Rule without rule_type returns error dict."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [{"id": "r1", "name": "Name", "rule_type": "", "value": "V"}]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is not None
        assert error["message"] == "Rule 1: Must specify description or source"

    def test_invalid_rule_type_returns_error(self):
        """Rule with invalid rule_type returns error dict."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {"id": "r1", "name": "Name", "rule_type": "invalid", "value": "V"}
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is not None
        assert error["message"] == "Rule 1: Must specify description or source"

    def test_missing_value_returns_error(self):
        """Rule without value returns error dict."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {"id": "r1", "name": "Name", "rule_type": "description", "value": ""}
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is not None
        assert error["message"] == "Rule 1: Value cannot be empty"

    def test_error_message_includes_rule_index(self):
        """Error message includes 1-based rule index."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {"id": "r1", "name": "Valid", "rule_type": "description", "value": "V"},
            {
                "id": "r2",
                "name": "Invalid",
                "rule_type": "description",
                "value": "",
            },
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is not None
        assert "Rule 2:" in error["message"]

    def test_whitespace_in_fields_is_stripped(self):
        """Whitespace is stripped from name, rule_type, value."""
        from adapters.ui_gradio.builders.payload import apply_special_rules

        rules_state = [
            {
                "id": "r1",
                "name": "  Name  ",
                "rule_type": " description ",
                "value": "  Value  ",
            }
        ]

        payload: dict = {}
        error = apply_special_rules(payload, rules_state)

        assert error is None
        assert payload["special_rules"] == [{"name": "Name", "description": "Value"}]


class TestAddSpecialRule:
    """Tests for state_helpers.add_special_rule()."""

    def test_adds_new_rule_to_empty_state(self):
        """Adding to empty state returns list with one rule."""
        from adapters.ui_gradio.state_helpers import add_special_rule

        result = add_special_rule([], rule_type="description")

        assert len(result) == 1
        assert result[0]["name"] == "New Rule"
        assert result[0]["rule_type"] == "description"
        assert result[0]["value"] == ""
        assert "id" in result[0]

    def test_adds_new_rule_to_existing_state(self):
        """Adding to existing state appends new rule."""
        from adapters.ui_gradio.state_helpers import add_special_rule

        existing = [
            {"id": "r1", "name": "Existing", "rule_type": "source", "value": "V"}
        ]
        result = add_special_rule(existing, rule_type="description")

        assert len(result) == 2
        assert result[0] == existing[0]
        assert result[1]["name"] == "New Rule"

    def test_default_rule_type_is_description(self):
        """Default rule_type is 'description'."""
        from adapters.ui_gradio.state_helpers import add_special_rule

        result = add_special_rule([])

        assert result[0]["rule_type"] == "description"

    def test_can_specify_source_rule_type(self):
        """Can specify rule_type='source'."""
        from adapters.ui_gradio.state_helpers import add_special_rule

        result = add_special_rule([], rule_type="source")

        assert result[0]["rule_type"] == "source"

    def test_generates_unique_id(self):
        """Each new rule gets a unique ID."""
        from adapters.ui_gradio.state_helpers import add_special_rule

        result1 = add_special_rule([])
        result2 = add_special_rule(result1)

        assert result1[0]["id"] != result2[1]["id"]

    def test_does_not_mutate_original_state(self):
        """Original state list is not mutated."""
        from adapters.ui_gradio.state_helpers import add_special_rule

        original = [
            {"id": "r1", "name": "Rule", "rule_type": "description", "value": "V"}
        ]
        original_copy = original.copy()

        add_special_rule(original)

        assert original == original_copy


class TestRemoveLastSpecialRule:
    """Tests for state_helpers.remove_last_special_rule()."""

    def test_removes_last_rule_from_state(self):
        """Removes the last rule from state."""
        from adapters.ui_gradio.state_helpers import remove_last_special_rule

        state = [
            {"id": "r1", "name": "Rule 1", "rule_type": "description", "value": "V1"},
            {"id": "r2", "name": "Rule 2", "rule_type": "description", "value": "V2"},
        ]

        result = remove_last_special_rule(state)

        assert len(result) == 1
        assert result[0]["id"] == "r1"

    def test_empty_state_returns_empty_list(self):
        """Removing from empty state returns []."""
        from adapters.ui_gradio.state_helpers import remove_last_special_rule

        result = remove_last_special_rule([])
        assert result == []

    def test_single_rule_state_returns_empty_list(self):
        """Removing last rule from single-rule state returns []."""
        from adapters.ui_gradio.state_helpers import remove_last_special_rule

        state = [{"id": "r1", "name": "Rule", "rule_type": "description", "value": "V"}]
        result = remove_last_special_rule(state)

        assert result == []

    def test_does_not_mutate_original_state(self):
        """Original state list is not mutated."""
        from adapters.ui_gradio.state_helpers import remove_last_special_rule

        original = [
            {"id": "r1", "name": "Rule 1", "rule_type": "description", "value": "V1"},
            {"id": "r2", "name": "Rule 2", "rule_type": "description", "value": "V2"},
        ]
        original_copy = original.copy()

        remove_last_special_rule(original)

        assert original == original_copy
