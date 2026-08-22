"""Add staged state liability evidence records.

Revision ID: 20260822_0024
Revises: 20260822_0023
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0024"
down_revision: str | None = "20260822_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LIABILITY_METRICS = (
    "contractor_arrears",
    "pensions_and_gratuity_arrears",
    "salary_arrears",
    "other_judgment_arrears",
    "total_domestic_arrears",
)


def upgrade() -> None:
    op.create_table(
        "state_liability_records",
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
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("metric", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(precision=24, scale=2), nullable=True),
        sa.Column("amount_text", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=False),
        sa.Column("source_table", sa.String(length=200), nullable=False),
        sa.Column("extraction_method", sa.String(length=120), nullable=False),
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
        sa.CheckConstraint("fiscal_year >= 2000", name="ck_state_liability_fiscal_year"),
        sa.CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="ck_state_liability_amount_nonnegative",
        ),
        sa.CheckConstraint("length(currency) = 3", name="ck_state_liability_currency_length"),
        sa.CheckConstraint(
            "metric IN (" + ", ".join(repr(metric) for metric in _LIABILITY_METRICS) + ")",
            name="ck_state_liability_metric",
        ),
        sa.CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_liability_demo_not_published",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "state_id",
            "metric",
            name="uq_state_liability_source_state_metric",
        ),
    )
    op.create_index(
        "ix_state_liability_records_state_id",
        "state_liability_records",
        ["state_id"],
    )
    op.create_index(
        "ix_state_liability_records_source_document_id",
        "state_liability_records",
        ["source_document_id"],
    )
    op.create_index(
        "ix_state_liability_state_year",
        "state_liability_records",
        ["state_id", "fiscal_year"],
    )
    op.create_index(
        "ix_state_liability_period_metric",
        "state_liability_records",
        ["fiscal_year", "metric"],
    )


def downgrade() -> None:
    op.drop_index("ix_state_liability_period_metric", table_name="state_liability_records")
    op.drop_index("ix_state_liability_state_year", table_name="state_liability_records")
    op.drop_index(
        "ix_state_liability_records_source_document_id",
        table_name="state_liability_records",
    )
    op.drop_index("ix_state_liability_records_state_id", table_name="state_liability_records")
    op.drop_table("state_liability_records")
