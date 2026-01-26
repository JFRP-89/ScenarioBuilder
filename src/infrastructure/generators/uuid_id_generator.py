"""UuidIdGenerator - UUID-based ID generation.

A simple implementation of IdGenerator using UUID4.
"""

from __future__ import annotations

import uuid


class UuidIdGenerator:
    """UUID-based ID generator.

    Generates unique card_ids using UUID4 in hex format (32 characters).
    """

    def generate_card_id(self) -> str:
        """Generate a unique card ID.

        Returns:
            A 32-character hex string from UUID4.
        """
        return uuid.uuid4().hex
