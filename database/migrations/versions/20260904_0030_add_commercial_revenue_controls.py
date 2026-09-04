"""Add commercial CRM stages, first-party events, and canonical payment linkage.

Revision ID: 20260904_0030
Revises: 20260904_0029
"""

from alembic import op
import sqlalchemy as sa

revision = "20260904_0030"
down_revision = "20260904_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("pilot_leads") as batch:
        batch.add_column(sa.Column("owner_name", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("next_action", sa.String(length=500), nullable=True))
        batch.add_column(sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("closed_reason", sa.String(length=1000), nullable=True))
        batch.add_column(sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("converted_organization_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_pilot_leads_converted_organization",
            "organizations",
            ["converted_organization_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_pilot_leads_next_action",
        "pilot_leads",
        ["status", "next_action_at"],
    )
    op.create_index(
        "ix_pilot_leads_converted_organization_id",
        "pilot_leads",
        ["converted_organization_id"],
    )

    op.create_table(
        "commercial_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_name", sa.String(length=80), nullable=False),
        sa.Column("subject_type", sa.String(length=80), nullable=True),
        sa.Column("subject_id", sa.String(length=160), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="server"),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_commercial_events_organization_id", "commercial_events", ["organization_id"]
    )
    op.create_index("ix_commercial_events_user_id", "commercial_events", ["user_id"])
    op.create_index(
        "ix_commercial_events_name_occurred",
        "commercial_events",
        ["event_name", "occurred_at"],
    )
    op.create_index(
        "ix_commercial_events_org_occurred",
        "commercial_events",
        ["organization_id", "occurred_at"],
    )
    op.create_index(
        "ix_commercial_events_subject",
        "commercial_events",
        ["subject_type", "subject_id"],
    )

    with op.batch_alter_table("payment_records") as batch:
        batch.add_column(sa.Column("canonical_subscription_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_payment_records_canonical_subscription",
            "subscriptions",
            ["canonical_subscription_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_payment_records_canonical_subscription",
        "payment_records",
        ["canonical_subscription_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_records_canonical_subscription", table_name="payment_records"
    )
    with op.batch_alter_table("payment_records") as batch:
        batch.drop_constraint(
            "fk_payment_records_canonical_subscription", type_="foreignkey"
        )
        batch.drop_column("canonical_subscription_id")

    op.drop_index("ix_commercial_events_subject", table_name="commercial_events")
    op.drop_index("ix_commercial_events_org_occurred", table_name="commercial_events")
    op.drop_index("ix_commercial_events_name_occurred", table_name="commercial_events")
    op.drop_index("ix_commercial_events_user_id", table_name="commercial_events")
    op.drop_index("ix_commercial_events_organization_id", table_name="commercial_events")
    op.drop_table("commercial_events")

    op.drop_index(
        "ix_pilot_leads_converted_organization_id", table_name="pilot_leads"
    )
    op.drop_index("ix_pilot_leads_next_action", table_name="pilot_leads")
    with op.batch_alter_table("pilot_leads") as batch:
        batch.drop_constraint(
            "fk_pilot_leads_converted_organization", type_="foreignkey"
        )
        batch.drop_column("converted_organization_id")
        batch.drop_column("status_changed_at")
        batch.drop_column("closed_reason")
        batch.drop_column("next_action_at")
        batch.drop_column("next_action")
        batch.drop_column("owner_name")
