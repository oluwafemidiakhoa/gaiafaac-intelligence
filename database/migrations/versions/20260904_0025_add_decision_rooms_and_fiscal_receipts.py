"""Add Decision Room context and immutable Fiscal Receipts.

Revision ID: 20260904_0025
Revises: 20260822_0024
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260904_0025"
down_revision: str | None = "20260822_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evidence_rooms", sa.Column("decision_question", sa.Text(), nullable=True))
    op.add_column(
        "evidence_rooms",
        sa.Column("jurisdictions", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "evidence_rooms",
        sa.Column("evidence_domains", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column("evidence_rooms", sa.Column("baseline_date", sa.Date(), nullable=True))
    op.add_column(
        "evidence_rooms",
        sa.Column("evidence_cutoff", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "fiscal_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("evidence_rooms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evidence_cutoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "methodology_version",
            sa.String(length=80),
            nullable=False,
            server_default="fiscal-receipt-v1",
        ),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("public_manifest", sa.JSON(), nullable=False),
        sa.Column("receipt_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "length(receipt_sha256) = 64",
            name="ck_fiscal_receipt_hash_length",
        ),
        sa.UniqueConstraint(
            "room_id",
            "receipt_sha256",
            name="uq_fiscal_receipt_room_hash",
        ),
    )
    op.create_index("ix_fiscal_receipts_organization_id", "fiscal_receipts", ["organization_id"])
    op.create_index("ix_fiscal_receipts_room_id", "fiscal_receipts", ["room_id"])
    op.create_index(
        "ix_fiscal_receipts_created_by_user_id",
        "fiscal_receipts",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_fiscal_receipts_org_created",
        "fiscal_receipts",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_fiscal_receipts_room_created",
        "fiscal_receipts",
        ["room_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_fiscal_receipts_room_created", table_name="fiscal_receipts")
    op.drop_index("ix_fiscal_receipts_org_created", table_name="fiscal_receipts")
    op.drop_index("ix_fiscal_receipts_created_by_user_id", table_name="fiscal_receipts")
    op.drop_index("ix_fiscal_receipts_room_id", table_name="fiscal_receipts")
    op.drop_index("ix_fiscal_receipts_organization_id", table_name="fiscal_receipts")
    op.drop_table("fiscal_receipts")

    op.drop_column("evidence_rooms", "evidence_cutoff")
    op.drop_column("evidence_rooms", "baseline_date")
    op.drop_column("evidence_rooms", "evidence_domains")
    op.drop_column("evidence_rooms", "jurisdictions")
    op.drop_column("evidence_rooms", "decision_question")
