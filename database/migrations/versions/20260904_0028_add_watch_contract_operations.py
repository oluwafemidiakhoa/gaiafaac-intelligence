"""Add Watch Contract operational reviews and in-app deliveries.

Revision ID: 20260904_0028
Revises: 20260904_0027
"""

from alembic import op
import sqlalchemy as sa

revision = "20260904_0028"
down_revision = "20260904_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("fiscal_watch_contracts") as batch:
        batch.add_column(
            sa.Column(
                "escalation_after_minutes",
                sa.Integer(),
                nullable=False,
                server_default="1440",
            )
        )
        batch.create_check_constraint(
            "ck_fiscal_watch_contract_escalation_window",
            "escalation_after_minutes >= 15 AND escalation_after_minutes <= 10080",
        )

    op.create_table(
        "fiscal_watch_contract_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_user_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("resolution_note", sa.String(length=5000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved')",
            name="ck_fiscal_watch_contract_review_status",
        ),
        sa.ForeignKeyConstraint(["match_id"], ["fiscal_watch_contract_matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contract_id"], ["fiscal_watch_contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["evidence_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["acknowledged_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("match_id", name="uq_fiscal_watch_contract_review_match"),
    )
    op.create_index(
        "ix_fiscal_watch_contract_reviews_org_status_due",
        "fiscal_watch_contract_reviews",
        ["organization_id", "status", "due_at"],
    )
    op.create_index(
        "ix_fiscal_watch_contract_reviews_contract_created",
        "fiscal_watch_contract_reviews",
        ["contract_id", "created_at"],
    )

    op.create_table(
        "fiscal_watch_contract_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=True),
        sa.Column("channel", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("channel IN ('in_app')", name="ck_fiscal_watch_contract_delivery_channel"),
        sa.CheckConstraint("status IN ('delivered', 'failed')", name="ck_fiscal_watch_contract_delivery_status"),
        sa.ForeignKeyConstraint(["review_id"], ["fiscal_watch_contract_reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_id"], ["fiscal_watch_contract_matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contract_id"], ["fiscal_watch_contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "review_id",
            "channel",
            name="uq_fiscal_watch_contract_delivery_review_channel",
        ),
    )
    op.create_index(
        "ix_fiscal_watch_contract_deliveries_org_created",
        "fiscal_watch_contract_deliveries",
        ["organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fiscal_watch_contract_deliveries_org_created",
        table_name="fiscal_watch_contract_deliveries",
    )
    op.drop_table("fiscal_watch_contract_deliveries")

    op.drop_index(
        "ix_fiscal_watch_contract_reviews_contract_created",
        table_name="fiscal_watch_contract_reviews",
    )
    op.drop_index(
        "ix_fiscal_watch_contract_reviews_org_status_due",
        table_name="fiscal_watch_contract_reviews",
    )
    op.drop_table("fiscal_watch_contract_reviews")

    with op.batch_alter_table("fiscal_watch_contracts") as batch:
        batch.drop_constraint(
            "ck_fiscal_watch_contract_escalation_window",
            type_="check",
        )
        batch.drop_column("escalation_after_minutes")
