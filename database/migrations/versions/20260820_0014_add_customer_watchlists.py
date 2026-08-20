"""Add customer fiscal watchlists.

Revision ID: 20260820_0014
Revises: 20260819_0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0014"
down_revision: str | None = "20260819_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_watchlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "state_id",
            sa.Uuid(),
            sa.ForeignKey("states.state_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "state_id", name="uq_customer_watchlist_user_state"
        ),
    )
    op.create_index(
        "ix_customer_watchlists_user_id", "customer_watchlists", ["user_id"]
    )
    op.create_index(
        "ix_customer_watchlists_state_id", "customer_watchlists", ["state_id"]
    )
    op.create_index(
        "ix_customer_watchlists_user_created",
        "customer_watchlists",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_watchlists_user_created", table_name="customer_watchlists"
    )
    op.drop_index("ix_customer_watchlists_state_id", table_name="customer_watchlists")
    op.drop_index("ix_customer_watchlists_user_id", table_name="customer_watchlists")
    op.drop_table("customer_watchlists")
