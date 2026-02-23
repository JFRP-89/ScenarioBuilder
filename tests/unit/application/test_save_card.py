"""
RED tests for SaveCard use case.

SaveCard persists a Card entity to the repository.
Only the card owner can save their own card.

MVP Contract:
1. Happy path: actor == owner → saves and returns card_id
2. actor_id invalid (None, "", "   ") → ValidationError
3. actor != owner → Forbidden (Exception)
"""

from __future__ import annotations

from typing import Optional

import pytest

# Domain imports (real)
from domain.cards.card import Card
from domain.errors import ValidationError
from tests.unit.application.conftest import FakeCardRepository


# =============================================================================
# 1) HAPPY PATH
# =============================================================================
class TestSaveCardHappyPath:
    """Actor == owner → saves and returns card_id."""

    def test_saves_card_when_actor_is_owner(
        self, valid_card: Card, fake_repository: FakeCardRepository
    ):
        # Lazy import - will fail in RED phase
        from application.use_cases.save_card import SaveCard, SaveCardRequest

        use_case = SaveCard(repository=fake_repository)
        request = SaveCardRequest(
            actor_id="owner-123",  # Same as card.owner_id
            card=valid_card,
        )

        result = use_case.execute(request)

        # Card was saved
        assert len(fake_repository.save_calls) == 1
        assert fake_repository.save_calls[0] == valid_card
        # Returns card_id
        assert result.card_id == "card-001"


# =============================================================================
# 2) INVALID ACTOR_ID
# =============================================================================
class TestSaveCardInvalidActorId:
    """Invalid actor_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_actor_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_actor_id_raises_error(
        self,
        valid_card: Card,
        fake_repository: FakeCardRepository,
        invalid_actor_id: Optional[str],
    ):
        from application.use_cases.save_card import SaveCard, SaveCardRequest

        use_case = SaveCard(repository=fake_repository)
        request = SaveCardRequest(
            actor_id=invalid_actor_id,
            card=valid_card,
        )

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)

        # Card was NOT saved
        assert len(fake_repository.save_calls) == 0


# =============================================================================
# 3) FORBIDDEN: ACTOR != OWNER
# =============================================================================
class TestSaveCardForbidden:
    """Actor != owner raises Forbidden error."""

    def test_actor_not_owner_raises_forbidden(
        self, valid_card: Card, fake_repository: FakeCardRepository
    ):
        from application.use_cases.save_card import SaveCard, SaveCardRequest

        use_case = SaveCard(repository=fake_repository)
        request = SaveCardRequest(
            actor_id="other-user",  # NOT the owner
            card=valid_card,
        )

        # Expect some kind of forbidden/permission error
        with pytest.raises(Exception, match="(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        # Card was NOT saved
        assert len(fake_repository.save_calls) == 0
