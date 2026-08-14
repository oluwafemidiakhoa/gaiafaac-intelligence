"""Add immutable fiscal ledger foundation tables.

Revision ID: 20260814_0006
Revises: 20260810_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260814_0006"
down_revision: str | None = "20260810_0005"
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


def _status(name: str) -> sa.Enum:
    return sa.Enum(
        *EVIDENCE_STATUSES, name=name, native_enum=False, create_constraint=True
    )


def upgrade() -> None:
    op.create_table(
        "fiscal_claims",
        sa.Column("gaia_id", sa.String(length=120), primary_key=True),
        sa.Column("object_type", sa.String(length=40), nullable=False),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("fiscal_period", sa.String(length=32), nullable=False),
        sa.Column("metric", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Numeric(30, 6)),
        sa.Column("value_text", sa.String(length=160)),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("currency", sa.String(length=3)),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_page", sa.Integer()),
        sa.Column("source_table", sa.String(length=160)),
        sa.Column("extraction_method", sa.String(length=40), nullable=False),
        sa.Column(
            "evidence_status", _status("fiscal_claim_evidence_status"), nullable=False
        ),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column("supersedes_gaia_id", sa.String(length=120)),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(source_sha256) = 64", name="ck_fiscal_claim_source_hash"
        ),
        sa.CheckConstraint(
            "currency IS NULL OR length(currency) = 3", name="ck_fiscal_claim_currency"
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["source_documents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_gaia_id"], ["fiscal_claims.gaia_id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_fiscal_claims_jurisdiction_period",
        "fiscal_claims",
        ["state_id", "fiscal_period"],
    )
    op.create_index("ix_fiscal_claims_status", "fiscal_claims", ["evidence_status"])

    op.create_table(
        "evidence_verifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("claim_gaia_id", sa.String(length=120), nullable=False, unique=True),
        sa.Column("status", _status("evidence_verification_status"), nullable=False),
        sa.Column("source_verified", sa.Boolean(), nullable=False),
        sa.Column("reconciled", sa.Boolean()),
        sa.Column("human_reviewed", sa.Boolean(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["claim_gaia_id"], ["fiscal_claims.gaia_id"], ondelete="CASCADE"
        ),
    )

    op.create_table(
        "evidence_manifests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject_gaia_id", sa.String(length=120), nullable=False),
        sa.Column("manifest_version", sa.String(length=80), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("canonicalization_version", sa.String(length=80), nullable=False),
        sa.Column(
            "hash_algorithm",
            sa.String(length=20),
            nullable=False,
            server_default="sha256",
        ),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(payload_sha256) = 64", name="ck_evidence_manifest_hash"
        ),
        sa.UniqueConstraint(
            "subject_gaia_id", "payload_sha256", name="uq_manifest_subject_hash"
        ),
    )
    op.create_index(
        "ix_evidence_manifests_subject_gaia_id",
        "evidence_manifests",
        ["subject_gaia_id"],
    )

    op.create_table(
        "fiscal_proofs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("gaia_id", sa.String(length=120), nullable=False, unique=True),
        sa.Column("manifest_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column("integrity_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_proof_gaia_id", sa.String(length=120)),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("length(integrity_hash) = 64", name="ck_fiscal_proof_hash"),
        sa.ForeignKeyConstraint(
            ["gaia_id"], ["fiscal_claims.gaia_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["manifest_id"], ["evidence_manifests.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["previous_proof_gaia_id"], ["fiscal_proofs.gaia_id"], ondelete="RESTRICT"
        ),
    )

    op.create_table(
        "fiscal_states",
        sa.Column("fiscal_state_id", sa.String(length=120), primary_key=True),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fiscal_period", sa.String(length=32), nullable=False),
        sa.Column(
            "ledger_status", _status("fiscal_state_ledger_status"), nullable=False
        ),
        sa.Column("evidence_coverage", sa.Numeric(5, 4)),
        sa.Column("evidence_coverage_status", sa.String(length=40), nullable=False),
        sa.Column("domains", sa.JSON(), nullable=False),
        sa.Column("evidence_integrity", sa.JSON(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("manifest_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("integrity_hash", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column("previous_state_id", sa.String(length=120)),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("length(integrity_hash) = 64", name="ck_fiscal_state_hash"),
        sa.CheckConstraint(
            "evidence_coverage IS NULL OR (evidence_coverage >= 0 AND evidence_coverage <= 1)",
            name="ck_fiscal_state_coverage_range",
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["manifest_id"], ["evidence_manifests.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["previous_state_id"],
            ["fiscal_states.fiscal_state_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "state_id", "effective_at", "integrity_hash", name="uq_fiscal_state_version"
        ),
    )
    op.create_index(
        "ix_fiscal_states_jurisdiction_effective",
        "fiscal_states",
        ["state_id", "effective_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_fiscal_states_jurisdiction_effective", table_name="fiscal_states")
    op.drop_table("fiscal_states")
    op.drop_table("fiscal_proofs")
    op.drop_index(
        "ix_evidence_manifests_subject_gaia_id", table_name="evidence_manifests"
    )
    op.drop_table("evidence_manifests")
    op.drop_table("evidence_verifications")
    op.drop_index("ix_fiscal_claims_status", table_name="fiscal_claims")
    op.drop_index("ix_fiscal_claims_jurisdiction_period", table_name="fiscal_claims")
    op.drop_table("fiscal_claims")
