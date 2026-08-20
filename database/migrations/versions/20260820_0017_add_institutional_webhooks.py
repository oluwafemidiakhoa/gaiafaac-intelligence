"""Add institutional webhook endpoints and delivery history.

Revision ID: 20260820_0017
Revises: 20260820_0016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0017"
down_revision: str | None = "20260820_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_webhook_endpoints",
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
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column("jurisdiction_codes", sa.JSON(), nullable=False),
        sa.Column("secret_salt", sa.String(length=64), nullable=False),
        sa.Column("secret_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(
        "ix_organization_webhook_endpoints_organization_id",
        "organization_webhook_endpoints",
        ["organization_id"],
    )
    op.create_index(
        "ix_org_webhook_endpoints_org_enabled",
        "organization_webhook_endpoints",
        ["organization_id", "enabled"],
    )
    op.create_index(
        "ix_org_webhook_endpoints_org_created",
        "organization_webhook_endpoints",
        ["organization_id", "created_at"],
    )

    op.create_table(
        "organization_webhook_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "endpoint_id",
            sa.Uuid(),
            sa.ForeignKey("organization_webhook_endpoints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fiscal_event_id",
            sa.String(length=120),
            sa.ForeignKey("fiscal_events.event_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body_excerpt", sa.String(length=1000), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("signing_secret_version", sa.Integer(), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
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
            "endpoint_id", "fiscal_event_id", name="uq_org_webhook_delivery_endpoint_event"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'retrying', 'delivered', 'dead_letter', 'deferred')",
            name="ck_org_webhook_delivery_status",
        ),
        sa.CheckConstraint(
            "length(payload_sha256) = 64", name="ck_org_webhook_payload_hash"
        ),
    )
    op.create_index(
        "ix_organization_webhook_deliveries_organization_id",
        "organization_webhook_deliveries",
        ["organization_id"],
    )
    op.create_index(
        "ix_org_webhook_deliveries_endpoint_status",
        "organization_webhook_deliveries",
        ["endpoint_id", "status"],
    )
    op.create_index(
        "ix_org_webhook_deliveries_org_created",
        "organization_webhook_deliveries",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_org_webhook_deliveries_next_attempt",
        "organization_webhook_deliveries",
        ["status", "next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_org_webhook_deliveries_next_attempt", table_name="organization_webhook_deliveries"
    )
    op.drop_index(
        "ix_org_webhook_deliveries_org_created", table_name="organization_webhook_deliveries"
    )
    op.drop_index(
        "ix_org_webhook_deliveries_endpoint_status",
        table_name="organization_webhook_deliveries",
    )
    op.drop_index(
        "ix_organization_webhook_deliveries_organization_id",
        table_name="organization_webhook_deliveries",
    )
    op.drop_table("organization_webhook_deliveries")
    op.drop_index(
        "ix_org_webhook_endpoints_org_created", table_name="organization_webhook_endpoints"
    )
    op.drop_index(
        "ix_org_webhook_endpoints_org_enabled", table_name="organization_webhook_endpoints"
    )
    op.drop_index(
        "ix_organization_webhook_endpoints_organization_id",
        table_name="organization_webhook_endpoints",
    )
    op.drop_table("organization_webhook_endpoints")
