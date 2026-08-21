"""Add shared organization monitoring workspace.

Revision ID: 20260820_0019
Revises: 20260820_0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0019"
down_revision: str | None = "20260820_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_watchlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "state_id",
            sa.Uuid(),
            sa.ForeignKey("states.state_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "state_id",
            name="uq_organization_watchlist_org_state",
        ),
    )
    op.create_index(
        "ix_organization_watchlists_organization_id",
        "organization_watchlists",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_watchlists_state_id",
        "organization_watchlists",
        ["state_id"],
    )
    op.create_index(
        "ix_organization_watchlists_created_by_user_id",
        "organization_watchlists",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_organization_watchlists_org_created",
        "organization_watchlists",
        ["organization_id", "created_at"],
    )

    op.create_table(
        "organization_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
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
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "event_key",
            name="uq_organization_alert_org_event",
        ),
        sa.CheckConstraint(
            "source_kind IN ('fiscal_watch', 'fiscal_event', 'publication')",
            name="ck_organization_alert_source_kind",
        ),
    )
    op.create_index(
        "ix_organization_alerts_organization_id",
        "organization_alerts",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_alerts_state_id",
        "organization_alerts",
        ["state_id"],
    )
    op.create_index(
        "ix_organization_alerts_org_occurred",
        "organization_alerts",
        ["organization_id", "occurred_at"],
    )
    op.create_index(
        "ix_organization_alerts_state_occurred",
        "organization_alerts",
        ["state_id", "occurred_at"],
    )

    op.create_table(
        "organization_alert_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "alert_id",
            sa.Uuid(),
            sa.ForeignKey("organization_alerts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "alert_id",
            "user_id",
            name="uq_organization_alert_receipt_alert_user",
        ),
    )
    op.create_index(
        "ix_organization_alert_receipts_alert_id",
        "organization_alert_receipts",
        ["alert_id"],
    )
    op.create_index(
        "ix_organization_alert_receipts_user_id",
        "organization_alert_receipts",
        ["user_id"],
    )
    op.create_index(
        "ix_organization_alert_receipts_user_read",
        "organization_alert_receipts",
        ["user_id", "read_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_organization_alert_receipts_user_read",
        table_name="organization_alert_receipts",
    )
    op.drop_index(
        "ix_organization_alert_receipts_user_id",
        table_name="organization_alert_receipts",
    )
    op.drop_index(
        "ix_organization_alert_receipts_alert_id",
        table_name="organization_alert_receipts",
    )
    op.drop_table("organization_alert_receipts")

    op.drop_index(
        "ix_organization_alerts_state_occurred", table_name="organization_alerts"
    )
    op.drop_index(
        "ix_organization_alerts_org_occurred", table_name="organization_alerts"
    )
    op.drop_index("ix_organization_alerts_state_id", table_name="organization_alerts")
    op.drop_index(
        "ix_organization_alerts_organization_id", table_name="organization_alerts"
    )
    op.drop_table("organization_alerts")

    op.drop_index(
        "ix_organization_watchlists_org_created", table_name="organization_watchlists"
    )
    op.drop_index(
        "ix_organization_watchlists_created_by_user_id",
        table_name="organization_watchlists",
    )
    op.drop_index(
        "ix_organization_watchlists_state_id", table_name="organization_watchlists"
    )
    op.drop_index(
        "ix_organization_watchlists_organization_id",
        table_name="organization_watchlists",
    )
    op.drop_table("organization_watchlists")
