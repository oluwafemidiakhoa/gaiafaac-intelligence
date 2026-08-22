"""Add staged DMO state/FCT debt evidence records.

Revision ID: 20260821_0021
Revises: 20260821_0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0021"
down_revision: str | None = "20260821_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "state_debt_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "state_id",
            sa.Uuid(),
            sa.ForeignKey("states.state_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("debt_kind", sa.String(length=8), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("debt_amount", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column("debt_amount_original", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_table", sa.String(length=160), nullable=True),
        sa.Column("verification_status", sa.String(length=23), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "debt_kind IN ('domestic', 'external')",
            name="ck_state_debt_kind",
        ),
        sa.CheckConstraint("debt_amount >= 0", name="ck_state_debt_amount_nonnegative"),
        sa.CheckConstraint("length(currency) = 3", name="ck_state_debt_currency_length"),
        sa.CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_debt_demo_not_published",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "state_id",
            name="uq_state_debt_source_state",
        ),
    )
    op.create_index("ix_state_debt_records_state_id", "state_debt_records", ["state_id"])
    op.create_index(
        "ix_state_debt_records_source_document_id",
        "state_debt_records",
        ["source_document_id"],
    )
    op.create_index(
        "ix_state_debt_period_kind",
        "state_debt_records",
        ["as_of_date", "debt_kind"],
    )
    op.create_index(
        "ix_state_debt_state_kind",
        "state_debt_records",
        ["state_id", "debt_kind", "as_of_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_state_debt_state_kind", table_name="state_debt_records")
    op.drop_index("ix_state_debt_period_kind", table_name="state_debt_records")
    op.drop_index("ix_state_debt_records_source_document_id", table_name="state_debt_records")
    op.drop_index("ix_state_debt_records_state_id", table_name="state_debt_records")
    op.drop_table("state_debt_records")
