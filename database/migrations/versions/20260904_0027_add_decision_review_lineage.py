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
    with op.batch_alter_table("evidence_rooms") as batch_op:
        batch_op.add_column(
            sa.Column(
                "review_required",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column("review_trigger_match_id", sa.Uuid(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("review_required_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_evidence_rooms_review_trigger_match",
            "fiscal_watch_contract_matches",
            ["review_trigger_match_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_evidence_rooms_reviewed_by_user",
            "users",
            ["reviewed_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_evidence_rooms_review_trigger_match_id",
            ["review_trigger_match_id"],
        )
        batch_op.create_index(
            "ix_evidence_rooms_reviewed_by_user_id",
            ["reviewed_by_user_id"],
        )
        batch_op.create_index(
            "ix_evidence_rooms_review_required",
            ["organization_id", "review_required"],
        )

    with op.batch_alter_table("fiscal_receipts") as batch_op:
        batch_op.add_column(
            sa.Column("predecessor_receipt_id", sa.Uuid(), nullable=True)
        )
        batch_op.add_column(sa.Column("triggering_match_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_fiscal_receipts_predecessor",
            "fiscal_receipts",
            ["predecessor_receipt_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_fiscal_receipts_trigger_match",
            "fiscal_watch_contract_matches",
            ["triggering_match_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_fiscal_receipts_predecessor",
            ["predecessor_receipt_id"],
        )
        batch_op.create_index(
            "ix_fiscal_receipts_trigger_match",
            ["triggering_match_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("fiscal_receipts") as batch_op:
        batch_op.drop_index("ix_fiscal_receipts_trigger_match")
        batch_op.drop_index("ix_fiscal_receipts_predecessor")
        batch_op.drop_constraint(
            "fk_fiscal_receipts_trigger_match",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_fiscal_receipts_predecessor",
            type_="foreignkey",
        )
        batch_op.drop_column("triggering_match_id")
        batch_op.drop_column("predecessor_receipt_id")

    with op.batch_alter_table("evidence_rooms") as batch_op:
        batch_op.drop_index("ix_evidence_rooms_review_required")
        batch_op.drop_index("ix_evidence_rooms_reviewed_by_user_id")
        batch_op.drop_index("ix_evidence_rooms_review_trigger_match_id")
        batch_op.drop_constraint(
            "fk_evidence_rooms_reviewed_by_user",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_evidence_rooms_review_trigger_match",
            type_="foreignkey",
        )
        batch_op.drop_column("reviewed_by_user_id")
        batch_op.drop_column("last_reviewed_at")
        batch_op.drop_column("review_required_at")
        batch_op.drop_column("review_trigger_match_id")
        batch_op.drop_column("review_required")
