"""Add customer alert delivery preferences and delivery ledger.

Revision ID: 20260820_0016
Revises: 20260820_0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0016"
down_revision: str | None = "20260820_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_notification_preferences",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("include_fiscal_watch", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("include_fiscal_events", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "customer_alert_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "alert_id",
            sa.Uuid(),
            sa.ForeignKey("customer_alerts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="email"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("alert_id", "channel", name="uq_customer_alert_delivery_channel"),
        sa.CheckConstraint("channel IN ('email')", name="ck_customer_alert_delivery_channel"),
        sa.CheckConstraint(
            "status IN ('pending', 'deferred', 'failed', 'sent')",
            name="ck_customer_alert_delivery_status",
        ),
    )
    op.create_index(
        "ix_customer_alert_deliveries_user_id", "customer_alert_deliveries", ["user_id"]
    )
    op.create_index(
        "ix_customer_alert_deliveries_user_status",
        "customer_alert_deliveries",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_customer_alert_deliveries_alert",
        "customer_alert_deliveries",
        ["alert_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_alert_deliveries_alert", table_name="customer_alert_deliveries")
    op.drop_index(
        "ix_customer_alert_deliveries_user_status", table_name="customer_alert_deliveries"
    )
    op.drop_index("ix_customer_alert_deliveries_user_id", table_name="customer_alert_deliveries")
    op.drop_table("customer_alert_deliveries")
    op.drop_table("customer_notification_preferences")
