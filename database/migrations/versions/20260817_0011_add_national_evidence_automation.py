"""Add durable national-evidence automation records.

Revision ID: 20260817_0011
Revises: 20260816_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260817_0011"
down_revision: str | None = "20260816_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "national_evidence_sync_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("candidates_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidates_archived", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deferred", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quarantined", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=False),
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
    )

    op.create_table(
        "national_evidence_candidates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "first_seen_run_id",
            sa.Uuid(),
            sa.ForeignKey("national_evidence_sync_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_run_id",
            sa.Uuid(),
            sa.ForeignKey("national_evidence_sync_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "extraction_run_id",
            sa.Uuid(),
            sa.ForeignKey("extraction_runs.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "reporting_period_id",
            sa.Uuid(),
            sa.ForeignKey("reporting_periods.id", ondelete="SET NULL"),
        ),
        sa.Column("source_organization", sa.String(length=200), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("publication_date", sa.Date()),
        sa.Column("content_type", sa.String(length=160), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reason_code", sa.String(length=120)),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("extracted_claims", sa.JSON()),
        sa.Column("disbursement_month", sa.Date()),
        sa.Column("allocation_period_month", sa.Date()),
        sa.Column(
            "source_type",
            sa.String(length=80),
            nullable=False,
            server_default="official_government_press_release",
        ),
        sa.Column(
            "source_authority",
            sa.String(length=40),
            nullable=False,
            server_default="official_secondary",
        ),
        sa.Column(
            "canonical_source_status",
            sa.String(length=40),
            nullable=False,
            server_default="missing",
        ),
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
            "length(sha256) = 64", name="ck_national_candidate_sha256_length"
        ),
        sa.CheckConstraint(
            "byte_length > 0", name="ck_national_candidate_positive_bytes"
        ),
        sa.UniqueConstraint("sha256", name="uq_national_candidate_sha256"),
    )
    op.create_index(
        "ix_national_candidate_status", "national_evidence_candidates", ["status"]
    )
    op.create_index(
        "ix_national_candidate_period",
        "national_evidence_candidates",
        ["reporting_period_id"],
    )
    op.create_index(
        "ix_national_candidate_source_url",
        "national_evidence_candidates",
        ["source_url"],
    )


def downgrade() -> None:
    op.drop_index("ix_national_candidate_source_url", table_name="national_evidence_candidates")
    op.drop_index("ix_national_candidate_period", table_name="national_evidence_candidates")
    op.drop_index("ix_national_candidate_status", table_name="national_evidence_candidates")
    op.drop_table("national_evidence_candidates")
    op.drop_table("national_evidence_sync_runs")
