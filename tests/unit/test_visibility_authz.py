"""
RED tests for Visibility enum and AuthZ helpers (anti-IDOR).

Visibility states:
- "private": only owner can read/write
- "shared": owner + allowlist can read, only owner can write
- "public": anyone can read, only owner can write

Authorization rules:
- can_read: based on visibility + ownership + shared_with
- can_write: only owner, regardless of visibility
- deny-by-default: invalid inputs raise errors, never return True
"""

from __future__ import annotations

import pytest
from domain.errors import ValidationError
from domain.security.authz import (
    Visibility,
    can_read,
    can_write,
    parse_visibility,
)


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def owner() -> str:
    return "user_a"


@pytest.fixture
def other() -> str:
    return "user_b"


@pytest.fixture
def friend() -> str:
    return "user_c"


@pytest.fixture
def blank() -> str:
    return "   "


# =============================================================================
# A) PARSING VISIBILITY
# =============================================================================
class TestParseVisibility:
    """Tests for parsing visibility strings into Visibility enum/value."""

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("private", Visibility.PRIVATE),
            ("shared", Visibility.SHARED),
            ("public", Visibility.PUBLIC),
        ],
    )
    def test_parse_valid_lowercase(self, input_value: str, expected: Visibility):
        """Valid lowercase strings should parse correctly."""
        result = parse_visibility(input_value)
        assert result == expected

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("PRIVATE", Visibility.PRIVATE),
            ("SHARED", Visibility.SHARED),
            ("PUBLIC", Visibility.PUBLIC),
            ("Private", Visibility.PRIVATE),
            ("Shared", Visibility.SHARED),
            ("Public", Visibility.PUBLIC),
            ("PrIvAtE", Visibility.PRIVATE),
        ],
    )
    def test_parse_case_insensitive(self, input_value: str, expected: Visibility):
        """Parsing should be case-insensitive and normalize to standard values."""
        result = parse_visibility(input_value)
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "friends",
            "unlisted",
            "secret",
            "restricted",
            "internal",
            "all",
            "none",
            "owner",
            "everyone",
            "unknown",
        ],
    )
    def test_parse_rejects_unknown_values(self, invalid_value: str):
        """Unknown visibility values should raise ValidationError."""
        with pytest.raises(ValidationError):
            parse_visibility(invalid_value)

    def test_parse_rejects_empty_string(self):
        """Empty string should raise ValidationError."""
        with pytest.raises(ValidationError):
            parse_visibility("")

    def test_parse_rejects_whitespace_only(self):
        """Whitespace-only string should raise ValidationError."""
        with pytest.raises(ValidationError):
            parse_visibility("   ")

    def test_parse_rejects_none(self):
        """None should raise ValidationError."""
        with pytest.raises(ValidationError):
            parse_visibility(None)

    def test_parse_rejects_non_string_types(self):
        """Non-string types should raise ValidationError."""
        with pytest.raises(ValidationError, match="visibility must be a string"):
            parse_visibility(123)
        with pytest.raises(ValidationError, match="visibility must be a string"):
            parse_visibility(["private"])
        with pytest.raises(ValidationError, match="visibility must be a string"):
            parse_visibility({"visibility": "private"})

    @pytest.mark.parametrize(
        "input_with_spaces,expected",
        [
            (" private", Visibility.PRIVATE),
            ("private ", Visibility.PRIVATE),
            (" private ", Visibility.PRIVATE),
            ("  shared  ", Visibility.SHARED),
            (" public ", Visibility.PUBLIC),
            ("\tprivate\t", Visibility.PRIVATE),
            ("\n shared \n", Visibility.SHARED),
        ],
    )
    def test_parse_strips_whitespace(self, input_with_spaces: str, expected: Visibility):
        """Leading/trailing whitespace should be stripped before parsing."""
        result = parse_visibility(input_with_spaces)
        assert result == expected


# =============================================================================
# B) CAN_READ - Access Matrix
# =============================================================================
class TestCanReadPublic:
    """can_read tests for PUBLIC visibility - anyone can read."""

    def test_owner_can_read_own_public_resource(self, owner: str):
        """Owner can always read their own public resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PUBLIC,
            current_user_id=owner,
            shared_with=None,
        )
        assert result is True

    def test_other_user_can_read_public_resource(self, owner: str, other: str):
        """Any user can read a public resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PUBLIC,
            current_user_id=other,
            shared_with=None,
        )
        assert result is True

    def test_public_resource_readable_by_anyone(self, owner: str):
        """Multiple different users can read public resources."""
        for user in ["user_x", "user_y", "user_z", "anonymous_123"]:
            result = can_read(
                owner_id=owner,
                visibility=Visibility.PUBLIC,
                current_user_id=user,
                shared_with=None,
            )
            assert result is True


class TestCanReadPrivate:
    """can_read tests for PRIVATE visibility - only owner can read."""

    def test_owner_can_read_own_private_resource(self, owner: str):
        """Owner can read their own private resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            current_user_id=owner,
            shared_with=None,
        )
        assert result is True

    def test_other_user_cannot_read_private_resource(self, owner: str, other: str):
        """Non-owner cannot read a private resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            current_user_id=other,
            shared_with=None,
        )
        assert result is False

    def test_private_resource_not_readable_by_shared_with_users(self, owner: str, friend: str):
        """Even if user is in shared_with, they cannot read PRIVATE resources."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            current_user_id=friend,
            shared_with=[friend],  # friend is in list but visibility is private
        )
        assert result is False


class TestCanReadShared:
    """can_read tests for SHARED visibility - owner + allowlist can read."""

    def test_owner_can_read_own_shared_resource(self, owner: str):
        """Owner can always read their own shared resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=owner,
            shared_with=[],
        )
        assert result is True

    def test_owner_can_read_shared_even_with_empty_shared_with(self, owner: str):
        """Owner can read shared resource even if shared_with is empty."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=owner,
            shared_with=None,
        )
        assert result is True

    def test_user_in_shared_with_can_read(self, owner: str, friend: str):
        """User in shared_with list can read the resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with=[friend],
        )
        assert result is True

    def test_user_in_shared_with_set_can_read(self, owner: str, friend: str):
        """User in shared_with set can read the resource."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with={friend, "other_friend"},
        )
        assert result is True

    def test_user_not_in_shared_with_cannot_read(self, owner: str, other: str, friend: str):
        """User not in shared_with list cannot read."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=other,
            shared_with=[friend],  # other is not in list
        )
        assert result is False

    def test_shared_with_empty_list_only_owner_can_read(self, owner: str, other: str):
        """With empty shared_with, only owner can read."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=other,
            shared_with=[],
        )
        assert result is False

    def test_shared_with_none_only_owner_can_read(self, owner: str, other: str):
        """With None shared_with (treated as empty), only owner can read."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=other,
            shared_with=None,
        )
        assert result is False

    def test_shared_with_multiple_users(self, owner: str, friend: str):
        """Multiple users in shared_with can all read."""
        shared_list = [friend, "user_d", "user_e"]
        for user in shared_list:
            result = can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=user,
                shared_with=shared_list,
            )
            assert result is True

    def test_shared_with_handles_duplicates(self, owner: str, friend: str):
        """shared_with with duplicates should still work correctly."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with=[friend, friend, friend],  # duplicates
        )
        assert result is True


# =============================================================================
# B.1) CAN_READ - Parametrized Matrix
# =============================================================================
class TestCanReadParametrized:
    """Parametrized can_read tests for comprehensive coverage."""

    @pytest.mark.parametrize(
        "visibility,is_owner,expected",
        [
            # PUBLIC: everyone can read (shared_with always [] for PUBLIC)
            (Visibility.PUBLIC, True, True),
            (Visibility.PUBLIC, False, True),
            # PRIVATE: only owner (shared_with always [] for PRIVATE)
            (Visibility.PRIVATE, True, True),
            (Visibility.PRIVATE, False, False),
        ],
    )
    def test_can_read_matrix_public_private(
        self,
        visibility: Visibility,
        is_owner: bool,
        expected: bool,
        owner: str,
        other: str,
    ):
        """Test PUBLIC and PRIVATE visibility (shared_with is always empty)."""
        current_user = owner if is_owner else other

        result = can_read(
            owner_id=owner,
            visibility=visibility,
            current_user_id=current_user,
            shared_with=[],  # Always empty for PUBLIC/PRIVATE
        )
        assert result is expected

    @pytest.mark.parametrize(
        "is_owner,in_shared_with,expected",
        [
            # SHARED: owner OR in shared_with
            (True, False, True),  # owner, not in list
            (True, True, True),  # owner, also in list
            (False, True, True),  # not owner, but in list
            (False, False, False),  # not owner, not in list
        ],
    )
    def test_can_read_matrix_shared(
        self,
        is_owner: bool,
        in_shared_with: bool,
        expected: bool,
        owner: str,
        other: str,
    ):
        """Test SHARED visibility with shared_with variations."""
        current_user = owner if is_owner else other
        shared_with = [other] if in_shared_with else []

        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=current_user,
            shared_with=shared_with,
        )
        assert result is expected


# =============================================================================
# B.2) CAN_READ - shared_with IGNORED for PUBLIC/PRIVATE
# =============================================================================
class TestCanReadSharedWithIgnored:
    """Explicit tests: shared_with is IGNORED for PUBLIC and PRIVATE visibility."""

    def test_private_ignores_shared_with_even_if_user_in_list(self, owner: str, other: str):
        """PRIVATE ignores shared_with: user in list still cannot read."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            current_user_id=other,
            shared_with=[other, "user_x", "user_y"],  # other IS in list
        )
        assert result is False

    def test_private_ignores_shared_with_owner_always_can_read(self, owner: str, other: str):
        """PRIVATE: owner can read regardless of shared_with content."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PRIVATE,
            current_user_id=owner,
            shared_with=[other],  # irrelevant for owner
        )
        assert result is True

    def test_public_ignores_shared_with_anyone_can_read(self, owner: str, other: str):
        """PUBLIC: anyone can read, shared_with is irrelevant."""
        # Non-owner can read even if NOT in shared_with
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PUBLIC,
            current_user_id=other,
            shared_with=[],  # empty list, but PUBLIC so doesn't matter
        )
        assert result is True

    def test_public_ignores_shared_with_even_with_populated_list(
        self, owner: str, other: str, friend: str
    ):
        """PUBLIC: shared_with list is completely ignored."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.PUBLIC,
            current_user_id=friend,
            shared_with=[other],  # friend NOT in list, but doesn't matter
        )
        assert result is True


# =============================================================================
# C) CAN_WRITE - Only Owner
# =============================================================================
class TestCanWrite:
    """can_write tests - only owner can write, regardless of visibility."""

    def test_owner_can_write_own_resource(self, owner: str):
        """Owner can write to their own resource."""
        result = can_write(owner_id=owner, current_user_id=owner)
        assert result is True

    def test_other_user_cannot_write(self, owner: str, other: str):
        """Non-owner cannot write to resource."""
        result = can_write(owner_id=owner, current_user_id=other)
        assert result is False

    def test_friend_cannot_write_even_if_shared(self, owner: str, friend: str):
        """User in shared_with still cannot write (write is owner-only)."""
        # Note: can_write doesn't take visibility/shared_with params
        # because write is ALWAYS owner-only
        result = can_write(owner_id=owner, current_user_id=friend)
        assert result is False

    @pytest.mark.parametrize(
        "current_user,expected",
        [
            ("user_a", True),  # owner
            ("user_b", False),
            ("user_c", False),
            ("admin", False),  # even "admin" string has no special privileges
            ("root", False),
        ],
    )
    def test_can_write_only_exact_owner_match(self, current_user: str, expected: bool):
        """Only exact owner_id match allows write."""
        result = can_write(owner_id="user_a", current_user_id=current_user)
        assert result is expected


# =============================================================================
# D) HARDENING INPUTS - Deny by Default
# =============================================================================
class TestHardeningOwnerIdCanRead:
    """Hardening tests for owner_id parameter in can_read."""

    def test_rejects_none_owner_id(self, owner: str):
        """None owner_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=None,
                visibility=Visibility.PUBLIC,
                current_user_id=owner,
                shared_with=None,
            )

    def test_rejects_empty_owner_id(self, owner: str):
        """Empty string owner_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id="",
                visibility=Visibility.PUBLIC,
                current_user_id=owner,
                shared_with=None,
            )

    def test_rejects_whitespace_only_owner_id(self, owner: str, blank: str):
        """Whitespace-only owner_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=blank,
                visibility=Visibility.PUBLIC,
                current_user_id=owner,
                shared_with=None,
            )


class TestHardeningCurrentUserIdCanRead:
    """Hardening tests for current_user_id parameter in can_read."""

    def test_rejects_none_current_user_id(self, owner: str):
        """None current_user_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.PUBLIC,
                current_user_id=None,
                shared_with=None,
            )

    def test_rejects_empty_current_user_id(self, owner: str):
        """Empty string current_user_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.PUBLIC,
                current_user_id="",
                shared_with=None,
            )

    def test_rejects_whitespace_only_current_user_id(self, owner: str, blank: str):
        """Whitespace-only current_user_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.PUBLIC,
                current_user_id=blank,
                shared_with=None,
            )


class TestHardeningSharedWith:
    """Hardening tests for shared_with parameter."""

    def test_rejects_shared_with_containing_empty_string(self, owner: str, other: str):
        """shared_with containing empty string should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=["valid_user", ""],
            )

    def test_rejects_shared_with_containing_whitespace_only(
        self, owner: str, other: str, blank: str
    ):
        """shared_with containing whitespace-only string should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=["valid_user", blank],
            )

    def test_rejects_shared_with_containing_none(self, owner: str, other: str):
        """shared_with containing None should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=["valid_user", None],
            )

    def test_shared_with_none_treated_as_empty_not_error(self, owner: str, other: str):
        """shared_with=None should be treated as empty list, not raise error."""
        # This should NOT raise, but should deny access to non-owner
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=other,
            shared_with=None,
        )
        assert result is False

    def test_shared_with_empty_list_valid(self, owner: str, other: str):
        """shared_with=[] is valid and denies access to non-owner."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=other,
            shared_with=[],
        )
        assert result is False


class TestHardeningSharedWithTypeValidation:
    """Hardening: shared_with must be a proper collection, not a string or int.

    SECURITY: Passing a string like "user_c" would iterate over characters
    ['u', 's', 'e', 'r', '_', 'c'] which is a dangerous bug.
    """

    def test_rejects_shared_with_as_string(self, owner: str, other: str, friend: str):
        """shared_with as string should raise ValidationError (dangerous iterable bug)."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=friend,  # "user_c" string, NOT a list!
            )

    def test_rejects_shared_with_as_string_even_if_would_match(self, owner: str, friend: str):
        """Even if string contains user chars, must reject (security hardening)."""
        # If we accidentally iterated "user_c", we'd check for 'u', 's', 'e', etc.
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id="u",  # 'u' is a char in "user_c"
                shared_with="user_c",  # WRONG: string instead of list
            )

    def test_rejects_shared_with_as_integer(self, owner: str, other: str):
        """shared_with as integer should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=123,  # int is not a valid collection
            )

    def test_rejects_shared_with_as_dict(self, owner: str, other: str):
        """shared_with as dict should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with={"user": "value"},  # dict is not a valid collection
            )

    def test_accepts_shared_with_as_list(self, owner: str, friend: str):
        """shared_with as list is valid."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with=[friend],
        )
        assert result is True

    def test_accepts_shared_with_as_set(self, owner: str, friend: str):
        """shared_with as set is valid."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with={friend},
        )
        assert result is True

    def test_accepts_shared_with_as_tuple(self, owner: str, friend: str):
        """shared_with as tuple is valid."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with=(friend,),
        )
        assert result is True

    def test_accepts_shared_with_as_frozenset(self, owner: str, friend: str):
        """shared_with as frozenset is valid."""
        result = can_read(
            owner_id=owner,
            visibility=Visibility.SHARED,
            current_user_id=friend,
            shared_with=frozenset([friend]),
        )
        assert result is True


class TestHardeningOwnerIdCanWrite:
    """Hardening tests for owner_id parameter in can_write."""

    def test_rejects_none_owner_id(self, owner: str):
        """None owner_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_write(owner_id=None, current_user_id=owner)

    def test_rejects_empty_owner_id(self, owner: str):
        """Empty string owner_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_write(owner_id="", current_user_id=owner)

    def test_rejects_whitespace_only_owner_id(self, owner: str, blank: str):
        """Whitespace-only owner_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_write(owner_id=blank, current_user_id=owner)


class TestHardeningCurrentUserIdCanWrite:
    """Hardening tests for current_user_id parameter in can_write."""

    def test_rejects_none_current_user_id(self, owner: str):
        """None current_user_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_write(owner_id=owner, current_user_id=None)

    def test_rejects_empty_current_user_id(self, owner: str):
        """Empty string current_user_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_write(owner_id=owner, current_user_id="")

    def test_rejects_whitespace_only_current_user_id(self, owner: str, blank: str):
        """Whitespace-only current_user_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            can_write(owner_id=owner, current_user_id=blank)


# =============================================================================
# E) PARAMETRIZED INVALID INPUTS
# =============================================================================
class TestInvalidInputsParametrized:
    """Parametrized tests for invalid inputs across functions."""

    @pytest.mark.parametrize(
        "invalid_owner_id",
        [
            None,
            "",
            "   ",
            "\t",
            "\n",
        ],
    )
    def test_can_read_rejects_invalid_owner_id(self, invalid_owner_id: str, owner: str):
        """can_read should reject various invalid owner_id values."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=invalid_owner_id,
                visibility=Visibility.PUBLIC,
                current_user_id=owner,
                shared_with=None,
            )

    @pytest.mark.parametrize(
        "invalid_current_user_id",
        [
            None,
            "",
            "   ",
            "\t",
            "\n",
        ],
    )
    def test_can_read_rejects_invalid_current_user_id(
        self, invalid_current_user_id: str, owner: str
    ):
        """can_read should reject various invalid current_user_id values."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.PUBLIC,
                current_user_id=invalid_current_user_id,
                shared_with=None,
            )

    @pytest.mark.parametrize(
        "invalid_owner_id",
        [
            None,
            "",
            "   ",
            "\t",
            "\n",
        ],
    )
    def test_can_write_rejects_invalid_owner_id(self, invalid_owner_id: str, owner: str):
        """can_write should reject various invalid owner_id values."""
        with pytest.raises(ValidationError):
            can_write(owner_id=invalid_owner_id, current_user_id=owner)

    @pytest.mark.parametrize(
        "invalid_current_user_id",
        [
            None,
            "",
            "   ",
            "\t",
            "\n",
        ],
    )
    def test_can_write_rejects_invalid_current_user_id(
        self, invalid_current_user_id: str, owner: str
    ):
        """can_write should reject various invalid current_user_id values."""
        with pytest.raises(ValidationError):
            can_write(owner_id=owner, current_user_id=invalid_current_user_id)

    @pytest.mark.parametrize(
        "invalid_visibility_value",
        [
            "friends",
            "unlisted",
            "",
            "   ",
            None,
            "INVALID",
        ],
    )
    def test_parse_visibility_rejects_invalid(self, invalid_visibility_value):
        """parse_visibility should reject various invalid values."""
        with pytest.raises(ValidationError):
            parse_visibility(invalid_visibility_value)

    def test_can_read_rejects_non_visibility_type(self):
        """can_read should reject non-Visibility values for visibility."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id="user_a",
                visibility="public",
                current_user_id="user_b",
                shared_with=None,
            )


# =============================================================================
# VISIBILITY ENUM TESTS
# =============================================================================
class TestVisibilityEnum:
    """Tests for Visibility enum behavior."""

    def test_visibility_has_private(self):
        """Visibility should have PRIVATE member."""
        assert hasattr(Visibility, "PRIVATE")

    def test_visibility_has_shared(self):
        """Visibility should have SHARED member."""
        assert hasattr(Visibility, "SHARED")

    def test_visibility_has_public(self):
        """Visibility should have PUBLIC member."""
        assert hasattr(Visibility, "PUBLIC")

    def test_visibility_members_are_distinct(self):
        """All visibility members should be distinct."""
        assert Visibility.PRIVATE != Visibility.SHARED
        assert Visibility.SHARED != Visibility.PUBLIC
        assert Visibility.PRIVATE != Visibility.PUBLIC

    def test_visibility_count(self):
        """Visibility should have exactly 3 members."""
        # This ensures we don't accidentally add/remove visibility levels
        members = list(Visibility)
        assert len(members) == 3


class TestHardeningTypeValidation:
    """Additional type validation tests for complete coverage."""

    def test_validate_user_id_rejects_non_string_types(self, owner: str):
        """_validate_user_id should reject non-string types."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=123,
                visibility=Visibility.PRIVATE,
                current_user_id=owner,
                shared_with=None,
            )

    def test_shared_with_rejects_non_iterable(self, owner: str, other: str):
        """shared_with must be iterable."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=12345,
            )

    def test_shared_with_rejects_non_string_items(self, owner: str, other: str):
        """shared_with items must be strings."""
        with pytest.raises(ValidationError):
            can_read(
                owner_id=owner,
                visibility=Visibility.SHARED,
                current_user_id=other,
                shared_with=[123, 456],
            )


class TestDenyByDefaultDefensiveCode:
    """Test that unknown visibility values are denied by default (defensive code).

    This tests the 'return False' safety net at the end of can_read(),
    which should be unreachable with a proper Visibility enum but exists
    as defense-in-depth.
    """

    def test_unknown_visibility_denies_access(self):
        """Test that an unknown visibility value triggers deny-by-default.

        This test temporarily adds a new member to the Visibility enum,
        verifying that the defensive 'return False' at the end of can_read()
        works correctly.
        """
        # Dynamically add a new enum member to Visibility
        # This simulates a future scenario where a new visibility level is
        # added but not yet handled in can_read()
        unknown_visibility = object.__new__(Visibility)
        unknown_visibility._name_ = "UNKNOWN"
        unknown_visibility._value_ = "unknown"

        # Non-owner with unknown visibility should be denied by default
        result = can_read(
            owner_id="owner_a",
            visibility=unknown_visibility,
            current_user_id="user_b",
        )

        # Deny by default should return False
        assert result is False

    def test_unknown_visibility_owner_bypasses_but_others_denied(self):
        """Test that owner can read but non-owners are denied by default.

        This verifies the defensive code triggers after the owner check.
        """
        restricted_visibility = object.__new__(Visibility)
        restricted_visibility._name_ = "RESTRICTED"
        restricted_visibility._value_ = "restricted"

        # Owner can still read (owner check comes first)
        result_owner = can_read(
            owner_id="owner_a",
            visibility=restricted_visibility,
            current_user_id="owner_a",
        )
        assert result_owner is True  # Owner bypass works

        # Non-owner gets denied by default
        result_other = can_read(
            owner_id="owner_a",
            visibility=restricted_visibility,
            current_user_id="user_b",
        )
        assert result_other is False  # Deny by default for unknown visibility
