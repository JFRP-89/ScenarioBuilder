"""create cards table

Revision ID: 20260215_000001
Revises:
Create Date: 2026-02-15 00:00:01
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260215_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("card_id", sa.String(length=255), nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("shared_with", sa.JSON(), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("table_width", sa.Integer(), nullable=False),
        sa.Column("table_height", sa.Integer(), nullable=False),
        sa.Column("table_unit", sa.String(length=10), nullable=False),
        sa.Column("map_spec", sa.JSON(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column("armies", sa.Text(), nullable=True),
        sa.Column("deployment", sa.Text(), nullable=True),
        sa.Column("layout", sa.Text(), nullable=True),
        sa.Column("objectives", sa.JSON(), nullable=True),
        sa.Column("initial_priority", sa.String(length=255), nullable=True),
        sa.Column("special_rules", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("card_id"),
    )
    op.create_index("ix_cards_owner_id", "cards", ["owner_id"], unique=False)
    op.create_index("ix_cards_visibility", "cards", ["visibility"], unique=False)
    op.create_index("ix_cards_mode", "cards", ["mode"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cards_mode", table_name="cards")
    op.drop_index("ix_cards_visibility", table_name="cards")
    op.drop_index("ix_cards_owner_id", table_name="cards")
    op.drop_table("cards")
