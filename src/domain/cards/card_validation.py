"""Validation helpers for Card domain model."""

from __future__ import annotations

from typing import Any, cast

from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from domain.validation import validate_non_empty_str


def validate_seed(value: Any) -> int:
    """Validate seed is int >= 0, rejecting bool."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("seed must be int")
    if value < 0:
        raise ValidationError("seed must be >= 0")
    return cast(int, value)


def validate_ids(card_id: str, owner_id: str) -> None:
    validate_non_empty_str("card_id", card_id)
    validate_non_empty_str("owner_id", owner_id)


def validate_types(
    table: TableSize,
    map_spec: MapSpec,
    visibility: Visibility,
    mode: object,
    mode_type: type,
) -> None:
    if not isinstance(table, TableSize):
        raise ValidationError("table must be TableSize")
    if not isinstance(map_spec, MapSpec):
        raise ValidationError("map_spec must be MapSpec")
    if not isinstance(visibility, Visibility):
        raise ValidationError("visibility must be Visibility")
    if not isinstance(mode, mode_type):
        raise ValidationError("mode must be GameMode")


def validate_table_coherence(table: TableSize, map_spec: MapSpec) -> None:
    if map_spec.table.width_mm != table.width_mm or map_spec.table.height_mm != table.height_mm:
        raise ValidationError("map_spec.table dimensions must match table")
