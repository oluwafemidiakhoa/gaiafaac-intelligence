"""Add append-only institutional webhook attempt history.

Revision ID: 20260820_0018
Revises: 20260820_0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0018"
down_revision: str | None = "20260820_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_webhook_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "delivery_id",
            sa.Uuid(),
            sa.ForeignKey("organization_webhook_deliveries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body_excerpt", sa.String(length=1000), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "delivery_id", "attempt_number", name="uq_org_webhook_attempt_number"
        ),
    )
    op.create_index(
        "ix_org_webhook_attempts_delivery",
        "organization_webhook_attempts",
        ["delivery_id", "attempt_number"],
    )


def downgrade() -> None:
    op.drop_index("ix_org_webhook_attempts_delivery", table_name="organization_webhook_attempts")
    op.drop_table("organization_webhook_attempts")
