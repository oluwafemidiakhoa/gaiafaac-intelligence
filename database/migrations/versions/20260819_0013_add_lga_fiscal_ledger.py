"""Add governed local-government fiscal ledger.

Revision ID: 20260819_0013
Revises: 20260818_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_0013"
down_revision: str | None = "20260818_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "local_governments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "state_id",
            sa.Uuid(),
            sa.ForeignKey("states.state_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("official_name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("state_id", "slug", name="uq_local_government_state_slug"),
        sa.UniqueConstraint(
            "state_id", "official_name", name="uq_local_government_state_name"
        ),
    )
    op.create_index("ix_local_governments_state_id", "local_governments", ["state_id"])
    op.create_index(
        "ix_local_governments_state_name",
        "local_governments",
        ["state_id", "official_name"],
    )

    op.create_table(
        "local_government_allocations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "reporting_period_id",
            sa.Uuid(),
            sa.ForeignKey("reporting_periods.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "local_government_id",
            sa.Uuid(),
            sa.ForeignKey("local_governments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "extraction_run_id",
            sa.Uuid(),
            sa.ForeignKey("extraction_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("net_statutory_allocation", sa.Numeric(24, 2)),
        sa.Column("deduction_amount", sa.Numeric(24, 2)),
        sa.Column("ecology_share", sa.Numeric(24, 2)),
        sa.Column("ecology_transfer", sa.Numeric(24, 2)),
        sa.Column("net_ecology_share", sa.Numeric(24, 2)),
        sa.Column("vat_amount", sa.Numeric(24, 2)),
        sa.Column("total_net_allocation", sa.Numeric(24, 2), nullable=False),
        sa.Column("net_statutory_original", sa.String(length=120)),
        sa.Column("deduction_original", sa.String(length=120)),
        sa.Column("ecology_share_original", sa.String(length=120)),
        sa.Column("ecology_transfer_original", sa.String(length=120)),
        sa.Column("net_ecology_original", sa.String(length=120)),
        sa.Column("vat_original", sa.String(length=120)),
        sa.Column("total_net_original", sa.String(length=120), nullable=False),
        sa.Column("reported_unit", sa.String(length=40), nullable=False, server_default="naira"),
        sa.Column("source_page", sa.Integer()),
        sa.Column("source_table", sa.String(length=80), nullable=False, server_default="Table IV"),
        sa.Column(
            "verification_status",
            sa.String(length=40),
            nullable=False,
            server_default="requires_review",
        ),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.UniqueConstraint(
            "reporting_period_id",
            "local_government_id",
            name="uq_lga_allocation_period_local_government",
        ),
        sa.CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_lga_allocation_demo_not_published"
        ),
    )
    op.create_index(
        "ix_local_government_allocations_reporting_period_id",
        "local_government_allocations",
        ["reporting_period_id"],
    )
    op.create_index(
        "ix_local_government_allocations_local_government_id",
        "local_government_allocations",
        ["local_government_id"],
    )
    op.create_index(
        "ix_local_government_allocations_source_document_id",
        "local_government_allocations",
        ["source_document_id"],
    )
    op.create_index(
        "ix_local_government_allocations_extraction_run_id",
        "local_government_allocations",
        ["extraction_run_id"],
    )
    op.create_index(
        "ix_lga_allocations_period_published",
        "local_government_allocations",
        ["reporting_period_id", "is_published"],
    )

    op.create_table(
        "local_government_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "reporting_period_id",
            sa.Uuid(),
            sa.ForeignKey("reporting_periods.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "extraction_run_id",
            sa.Uuid(),
            sa.ForeignKey("extraction_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="requires_review"),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("blocking_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("published_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.UniqueConstraint("extraction_run_id", name="uq_lga_review_extraction_run"),
    )
    op.create_index(
        "ix_lga_review_period", "local_government_reviews", ["reporting_period_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_lga_review_period", table_name="local_government_reviews")
    op.drop_table("local_government_reviews")
    op.drop_index(
        "ix_lga_allocations_period_published", table_name="local_government_allocations"
    )
    op.drop_index(
        "ix_local_government_allocations_extraction_run_id",
        table_name="local_government_allocations",
    )
    op.drop_index(
        "ix_local_government_allocations_source_document_id",
        table_name="local_government_allocations",
    )
    op.drop_index(
        "ix_local_government_allocations_local_government_id",
        table_name="local_government_allocations",
    )
    op.drop_index(
        "ix_local_government_allocations_reporting_period_id",
        table_name="local_government_allocations",
    )
    op.drop_table("local_government_allocations")
    op.drop_index("ix_local_governments_state_name", table_name="local_governments")
    op.drop_index("ix_local_governments_state_id", table_name="local_governments")
    op.drop_table("local_governments")
