"""Add canonical one-time purchase/order ledger.

Revision ID: 20260904_0031
Revises: 20260904_0030
"""

from alembic import op
import sqlalchemy as sa

revision = "20260904_0031"
down_revision = "20260904_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "one_time_purchases",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("product_code", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="paystack"),
        sa.Column("provider_reference", sa.String(length=160), nullable=False),
        sa.Column("amount_naira", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="NGN"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column(
            "fulfillment_status",
            sa.String(length=40),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("fulfillment_reference", sa.String(length=200), nullable=True),
        sa.Column("purchase_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "provider",
            "provider_reference",
            name="uq_one_time_purchase_provider_reference",
        ),
    )
    op.create_index(
        "ix_one_time_purchases_organization_id",
        "one_time_purchases",
        ["organization_id"],
    )
    op.create_index("ix_one_time_purchases_user_id", "one_time_purchases", ["user_id"])
    op.create_index(
        "ix_one_time_purchases_org_created",
        "one_time_purchases",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_one_time_purchases_status_created",
        "one_time_purchases",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_one_time_purchases_product_status",
        "one_time_purchases",
        ["product_code", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_one_time_purchases_product_status", table_name="one_time_purchases")
    op.drop_index("ix_one_time_purchases_status_created", table_name="one_time_purchases")
    op.drop_index("ix_one_time_purchases_org_created", table_name="one_time_purchases")
    op.drop_index("ix_one_time_purchases_user_id", table_name="one_time_purchases")
    op.drop_index("ix_one_time_purchases_organization_id", table_name="one_time_purchases")
    op.drop_table("one_time_purchases")
