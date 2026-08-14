"""Add evidence trust, revision, conflict, and source registry tables.

Revision ID: 20260814_0007
Revises: 20260814_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260814_0007"
down_revision: str | None = "20260814_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EVIDENCE_STATUSES = (
    "unavailable",
    "detected",
    "pending_extraction",
    "extracted",
    "pending_verification",
    "verified",
    "partial",
    "conflicting",
    "superseded",
    "rejected",
)
CONFLICT_STATUSES = ("unresolved", "resolved", "dismissed")


def upgrade() -> None:
    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("publisher", sa.String(length=200), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("fiscal_domain", sa.String(length=40), nullable=False),
        sa.Column("reporting_cadence", sa.String(length=40)),
        sa.Column("canonical_url", sa.Text()),
        sa.Column("document_url", sa.Text()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("document_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_status", sa.String(length=40), nullable=False),
        sa.Column("extraction_status", sa.String(length=40), nullable=False),
        sa.Column(
            "verification_status",
            sa.Enum(
                *EVIDENCE_STATUSES,
                name="evidence_source_verification_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "revision_detected", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("supersedes_source_id", sa.Uuid()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(document_sha256) = 64", name="ck_evidence_source_hash"
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["source_documents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["supersedes_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "state_id",
            "fiscal_domain",
            name="uq_evidence_source_document_jurisdiction_domain",
        ),
    )
    op.create_index("ix_evidence_sources_publisher", "evidence_sources", ["publisher"])
    op.create_index(
        "ix_evidence_sources_jurisdiction_domain",
        "evidence_sources",
        ["state_id", "fiscal_domain"],
    )

    op.create_table(
        "claim_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("previous_claim_gaia_id", sa.String(length=120), nullable=False),
        sa.Column("revised_claim_gaia_id", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.String(length=80), nullable=False),
        sa.Column("value_delta", sa.Numeric(30, 6)),
        sa.Column("value_delta_text", sa.String(length=160)),
        sa.Column("value_change_percent", sa.Numeric(18, 6)),
        sa.Column("value_change_percent_text", sa.String(length=80)),
        sa.Column("material_change", sa.Boolean()),
        sa.Column("source_revision", sa.Boolean(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "previous_claim_gaia_id <> revised_claim_gaia_id",
            name="ck_claim_revision_distinct_claims",
        ),
        sa.ForeignKeyConstraint(
            ["previous_claim_gaia_id"], ["fiscal_claims.gaia_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["revised_claim_gaia_id"], ["fiscal_claims.gaia_id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "revised_claim_gaia_id", name="uq_claim_revision_revised_claim"
        ),
    )

    op.create_table(
        "evidence_conflicts",
        sa.Column("conflict_id", sa.String(length=120), primary_key=True),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("object_type", sa.String(length=40), nullable=False),
        sa.Column("fiscal_period", sa.String(length=32), nullable=False),
        sa.Column("metric", sa.String(length=120), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                *CONFLICT_STATUSES,
                name="evidence_conflict_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_evidence_conflicts_jurisdiction_metric",
        "evidence_conflicts",
        ["state_id", "object_type", "fiscal_period", "metric"],
    )

    op.create_table(
        "evidence_conflict_claims",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conflict_id", sa.String(length=120), nullable=False),
        sa.Column("claim_gaia_id", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conflict_id"], ["evidence_conflicts.conflict_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["claim_gaia_id"], ["fiscal_claims.gaia_id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("conflict_id", "claim_gaia_id", name="uq_conflict_claim"),
    )


def downgrade() -> None:
    op.drop_table("evidence_conflict_claims")
    op.drop_index(
        "ix_evidence_conflicts_jurisdiction_metric", table_name="evidence_conflicts"
    )
    op.drop_table("evidence_conflicts")
    op.drop_table("claim_revisions")
    op.drop_index(
        "ix_evidence_sources_jurisdiction_domain", table_name="evidence_sources"
    )
    op.drop_index("ix_evidence_sources_publisher", table_name="evidence_sources")
    op.drop_table("evidence_sources")
