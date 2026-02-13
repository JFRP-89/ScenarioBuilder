"""Tests for _payload._rules — special rules application."""

from __future__ import annotations

from adapters.ui_gradio.builders._payload._rules import apply_special_rules


class TestApplySpecialRules:
    def test_empty_rules_returns_none(self):
        payload: dict = {}
        err = apply_special_rules(payload, [])
        assert err is None
        assert "special_rules" not in payload

    def test_valid_description_rule(self):
        payload: dict = {}
        rules = [{"name": "Rule1", "rule_type": "description", "value": "Desc1"}]
        err = apply_special_rules(payload, rules)
        assert err is None
        assert payload["special_rules"] == [{"name": "Rule1", "description": "Desc1"}]

    def test_valid_source_rule(self):
        payload: dict = {}
        rules = [{"name": "Rule2", "rule_type": "source", "value": "Src2"}]
        err = apply_special_rules(payload, rules)
        assert err is None
        assert payload["special_rules"] == [{"name": "Rule2", "source": "Src2"}]

    def test_missing_name_returns_error(self):
        payload: dict = {}
        rules = [{"name": "", "rule_type": "description", "value": "Val"}]
        err = apply_special_rules(payload, rules)
        assert err is not None
        assert err["status"] == "error"
        assert "Name" in err["message"]

    def test_invalid_rule_type_returns_error(self):
        payload: dict = {}
        rules = [{"name": "R", "rule_type": "invalid", "value": "V"}]
        err = apply_special_rules(payload, rules)
        assert err is not None
        assert "description or source" in err["message"]

    def test_empty_value_returns_error(self):
        payload: dict = {}
        rules = [{"name": "R", "rule_type": "description", "value": ""}]
        err = apply_special_rules(payload, rules)
        assert err is not None
        assert "empty" in err["message"]

    def test_multiple_valid_rules(self):
        payload: dict = {}
        rules = [
            {"name": "A", "rule_type": "description", "value": "D"},
            {"name": "B", "rule_type": "source", "value": "S"},
        ]
        err = apply_special_rules(payload, rules)
        assert err is None
        assert len(payload["special_rules"]) == 2
