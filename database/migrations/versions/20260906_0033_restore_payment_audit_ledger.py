"""Restore the payment audit ledger for clean canonical production databases.

Revision ID: 20260906_0033
Revises: 20260904_0032

Some canonical migration histories never contained the older billing-generation
``payment_records`` table, while the current Paystack subscription billing and
billing-history routes still use the payment audit ledger. Create the ledger
only when it is absent. The deprecated legacy subscription relation is kept as
a nullable UUID column without a foreign key so clean canonical databases do
not need the retired ``organization_subscriptions`` table.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20260906_0033"
down_revision = "20260904_0032"
branch_labels = None
depends_on = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return _inspector().has_table(name)


def _has_legacy_subscription_fk() -> bool:
    """Return True when payment_records predates this canonical fallback migration."""

    if not _has_table("payment_records"):
        return False
    for foreign_key in _inspector().get_foreign_keys("payment_records"):
        if "subscription_id" in (foreign_key.get("constrained_columns") or []):
            return True
    return False


def _payment_record_count() -> int:
    result = op.get_bind().execute(sa.text("SELECT COUNT(*) FROM payment_records"))
    return int(result.scalar_one())


def upgrade() -> None:
    if _has_table("payment_records"):
        return

    op.create_table(
        "payment_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subscription_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("canonical_subscription_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("paystack_transaction_id", sa.String(length=100), nullable=True),
        sa.Column("amount_naira", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("invoice_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_payment_records_organization",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_subscription_id"],
            ["subscriptions.id"],
            name="fk_payment_records_canonical_subscription",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paystack_transaction_id"),
        sa.UniqueConstraint("invoice_number"),
    )
    op.create_index(
        "ix_payment_records_organization_id",
        "payment_records",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_records_org_created",
        "payment_records",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_records_status_created",
        "payment_records",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payment_records_canonical_subscription",
        "payment_records",
        ["canonical_subscription_id"],
        unique=False,
    )


def downgrade() -> None:
    if not _has_table("payment_records"):
        return

    # A legacy ledger has a real FK from subscription_id to the retired
    # organization_subscriptions table. It existed before this migration, so
    # leave it in place and let migration 0030 remove only the canonical link.
    if _has_legacy_subscription_fk():
        return

    # A ledger without that legacy FK is the clean-canonical fallback created
    # here. Empty fallback tables can be removed for migration round-trips. Once
    # payment evidence exists, refuse a destructive downgrade rather than erase
    # an audit record automatically.
    if _payment_record_count() > 0:
        raise RuntimeError(
            "Refusing to downgrade 20260906_0033 because payment_records contains "
            "payment evidence. Preserve or explicitly migrate the ledger first."
        )

    op.drop_table("payment_records")
