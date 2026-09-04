"""Add Fiscal Watch Contracts and immutable matches.

Revision ID: 20260904_0026
Revises: 20260904_0025
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260904_0026"
down_revision: str | None = "20260904_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fiscal_watch_contracts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("evidence_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "baseline_receipt_id",
            sa.Uuid(),
            sa.ForeignKey("fiscal_receipts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("state_codes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("event_types", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("minimum_severity", sa.String(length=24), nullable=False, server_default="watch"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'archived')",
            name="ck_fiscal_watch_contract_status",
        ),
        sa.CheckConstraint(
            "minimum_severity IN ('informational', 'watch', 'elevated', 'notable', 'material', 'critical')",
            name="ck_fiscal_watch_contract_minimum_severity",
        ),
    )
    op.create_index(
        "ix_fiscal_watch_contracts_organization_id",
        "fiscal_watch_contracts",
        ["organization_id"],
    )
    op.create_index("ix_fiscal_watch_contracts_room_id", "fiscal_watch_contracts", ["room_id"])
    op.create_index(
        "ix_fiscal_watch_contracts_baseline_receipt_id",
        "fiscal_watch_contracts",
        ["baseline_receipt_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contracts_created_by_user_id",
        "fiscal_watch_contracts",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contracts_org_status",
        "fiscal_watch_contracts",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_fiscal_watch_contracts_room_created",
        "fiscal_watch_contracts",
        ["room_id", "created_at"],
    )

    op.create_table(
        "fiscal_watch_contract_matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "contract_id",
            sa.Uuid(),
            sa.ForeignKey("fiscal_watch_contracts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("evidence_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_alert_id",
            sa.Uuid(),
            sa.ForeignKey("organization_alerts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "contract_id",
            "organization_alert_id",
            name="uq_watch_contract_match",
        ),
    )
    op.create_index(
        "ix_fiscal_watch_contract_matches_contract_id",
        "fiscal_watch_contract_matches",
        ["contract_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_matches_organization_id",
        "fiscal_watch_contract_matches",
        ["organization_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_matches_room_id",
        "fiscal_watch_contract_matches",
        ["room_id"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_matches_organization_alert_id",
        "fiscal_watch_contract_matches",
        ["organization_alert_id"],
    )
    op.create_index(
        "ix_watch_contract_matches_contract_matched",
        "fiscal_watch_contract_matches",
        ["contract_id", "matched_at"],
    )
    op.create_index(
        "ix_watch_contract_matches_room_matched",
        "fiscal_watch_contract_matches",
        ["room_id", "matched_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_watch_contract_matches_room_matched", table_name="fiscal_watch_contract_matches")
    op.drop_index("ix_watch_contract_matches_contract_matched", table_name="fiscal_watch_contract_matches")
    op.drop_index(
        "ix_fiscal_watch_contract_matches_organization_alert_id",
        table_name="fiscal_watch_contract_matches",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_matches_room_id",
        table_name="fiscal_watch_contract_matches",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_matches_organization_id",
        table_name="fiscal_watch_contract_matches",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_matches_contract_id",
        table_name="fiscal_watch_contract_matches",
    )
    op.drop_table("fiscal_watch_contract_matches")

    op.drop_index("ix_fiscal_watch_contracts_room_created", table_name="fiscal_watch_contracts")
    op.drop_index("ix_fiscal_watch_contracts_org_status", table_name="fiscal_watch_contracts")
    op.drop_index("ix_fiscal_watch_contracts_created_by_user_id", table_name="fiscal_watch_contracts")
    op.drop_index("ix_fiscal_watch_contracts_baseline_receipt_id", table_name="fiscal_watch_contracts")
    op.drop_index("ix_fiscal_watch_contracts_room_id", table_name="fiscal_watch_contracts")
    op.drop_index("ix_fiscal_watch_contracts_organization_id", table_name="fiscal_watch_contracts")
    op.drop_table("fiscal_watch_contracts")
