"""RED tests for UuidIdGenerator.

Tests the UUID-based implementation of IdGenerator for the modern API.
This generator produces unique card_ids using UUID4.
"""

from __future__ import annotations


# =============================================================================
# UNIQUENESS AND FORMAT TESTS
# =============================================================================
class TestUuidIdGeneratorUniqueness:
    """Tests for id uniqueness."""

    def test_generate_card_id_returns_non_empty_string(self) -> None:
        """generate_card_id returns a non-empty string."""
        from infrastructure.generators.uuid_id_generator import UuidIdGenerator

        # Arrange
        gen = UuidIdGenerator()

        # Act
        card_id = gen.generate_card_id()

        # Assert
        assert isinstance(card_id, str)
        assert card_id.strip() != ""

    def test_two_calls_return_different_ids(self) -> None:
        """Two consecutive calls return different ids."""
        from infrastructure.generators.uuid_id_generator import UuidIdGenerator

        # Arrange
        gen = UuidIdGenerator()

        # Act
        id1 = gen.generate_card_id()
        id2 = gen.generate_card_id()

        # Assert
        assert isinstance(id1, str) and id1.strip() != ""
        assert isinstance(id2, str) and id2.strip() != ""
        assert id1 != id2


class TestUuidIdGeneratorFormat:
    """Tests for UUID format (optional but useful)."""

    def test_id_has_uuid_hex_format(self) -> None:
        """Generated id has UUID4 hex format (32 hex characters)."""
        from infrastructure.generators.uuid_id_generator import UuidIdGenerator

        # Arrange
        gen = UuidIdGenerator()

        # Act
        card_id = gen.generate_card_id()

        # Assert - UUID4.hex format: 32 lowercase hex chars
        assert len(card_id) == 32
        assert all(c in "0123456789abcdef" for c in card_id.lower())


class TestUuidIdGeneratorRobustness:
    """Tests for robustness and collision resistance."""

    def test_no_duplicates_in_many_generations(self) -> None:
        """No duplicates when generating many ids."""
        from infrastructure.generators.uuid_id_generator import UuidIdGenerator

        # Arrange
        gen = UuidIdGenerator()
        n = 100

        # Act
        ids = [gen.generate_card_id() for _ in range(n)]

        # Assert - all unique
        assert len(set(ids)) == n

    def test_separate_instances_generate_different_ids(self) -> None:
        """Different generator instances produce different ids."""
        from infrastructure.generators.uuid_id_generator import UuidIdGenerator

        # Arrange
        gen1 = UuidIdGenerator()
        gen2 = UuidIdGenerator()

        # Act
        id1 = gen1.generate_card_id()
        id2 = gen2.generate_card_id()

        # Assert
        assert id1 != id2
