"""Add auditable OAGF source discovery and synchronization records.

Revision ID: 20260816_0010
Revises: 20260815_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260816_0010"
down_revision: str | None = "20260815_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oagf_sync_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hub_url", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column(
            "categories_discovered", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("pages_checked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "documents_discovered", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "documents_archived", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("duplicates_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revisions_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "inaccessible_documents", sa.Integer(), nullable=False, server_default="0"
        ),
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
        "oagf_discovery_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "first_seen_run_id",
            sa.Uuid(),
            sa.ForeignKey("oagf_sync_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_run_id",
            sa.Uuid(),
            sa.ForeignKey("oagf_sync_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            sa.Uuid(),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "previous_record_id",
            sa.Uuid(),
            sa.ForeignKey("oagf_discovery_records.id", ondelete="SET NULL"),
        ),
        sa.Column("source_organization", sa.String(length=200), nullable=False),
        sa.Column("category_name", sa.String(length=160), nullable=False),
        sa.Column("category_slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("publication_identity", sa.Text(), nullable=False),
        sa.Column("publication_page_url", sa.Text()),
        sa.Column("document_url", sa.Text(), nullable=False),
        sa.Column("discovery_url", sa.Text(), nullable=False),
        sa.Column("source_publication_date", sa.Date()),
        sa.Column("displayed_year", sa.String(length=40)),
        sa.Column("displayed_month", sa.String(length=40)),
        sa.Column("first_discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("downloaded_filename", sa.String(length=500)),
        sa.Column("content_type", sa.String(length=160)),
        sa.Column("byte_length", sa.Integer()),
        sa.Column("sha256", sa.String(length=64)),
        sa.Column("storage_path", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("classification", sa.String(length=120), nullable=False),
        sa.Column("classification_confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("classification_method", sa.String(length=80), nullable=False),
        sa.Column(
            "extraction_status",
            sa.String(length=40),
            nullable=False,
            server_default="not_requested",
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
            "sha256 IS NULL OR length(sha256) = 64",
            name="ck_oagf_discovery_sha256_length",
        ),
        sa.CheckConstraint(
            "classification_confidence >= 0 AND classification_confidence <= 1",
            name="ck_oagf_discovery_confidence_range",
        ),
        sa.UniqueConstraint(
            "publication_identity",
            "version",
            name="uq_oagf_discovery_identity_version",
        ),
    )
    op.create_index(
        "ix_oagf_discovery_category", "oagf_discovery_records", ["category_slug"]
    )
    op.create_index("ix_oagf_discovery_sha256", "oagf_discovery_records", ["sha256"])
    op.create_index(
        "ix_oagf_discovery_source_date",
        "oagf_discovery_records",
        ["source_publication_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_oagf_discovery_source_date", table_name="oagf_discovery_records")
    op.drop_index("ix_oagf_discovery_sha256", table_name="oagf_discovery_records")
    op.drop_index("ix_oagf_discovery_category", table_name="oagf_discovery_records")
    op.drop_table("oagf_discovery_records")
    op.drop_table("oagf_sync_runs")
