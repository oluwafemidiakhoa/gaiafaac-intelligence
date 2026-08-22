"""Add staged state budget-performance evidence records.

Revision ID: 20260822_0023
Revises: 20260822_0022
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0023"
down_revision: str | None = "20260822_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PERFORMANCE_METRICS = (
    "opening_balance",
    "recurrent_revenue",
    "faac_revenue",
    "independent_revenue",
    "recurrent_expenditure",
    "personnel_cost",
    "other_recurrent_costs",
    "overhead_cost",
    "other_recurrent",
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
        "state_budget_performance_records",
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
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("metric", sa.String(length=40), nullable=False),
        sa.Column("original_budget", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column("original_budget_text", sa.String(length=120), nullable=False),
        sa.Column("quarter_actual", sa.Numeric(precision=24, scale=2), nullable=True),
        sa.Column("quarter_actual_text", sa.String(length=120), nullable=False),
        sa.Column("ytd_actual", sa.Numeric(precision=24, scale=2), nullable=True),
        sa.Column("ytd_actual_text", sa.String(length=120), nullable=False),
        sa.Column("performance_percent", sa.Numeric(precision=9, scale=4), nullable=True),
        sa.Column("performance_percent_text", sa.String(length=40), nullable=False),
        sa.Column("balance", sa.Numeric(precision=24, scale=2), nullable=True),
        sa.Column("balance_text", sa.String(length=120), nullable=False),
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
        sa.CheckConstraint("fiscal_year >= 2000", name="ck_budget_performance_fiscal_year"),
        sa.CheckConstraint("quarter BETWEEN 1 AND 4", name="ck_budget_performance_quarter"),
        sa.CheckConstraint(
            "original_budget >= 0",
            name="ck_budget_performance_original_budget_nonnegative",
        ),
        sa.CheckConstraint(
            "quarter_actual IS NULL OR quarter_actual >= 0",
            name="ck_budget_performance_quarter_actual_nonnegative",
        ),
        sa.CheckConstraint(
            "ytd_actual IS NULL OR ytd_actual >= 0",
            name="ck_budget_performance_ytd_actual_nonnegative",
        ),
        sa.CheckConstraint(
            "performance_percent IS NULL OR performance_percent >= 0",
            name="ck_budget_performance_percent_nonnegative",
        ),
        sa.CheckConstraint("length(currency) = 3", name="ck_budget_performance_currency_length"),
        sa.CheckConstraint(
            "metric IN (" + ", ".join(repr(metric) for metric in _PERFORMANCE_METRICS) + ")",
            name="ck_budget_performance_metric",
        ),
        sa.CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_budget_performance_demo_not_published",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "state_id",
            "metric",
            name="uq_state_budget_performance_source_state_metric",
        ),
    )
    op.create_index(
        "ix_state_budget_performance_records_state_id",
        "state_budget_performance_records",
        ["state_id"],
    )
    op.create_index(
        "ix_state_budget_performance_records_source_document_id",
        "state_budget_performance_records",
        ["source_document_id"],
    )
    op.create_index(
        "ix_budget_performance_state_period",
        "state_budget_performance_records",
        ["state_id", "fiscal_year", "quarter"],
    )
    op.create_index(
        "ix_budget_performance_period_metric",
        "state_budget_performance_records",
        ["fiscal_year", "quarter", "metric"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_budget_performance_period_metric",
        table_name="state_budget_performance_records",
    )
    op.drop_index(
        "ix_budget_performance_state_period",
        table_name="state_budget_performance_records",
    )
    op.drop_index(
        "ix_state_budget_performance_records_source_document_id",
        table_name="state_budget_performance_records",
    )
    op.drop_index(
        "ix_state_budget_performance_records_state_id",
        table_name="state_budget_performance_records",
    )
    op.drop_table("state_budget_performance_records")
