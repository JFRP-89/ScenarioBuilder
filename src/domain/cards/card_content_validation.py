"""Validation helpers for card content (objectives, special_rules, shared_with).

These validators enforce business rules for card content fields that are
not part of the Card entity itself but are part of the full card schema.
"""

from __future__ import annotations

from domain.errors import ValidationError
from domain.security.authz import Visibility


def _validate_objectives_dict(objectives: dict) -> None:
    """Validate a dict-shaped objectives field."""
    if "objective" not in objectives:
        raise ValidationError("objectives dict must have 'objective' key")
    if not isinstance(objectives["objective"], str):
        raise ValidationError("objectives.objective must be a string")

    vp = objectives.get("victory_points")
    if vp is None:
        return

    if not isinstance(vp, list):
        raise ValidationError("victory_points must be a list")
    for item in vp:
        if not isinstance(item, str):
            raise ValidationError("victory_points must contain only strings")


def validate_objectives(objectives: object) -> None:
    """Validate objectives field.

    Objectives can be:
    - None (no objectives)
    - str (simple description)
    - dict with 'objective' (str) and optional 'victory_points' (list[str])

    Raises:
        ValidationError: If objectives is not a valid type or structure.
    """
    if objectives is None:
        return

    if isinstance(objectives, str):
        return

    if isinstance(objectives, dict):
        _validate_objectives_dict(objectives)
        return

    raise ValidationError("objectives must be a string or dict")


def _validate_single_rule(i: int, rule: object) -> None:
    """Validate a single special rule dict."""
    if not isinstance(rule, dict):
        raise ValidationError(f"special_rules[{i}] must be a dict")
    if "name" not in rule:
        raise ValidationError(f"special_rules[{i}] must have 'name'")
    if not isinstance(rule["name"], str):
        raise ValidationError(f"special_rules[{i}].name must be a string")
    if not rule["name"].strip():
        raise ValidationError(f"special_rules[{i}].name cannot be empty")

    if "description" in rule and not isinstance(rule["description"], str):
        raise ValidationError(f"special_rules[{i}].description must be a string")
    if "source" in rule and not isinstance(rule["source"], str):
        raise ValidationError(f"special_rules[{i}].source must be a string")


def validate_special_rules(special_rules: object) -> None:
    """Validate special_rules field.

    Special rules can be:
    - None (no special rules)
    - list of dicts, each with 'name' (required str) and optionally
      'description' (str) or 'source' (str)

    Raises:
        ValidationError: If special_rules is not valid.
    """
    if special_rules is None:
        return

    if not isinstance(special_rules, list):
        raise ValidationError("special_rules must be a list or null")

    for i, rule in enumerate(special_rules):
        _validate_single_rule(i, rule)


def validate_shared_with_visibility(
    visibility: Visibility, shared_with: object
) -> None:
    """Validate that shared_with is coherent with visibility.

    If shared_with is non-empty, visibility must be SHARED.

    Raises:
        ValidationError: If shared_with is non-empty but visibility is not SHARED.
    """
    if shared_with is None:
        return

    has_entries = False
    if isinstance(shared_with, (list, set, frozenset, tuple)):
        has_entries = len(shared_with) > 0

    if has_entries and visibility != Visibility.SHARED:
        raise ValidationError("shared_with requires visibility to be 'shared'")
