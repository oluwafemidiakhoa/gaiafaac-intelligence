"""add pilot leads for commercial enquiries

Revision ID: 20260801_0004
Revises: 20260801_0003
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0004"
down_revision: str | None = "20260801_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pilot_leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=160), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("plan_interest", sa.String(length=40), nullable=False),
        sa.Column("use_case", sa.Text(), nullable=False),
        sa.Column("states_or_periods", sa.Text(), nullable=True),
        sa.Column("preferred_format", sa.String(length=80), nullable=True),
        sa.Column("expected_users", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pilot_leads_email", "pilot_leads", ["email"], unique=False)
    op.create_index(
        "ix_pilot_leads_status_created",
        "pilot_leads",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pilot_leads_status_created", table_name="pilot_leads")
    op.drop_index("ix_pilot_leads_email", table_name="pilot_leads")
    op.drop_table("pilot_leads")
