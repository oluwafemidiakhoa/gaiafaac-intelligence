"""Add outbound Watch delivery channels, retry state and append-only attempts.

Revision ID: 20260904_0029
Revises: 20260904_0028
"""

from alembic import op
import sqlalchemy as sa

revision = "20260904_0029"
down_revision = "20260904_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("fiscal_watch_contract_deliveries") as batch:
        batch.drop_constraint(
            "uq_fiscal_watch_contract_delivery_review_channel",
            type_="unique",
        )
        batch.drop_constraint(
            "ck_fiscal_watch_contract_delivery_channel",
            type_="check",
        )
        batch.drop_constraint(
            "ck_fiscal_watch_contract_delivery_status",
            type_="check",
        )
        batch.add_column(
            sa.Column(
                "endpoint_id",
                sa.Uuid(),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column(
                "destination_key",
                sa.String(length=200),
                nullable=False,
                server_default="organization_watch_inbox",
            )
        )
        batch.add_column(sa.Column("recipient_address", sa.String(length=500), nullable=True))
        batch.add_column(
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("response_status", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("response_body_excerpt", sa.String(length=1000), nullable=True)
        )
        batch.add_column(sa.Column("last_error", sa.String(length=500), nullable=True))
        batch.add_column(sa.Column("payload_sha256", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("payload", sa.JSON(), nullable=True))
        batch.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch.create_foreign_key(
            "fk_fiscal_watch_delivery_endpoint",
            "organization_webhook_endpoints",
            ["endpoint_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_check_constraint(
            "ck_fiscal_watch_contract_delivery_channel",
            "channel IN ('in_app', 'email', 'webhook')",
        )
        batch.create_check_constraint(
            "ck_fiscal_watch_contract_delivery_status",
            "status IN ('pending', 'delivered', 'retrying', 'dead_letter', 'deferred', 'failed')",
        )
        batch.create_unique_constraint(
            "uq_fiscal_watch_contract_delivery_destination",
            ["review_id", "channel", "destination_key"],
        )

    op.create_index(
        "ix_fiscal_watch_contract_deliveries_status_next",
        "fiscal_watch_contract_deliveries",
        ["status", "next_attempt_at"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_deliveries_endpoint_id",
        "fiscal_watch_contract_deliveries",
        ["endpoint_id"],
    )

    op.create_table(
        "fiscal_watch_contract_delivery_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body_excerpt", sa.String(length=1000), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["fiscal_watch_contract_deliveries.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "delivery_id",
            "attempt_number",
            name="uq_fiscal_watch_contract_delivery_attempt_number",
        ),
    )
    op.create_index(
        "ix_fiscal_watch_contract_delivery_attempts_delivery",
        "fiscal_watch_contract_delivery_attempts",
        ["delivery_id", "attempt_number"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fiscal_watch_contract_delivery_attempts_delivery",
        table_name="fiscal_watch_contract_delivery_attempts",
    )
    op.drop_table("fiscal_watch_contract_delivery_attempts")

    op.drop_index(
        "ix_fiscal_watch_contract_deliveries_endpoint_id",
        table_name="fiscal_watch_contract_deliveries",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_deliveries_status_next",
        table_name="fiscal_watch_contract_deliveries",
    )

    with op.batch_alter_table("fiscal_watch_contract_deliveries") as batch:
        batch.drop_constraint(
            "uq_fiscal_watch_contract_delivery_destination",
            type_="unique",
        )
        batch.drop_constraint(
            "ck_fiscal_watch_contract_delivery_channel",
            type_="check",
        )
        batch.drop_constraint(
            "ck_fiscal_watch_contract_delivery_status",
            type_="check",
        )
        batch.drop_constraint("fk_fiscal_watch_delivery_endpoint", type_="foreignkey")
        batch.drop_column("updated_at")
        batch.drop_column("payload")
        batch.drop_column("payload_sha256")
        batch.drop_column("last_error")
        batch.drop_column("response_body_excerpt")
        batch.drop_column("response_status")
        batch.drop_column("last_attempt_at")
        batch.drop_column("next_attempt_at")
        batch.drop_column("attempt_count")
        batch.drop_column("recipient_address")
        batch.drop_column("destination_key")
        batch.drop_column("endpoint_id")
        batch.create_check_constraint(
            "ck_fiscal_watch_contract_delivery_channel",
            "channel IN ('in_app')",
        )
        batch.create_check_constraint(
            "ck_fiscal_watch_contract_delivery_status",
            "status IN ('delivered', 'failed')",
        )
        batch.create_unique_constraint(
            "uq_fiscal_watch_contract_delivery_review_channel",
            ["review_id", "channel"],
        )
