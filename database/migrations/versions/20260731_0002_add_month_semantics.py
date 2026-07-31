"""add month-semantics columns to reporting_periods

Adds ``disbursement_month`` (customer-facing key) and ``allocation_period_month`` (the
revenue period a report describes). ``revenue_month`` is retained, deprecated, and treated
as the disbursement month for backfill. No existing data is deleted or altered destructively.

Revision ID: 20260731_0002
Revises: 20260723_0001
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0002"
down_revision: str | None = "20260723_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this revision."""
    op.add_column(
        "reporting_periods", sa.Column("disbursement_month", sa.Date(), nullable=True)
    )
    op.add_column(
        "reporting_periods",
        sa.Column("allocation_period_month", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_reporting_periods_disbursement_month",
        "reporting_periods",
        ["disbursement_month"],
    )
    # revenue_month has historically held the disbursement month: backfill it forward.
    # allocation_period_month is intentionally left NULL — it cannot be established
    # confidently from existing rows, and the pipeline never guesses.
    op.execute(
        "UPDATE reporting_periods SET disbursement_month = revenue_month "
        "WHERE disbursement_month IS NULL"
    )


def downgrade() -> None:
    """Revert this revision."""
    op.drop_index(
        "ix_reporting_periods_disbursement_month", table_name="reporting_periods"
    )
    op.drop_column("reporting_periods", "allocation_period_month")
    op.drop_column("reporting_periods", "disbursement_month")
