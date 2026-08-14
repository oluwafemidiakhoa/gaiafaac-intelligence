"""Add fiscal lifecycle events and immutable certificates.

Revision ID: 20260814_0008
Revises: 20260814_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260814_0008"
down_revision: str | None = "20260814_0007"
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
EVENT_SEVERITIES = ("informational", "notable", "material", "critical")


def upgrade() -> None:
    op.create_table(
        "fiscal_events",
        sa.Column("event_id", sa.String(length=120), primary_key=True),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column(
            "severity",
            sa.Enum(
                *EVENT_SEVERITIES,
                name="fiscal_event_severity",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "evidence_status",
            sa.Enum(
                *EVIDENCE_STATUSES,
                name="fiscal_event_evidence_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("calculation", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("fiscal_state_id", sa.String(length=120)),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["fiscal_state_id"], ["fiscal_states.fiscal_state_id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_fiscal_events_jurisdiction_effective",
        "fiscal_events",
        ["state_id", "effective_at"],
    )
    op.create_index(
        "ix_fiscal_events_type_severity",
        "fiscal_events",
        ["event_type", "severity"],
    )

    op.create_table(
        "fiscal_certificates",
        sa.Column("gaia_id", sa.String(length=120), primary_key=True),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("fiscal_state_id", sa.String(length=120), nullable=False),
        sa.Column("fiscal_period", sa.String(length=32), nullable=False),
        sa.Column("manifest_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("integrity_hash", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("methodology_version", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(integrity_hash) = 64", name="ck_fiscal_certificate_hash"
        ),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["fiscal_state_id"], ["fiscal_states.fiscal_state_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["manifest_id"], ["evidence_manifests.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_fiscal_certificates_jurisdiction_issued",
        "fiscal_certificates",
        ["state_id", "issued_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fiscal_certificates_jurisdiction_issued",
        table_name="fiscal_certificates",
    )
    op.drop_table("fiscal_certificates")
    op.drop_index("ix_fiscal_events_type_severity", table_name="fiscal_events")
    op.drop_index("ix_fiscal_events_jurisdiction_effective", table_name="fiscal_events")
    op.drop_table("fiscal_events")
