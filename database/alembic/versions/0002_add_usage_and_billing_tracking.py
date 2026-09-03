"""Add usage logging and billing event tracking tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-03 15:35:13.298765

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create usage_logs, billing_events, and invoices tables."""
    # UsageLog table
    op.create_table(
        "usage_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subscription_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("endpoint", sa.String(200), nullable=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["organization_subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_logs_org_created", "usage_logs", ["organization_id", "created_at"])
    op.create_index(
        "ix_usage_logs_subscription_created",
        "usage_logs",
        ["subscription_id", "created_at"],
    )
    op.create_index("ix_usage_logs_event_type", "usage_logs", ["event_type"])

    # BillingEvent table
    op.create_table(
        "billing_events",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subscription_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("amount_naira", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_invoiced", sa.Boolean(), default=False),
        sa.Column("invoice_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["organization_subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_events_org_created", "billing_events", ["organization_id", "created_at"])
    op.create_index("ix_billing_events_event_type", "billing_events", ["event_type"])

    # Invoice table
    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subscription_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("subtotal_naira", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_naira", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_naira", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("line_items", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["organization_subscriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id"], ["billing_events.invoice_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number", name="uq_invoices_number"),
    )
    op.create_index("ix_invoices_org_created", "invoices", ["organization_id", "created_at"])
    op.create_index("ix_invoices_status", "invoices", ["status"])


def downgrade() -> None:
    """Drop usage_logs, billing_events, and invoices tables."""
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_org_created", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("ix_billing_events_event_type", table_name="billing_events")
    op.drop_index("ix_billing_events_org_created", table_name="billing_events")
    op.drop_table("billing_events")

    op.drop_index("ix_usage_logs_event_type", table_name="usage_logs")
    op.drop_index("ix_usage_logs_subscription_created", table_name="usage_logs")
    op.drop_index("ix_usage_logs_org_created", table_name="usage_logs")
    op.drop_table("usage_logs")
