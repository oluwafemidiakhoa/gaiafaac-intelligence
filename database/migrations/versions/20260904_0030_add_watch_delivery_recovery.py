"""Add append-only Watch delivery recovery audit records.

Revision ID: 20260904_0030
Revises: 20260904_0029
"""

from alembic import op
import sqlalchemy as sa

revision = "20260904_0030"
down_revision = "20260904_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fiscal_watch_contract_delivery_recoveries",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("previous_status", sa.String(length=24), nullable=False),
        sa.Column("previous_attempt_count", sa.Integer(), nullable=False),
        sa.Column("previous_error", sa.String(length=500), nullable=True),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "previous_status IN ('dead_letter', 'failed')",
            name="ck_fiscal_watch_contract_delivery_recovery_previous_status",
        ),
        sa.CheckConstraint(
            "previous_attempt_count >= 0",
            name="ck_fiscal_watch_contract_delivery_recovery_attempt_count",
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["fiscal_watch_contract_deliveries.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_fiscal_watch_contract_delivery_recoveries_delivery_id",
        "fiscal_watch_contract_delivery_recoveries",
        ["delivery_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_delivery_recoveries_organization_id",
        "fiscal_watch_contract_delivery_recoveries",
        ["organization_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_delivery_recoveries_requested_by_user_id",
        "fiscal_watch_contract_delivery_recoveries",
        ["requested_by_user_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_delivery_recoveries_delivery_requested",
        "fiscal_watch_contract_delivery_recoveries",
        ["delivery_id", "requested_at"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_delivery_recoveries_org_requested",
        "fiscal_watch_contract_delivery_recoveries",
        ["organization_id", "requested_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fiscal_watch_contract_delivery_recoveries_org_requested",
        table_name="fiscal_watch_contract_delivery_recoveries",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_delivery_recoveries_delivery_requested",
        table_name="fiscal_watch_contract_delivery_recoveries",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_delivery_recoveries_requested_by_user_id",
        table_name="fiscal_watch_contract_delivery_recoveries",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_delivery_recoveries_organization_id",
        table_name="fiscal_watch_contract_delivery_recoveries",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_delivery_recoveries_delivery_id",
        table_name="fiscal_watch_contract_delivery_recoveries",
    )
    op.drop_table("fiscal_watch_contract_delivery_recoveries")
