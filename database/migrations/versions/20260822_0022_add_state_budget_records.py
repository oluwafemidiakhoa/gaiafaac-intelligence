"""Add staged approved state-budget evidence records.

Revision ID: 20260822_0022
Revises: 20260821_0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0022"
down_revision: str | None = "20260821_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BUDGET_METRICS = (
    "recurrent_revenue",
    "faac_revenue",
    "independent_revenue",
    "recurrent_expenditure",
    "personnel_cost",
    "other_non_debt_recurrent",
    "budgeted_debt_service",
    "transfer_to_capital_account",
    "other_receipts",
    "aid_and_grants",
    "capital_development_fund_receipts",
    "capital_expenditure",
    "total_revenue",
    "total_expenditure",
)


def upgrade() -> None:
    op.create_table(
        "state_budget_records",
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
        sa.Column("amount", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column("amount_original", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_table", sa.String(length=200), nullable=True),
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
        sa.CheckConstraint("fiscal_year >= 2000", name="ck_state_budget_fiscal_year"),
        sa.CheckConstraint("amount >= 0", name="ck_state_budget_amount_nonnegative"),
        sa.CheckConstraint("length(currency) = 3", name="ck_state_budget_currency_length"),
        sa.CheckConstraint(
            "metric IN (" + ", ".join(repr(metric) for metric in _BUDGET_METRICS) + ")",
            name="ck_state_budget_metric",
        ),
        sa.CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_budget_demo_not_published",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "state_id",
            "metric",
            name="uq_state_budget_source_state_metric",
        ),
    )
    op.create_index("ix_state_budget_records_state_id", "state_budget_records", ["state_id"])
    op.create_index(
        "ix_state_budget_records_source_document_id",
        "state_budget_records",
        ["source_document_id"],
    )
    op.create_index(
        "ix_state_budget_period_metric",
        "state_budget_records",
        ["fiscal_year", "metric"],
    )
    op.create_index(
        "ix_state_budget_state_year",
        "state_budget_records",
        ["state_id", "fiscal_year"],
    )


def downgrade() -> None:
    op.drop_index("ix_state_budget_state_year", table_name="state_budget_records")
    op.drop_index("ix_state_budget_period_metric", table_name="state_budget_records")
    op.drop_index("ix_state_budget_records_source_document_id", table_name="state_budget_records")
    op.drop_index("ix_state_budget_records_state_id", table_name="state_budget_records")
    op.drop_table("state_budget_records")
