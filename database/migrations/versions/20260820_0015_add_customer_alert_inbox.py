"""Add persistent customer alert inbox.

Revision ID: 20260820_0015
Revises: 20260820_0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0015"
down_revision: str | None = "20260820_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_alerts",
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
        sa.Column("event_key", sa.String(length=240), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column(
            "source_event_id",
            sa.String(length=120),
            sa.ForeignKey("fiscal_events.event_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=24), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "event_key", name="uq_customer_alert_user_event"),
        sa.CheckConstraint(
            "source_kind IN ('fiscal_watch', 'fiscal_event', 'publication')",
            name="ck_customer_alert_source_kind",
        ),
    )
    op.create_index("ix_customer_alerts_user_id", "customer_alerts", ["user_id"])
    op.create_index("ix_customer_alerts_state_id", "customer_alerts", ["state_id"])
    op.create_index(
        "ix_customer_alerts_user_occurred", "customer_alerts", ["user_id", "occurred_at"]
    )
    op.create_index(
        "ix_customer_alerts_user_read", "customer_alerts", ["user_id", "read_at"]
    )
    op.create_index(
        "ix_customer_alerts_state_occurred", "customer_alerts", ["state_id", "occurred_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_customer_alerts_state_occurred", table_name="customer_alerts")
    op.drop_index("ix_customer_alerts_user_read", table_name="customer_alerts")
    op.drop_index("ix_customer_alerts_user_occurred", table_name="customer_alerts")
    op.drop_index("ix_customer_alerts_state_id", table_name="customer_alerts")
    op.drop_index("ix_customer_alerts_user_id", table_name="customer_alerts")
    op.drop_table("customer_alerts")
