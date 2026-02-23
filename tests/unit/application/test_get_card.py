"""
RED tests for GetCard use case.

GetCard retrieves a Card by ID, enforcing visibility/authz rules.
Only users with read access can retrieve a card.

MVP Contract:
1. Happy path: card PRIVATE and actor==owner → returns snapshot
2. Not found → error
3. Forbidden: card PRIVATE owner="user_a" and actor="user_b" → error
4. actor_id invalid → ValidationError
5. card_id invalid (None, "", "   ") → ValidationError
6. Optional: PUBLIC allows read by non-owner
"""

from __future__ import annotations

from typing import Optional

import pytest

# Domain imports (real)
from domain.errors import ValidationError
from tests.unit.application.conftest import FakeCardRepository


# =============================================================================
# 1) HAPPY PATH - OWNER READS PRIVATE CARD
# =============================================================================
class TestGetCardHappyPath:
    """Card PRIVATE and actor==owner → returns snapshot."""

    def test_owner_can_read_private_card(
        self, repository_with_private_card: FakeCardRepository
    ):
        from application.use_cases.get_card import GetCard, GetCardRequest

        use_case = GetCard(repository=repository_with_private_card)
        request = GetCardRequest(
            actor_id="owner-123",  # Same as card.owner_id
            card_id="card-001",
        )

        response = use_case.execute(request)

        # Returns card data
        assert response.card_id == "card-001"
        assert response.owner_id == "owner-123"
        assert response.seed == 42
        assert response.mode == "matched"
        assert response.visibility == "private"


# =============================================================================
# 2) NOT FOUND
# =============================================================================
class TestGetCardNotFound:
    """Non-existent card raises NotFound error."""

    def test_card_not_found_raises_error(self, empty_repository: FakeCardRepository):
        from application.use_cases.get_card import GetCard, GetCardRequest

        use_case = GetCard(repository=empty_repository)
        request = GetCardRequest(
            actor_id="owner-123",
            card_id="nonexistent-card",
        )

        # Expect NotFound or similar error
        with pytest.raises(Exception, match="(?i)not.?found|does.?not.?exist"):
            use_case.execute(request)


# =============================================================================
# 3) FORBIDDEN - NON-OWNER READS PRIVATE CARD
# =============================================================================
class TestGetCardForbidden:
    """Card PRIVATE owner='user_a' and actor='user_b' → Forbidden."""

    def test_non_owner_cannot_read_private_card(
        self, repository_with_private_card: FakeCardRepository
    ):
        from application.use_cases.get_card import GetCard, GetCardRequest

        use_case = GetCard(repository=repository_with_private_card)
        request = GetCardRequest(
            actor_id="other-user",  # NOT the owner
            card_id="card-001",  # PRIVATE card owned by "owner-123"
        )

        with pytest.raises(Exception, match="(?i)forbidden|permission|access"):
            use_case.execute(request)


# =============================================================================
# 4) INVALID ACTOR_ID
# =============================================================================
class TestGetCardInvalidActorId:
    """Invalid actor_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_actor_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_actor_id_raises_error(
        self,
        repository_with_private_card: FakeCardRepository,
        invalid_actor_id: Optional[str],
    ):
        from application.use_cases.get_card import GetCard, GetCardRequest

        use_case = GetCard(repository=repository_with_private_card)
        request = GetCardRequest(
            actor_id=invalid_actor_id,
            card_id="card-001",
        )

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)


# =============================================================================
# 5) INVALID CARD_ID
# =============================================================================
class TestGetCardInvalidCardId:
    """Invalid card_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_card_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_card_id_raises_error(
        self,
        repository_with_private_card: FakeCardRepository,
        invalid_card_id: Optional[str],
    ):
        from application.use_cases.get_card import GetCard, GetCardRequest

        use_case = GetCard(repository=repository_with_private_card)
        request = GetCardRequest(
            actor_id="owner-123",
            card_id=invalid_card_id,
        )

        with pytest.raises(ValidationError, match="(?i)card"):
            use_case.execute(request)


# =============================================================================
# 6) PUBLIC CARD - NON-OWNER CAN READ
# =============================================================================
class TestGetCardPublicAccess:
    """PUBLIC card allows read by non-owner."""

    def test_non_owner_can_read_public_card(
        self, repository_with_public_card: FakeCardRepository
    ):
        from application.use_cases.get_card import GetCard, GetCardRequest

        use_case = GetCard(repository=repository_with_public_card)
        request = GetCardRequest(
            actor_id="other-user",  # NOT the owner
            card_id="card-002",  # PUBLIC card
        )

        response = use_case.execute(request)

        # Returns card data
        assert response.card_id == "card-002"
        assert response.visibility == "public"
