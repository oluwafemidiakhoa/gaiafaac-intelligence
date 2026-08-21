"""Add durable organization Evidence Rooms.

Revision ID: 20260821_0020
Revises: 20260820_0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0020"
down_revision: str | None = "20260820_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_rooms",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
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
            "status IN ('open', 'closed', 'archived')",
            name="ck_evidence_room_status",
        ),
    )
    op.create_index("ix_evidence_rooms_organization_id", "evidence_rooms", ["organization_id"])
    op.create_index(
        "ix_evidence_rooms_created_by_user_id", "evidence_rooms", ["created_by_user_id"]
    )
    op.create_index(
        "ix_evidence_rooms_org_created", "evidence_rooms", ["organization_id", "created_at"]
    )
    op.create_index(
        "ix_evidence_rooms_org_status", "evidence_rooms", ["organization_id", "status"]
    )

    op.create_table(
        "evidence_room_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("evidence_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "captured_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reference_kind", sa.String(length=32), nullable=False),
        sa.Column("reference_id", sa.String(length=240), nullable=False),
        sa.Column("reference_uri", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("record_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "reference_kind IN ('organization_alert', 'fiscal_proof', 'decision_packet', 'source', 'fiscal_event')",
            name="ck_evidence_room_reference_kind",
        ),
        sa.CheckConstraint(
            "source_sha256 IS NULL OR length(source_sha256) = 64",
            name="ck_evidence_room_source_hash",
        ),
        sa.CheckConstraint(
            "length(record_sha256) = 64",
            name="ck_evidence_room_record_hash",
        ),
        sa.UniqueConstraint(
            "room_id", "reference_kind", "reference_id", name="uq_evidence_room_reference"
        ),
    )
    op.create_index("ix_evidence_room_evidence_room_id", "evidence_room_evidence", ["room_id"])
    op.create_index(
        "ix_evidence_room_evidence_captured_by_user_id",
        "evidence_room_evidence",
        ["captured_by_user_id"],
    )
    op.create_index(
        "ix_evidence_room_evidence_room_captured",
        "evidence_room_evidence",
        ["room_id", "captured_at"],
    )

    op.create_table(
        "evidence_room_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("evidence_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
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
    op.create_index("ix_evidence_room_notes_room_id", "evidence_room_notes", ["room_id"])
    op.create_index(
        "ix_evidence_room_notes_author_user_id", "evidence_room_notes", ["author_user_id"]
    )
    op.create_index(
        "ix_evidence_room_notes_room_created", "evidence_room_notes", ["room_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_evidence_room_notes_room_created", table_name="evidence_room_notes")
    op.drop_index("ix_evidence_room_notes_author_user_id", table_name="evidence_room_notes")
    op.drop_index("ix_evidence_room_notes_room_id", table_name="evidence_room_notes")
    op.drop_table("evidence_room_notes")

    op.drop_index(
        "ix_evidence_room_evidence_room_captured", table_name="evidence_room_evidence"
    )
    op.drop_index(
        "ix_evidence_room_evidence_captured_by_user_id", table_name="evidence_room_evidence"
    )
    op.drop_index("ix_evidence_room_evidence_room_id", table_name="evidence_room_evidence")
    op.drop_table("evidence_room_evidence")

    op.drop_index("ix_evidence_rooms_org_status", table_name="evidence_rooms")
    op.drop_index("ix_evidence_rooms_org_created", table_name="evidence_rooms")
    op.drop_index("ix_evidence_rooms_created_by_user_id", table_name="evidence_rooms")
    op.drop_index("ix_evidence_rooms_organization_id", table_name="evidence_rooms")
    op.drop_table("evidence_rooms")
