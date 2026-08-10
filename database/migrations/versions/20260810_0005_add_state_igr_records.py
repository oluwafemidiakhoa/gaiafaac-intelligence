"""add state IGR evidence records

Revision ID: 20260810_0005
Revises: 20260801_0004
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0005"
down_revision: str | None = "20260801_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "state_igr_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("period_type", sa.String(length=9), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("igr_amount", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column("igr_amount_original", sa.String(length=120), nullable=False),
        sa.Column("reported_unit", sa.String(length=20), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_table", sa.String(length=160), nullable=True),
        sa.Column("verification_status", sa.String(length=23), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("period_start <= period_end", name="ck_state_igr_period_order"),
        sa.CheckConstraint("igr_amount >= 0", name="ck_state_igr_amount_nonnegative"),
        sa.CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_state_igr_demo_not_published"
        ),
        sa.CheckConstraint(
            "(period_type = 'annual' AND quarter IS NULL) OR "
            "(period_type = 'quarterly' AND quarter BETWEEN 1 AND 4)",
            name="ck_state_igr_period_shape",
        ),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["source_documents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "state_id", "period_start", "period_end", name="uq_state_igr_state_period"
        ),
    )
    op.create_index(
        "ix_state_igr_records_state_id", "state_igr_records", ["state_id"], unique=False
    )
    op.create_index(
        "ix_state_igr_records_source_document_id",
        "state_igr_records",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_state_igr_year_state",
        "state_igr_records",
        ["fiscal_year", "state_id"],
        unique=False,
    )
    op.create_index(
        "ix_state_igr_period",
        "state_igr_records",
        ["period_start", "period_end"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_state_igr_period", table_name="state_igr_records")
    op.drop_index("ix_state_igr_year_state", table_name="state_igr_records")
    op.drop_index("ix_state_igr_records_source_document_id", table_name="state_igr_records")
    op.drop_index("ix_state_igr_records_state_id", table_name="state_igr_records")
    op.drop_table("state_igr_records")
