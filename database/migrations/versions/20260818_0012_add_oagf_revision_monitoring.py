"""Add durable OAGF archive objects and revision review cases.

Revision ID: 20260818_0012
Revises: 20260817_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0012"
down_revision: str | None = "20260817_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oagf_archive_objects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=160), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
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
        sa.CheckConstraint("length(sha256) = 64", name="ck_oagf_archive_sha256_length"),
        sa.CheckConstraint("byte_length > 0", name="ck_oagf_archive_positive_bytes"),
        sa.UniqueConstraint("sha256", name="uq_oagf_archive_sha256"),
    )
    op.create_index(
        "ix_oagf_archive_created_at", "oagf_archive_objects", ["created_at"]
    )

    op.create_table(
        "oagf_revision_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "discovery_record_id",
            sa.Uuid(),
            sa.ForeignKey("oagf_discovery_records.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "previous_record_id",
            sa.Uuid(),
            sa.ForeignKey("oagf_discovery_records.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "previous_source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "reporting_period_id",
            sa.Uuid(),
            sa.ForeignKey("reporting_periods.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending_review"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_code", sa.String(length=80)),
        sa.Column("review_note", sa.Text()),
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
        sa.UniqueConstraint(
            "discovery_record_id", name="uq_oagf_revision_discovery_record"
        ),
    )
    op.create_index(
        "ix_oagf_revision_case_status", "oagf_revision_cases", ["status"]
    )
    op.create_index(
        "ix_oagf_revision_case_period", "oagf_revision_cases", ["reporting_period_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_oagf_revision_case_period", table_name="oagf_revision_cases")
    op.drop_index("ix_oagf_revision_case_status", table_name="oagf_revision_cases")
    op.drop_table("oagf_revision_cases")
    op.drop_index("ix_oagf_archive_created_at", table_name="oagf_archive_objects")
    op.drop_table("oagf_archive_objects")
