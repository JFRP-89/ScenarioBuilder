"""create favorites table

Revision ID: 20260215_000002
Revises: 20260215_000001
Create Date: 2026-02-15 00:00:02
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260215_000002"
down_revision = "20260215_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("card_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("actor_id", "card_id"),
    )
    op.create_index("ix_favorites_actor_id", "favorites", ["actor_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_favorites_actor_id", table_name="favorites")
    op.drop_table("favorites")
