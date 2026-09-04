"""Add Decision Room review state and Fiscal Receipt lineage.

Revision ID: 20260904_0027
Revises: 20260904_0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260904_0027"
down_revision: str | None = "20260904_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evidence_rooms",
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "evidence_rooms",
        sa.Column("review_trigger_match_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "evidence_rooms",
        sa.Column("review_required_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "evidence_rooms",
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "evidence_rooms",
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_evidence_rooms_review_trigger_match",
        "evidence_rooms",
        "fiscal_watch_contract_matches",
        ["review_trigger_match_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_evidence_rooms_reviewed_by_user",
        "evidence_rooms",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_evidence_rooms_review_trigger_match_id",
        "evidence_rooms",
        ["review_trigger_match_id"],
    )
    op.create_index(
        "ix_evidence_rooms_reviewed_by_user_id",
        "evidence_rooms",
        ["reviewed_by_user_id"],
    )
    op.create_index(
        "ix_evidence_rooms_review_required",
        "evidence_rooms",
        ["organization_id", "review_required"],
    )

    op.add_column(
        "fiscal_receipts",
        sa.Column("predecessor_receipt_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "fiscal_receipts",
        sa.Column("triggering_match_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_fiscal_receipts_predecessor",
        "fiscal_receipts",
        "fiscal_receipts",
        ["predecessor_receipt_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_fiscal_receipts_trigger_match",
        "fiscal_receipts",
        "fiscal_watch_contract_matches",
        ["triggering_match_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_fiscal_receipts_predecessor",
        "fiscal_receipts",
        ["predecessor_receipt_id"],
    )
    op.create_index(
        "ix_fiscal_receipts_trigger_match",
        "fiscal_receipts",
        ["triggering_match_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fiscal_receipts_trigger_match", table_name="fiscal_receipts")
    op.drop_index("ix_fiscal_receipts_predecessor", table_name="fiscal_receipts")
    op.drop_constraint(
        "fk_fiscal_receipts_trigger_match",
        "fiscal_receipts",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_fiscal_receipts_predecessor",
        "fiscal_receipts",
        type_="foreignkey",
    )
    op.drop_column("fiscal_receipts", "triggering_match_id")
    op.drop_column("fiscal_receipts", "predecessor_receipt_id")

    op.drop_index("ix_evidence_rooms_review_required", table_name="evidence_rooms")
    op.drop_index("ix_evidence_rooms_reviewed_by_user_id", table_name="evidence_rooms")
    op.drop_index("ix_evidence_rooms_review_trigger_match_id", table_name="evidence_rooms")
    op.drop_constraint(
        "fk_evidence_rooms_reviewed_by_user",
        "evidence_rooms",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_evidence_rooms_review_trigger_match",
        "evidence_rooms",
        type_="foreignkey",
    )
    op.drop_column("evidence_rooms", "reviewed_by_user_id")
    op.drop_column("evidence_rooms", "last_reviewed_at")
    op.drop_column("evidence_rooms", "review_required_at")
    op.drop_column("evidence_rooms", "review_trigger_match_id")
    op.drop_column("evidence_rooms", "review_required")
