"""Add subscription tier, billing and payment models

Revision ID: 0001_add_subscription_models
Revises:
Create Date: 2026-09-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_add_subscription_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscription_tiers table
    op.create_table(
        'subscription_tiers',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('price_naira', sa.Integer(), nullable=False),
        sa.Column('requests_per_month', sa.Integer(), nullable=False),
        sa.Column('exports_per_month', sa.Integer(), nullable=False),
        sa.Column('features', sa.String(500), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_subscription_tiers_name')
    )

    # Create organization_subscriptions table
    op.create_table(
        'organization_subscriptions',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('organization_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('tier_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('tier_name', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('paystack_subscription_id', sa.String(100), nullable=True),
        sa.Column('paystack_authorization_code', sa.String(200), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('renewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('api_requests_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exports_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reset_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tier_id'], ['subscription_tiers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', name='uq_organization_subscriptions_org')
    )
    op.create_index('ix_organization_subscriptions_org_expires', 'organization_subscriptions', ['organization_id', 'expires_at'])

    # Create payment_records table
    op.create_table(
        'payment_records',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('organization_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('subscription_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('paystack_transaction_id', sa.String(100), nullable=True),
        sa.Column('amount_naira', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=True),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['organization_subscriptions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paystack_transaction_id', name='uq_payment_records_paystack_id'),
        sa.UniqueConstraint('invoice_number', name='uq_payment_records_invoice_number')
    )
    op.create_index('ix_payment_records_org_created', 'payment_records', ['organization_id', 'created_at'])
    op.create_index('ix_payment_records_status_created', 'payment_records', ['status', 'created_at'])

    # Insert default subscription tiers
    op.execute("""
        INSERT INTO subscription_tiers (id, name, price_naira, requests_per_month, exports_per_month, features, description, created_at)
        VALUES
            ('550e8400-e29b-41d4-a716-446655440001'::uuid, 'Free', 0, 10000, 0, 'public_search,basic_export', 'For explorers & researchers', now()),
            ('550e8400-e29b-41d4-a716-446655440002'::uuid, 'Professional', 50000, 100000, 5, 'watchlists,alerts,api_access,csv_export', 'For institutions & analysts', now()),
            ('550e8400-e29b-41d4-a716-446655440003'::uuid, 'Enterprise', 500000, 999999, 999, 'all,custom_reports,webhooks,sla,dedicated_support', 'For banks, governments, APIs', now())
    """)


def downgrade() -> None:
    op.drop_table('payment_records')
    op.drop_table('organization_subscriptions')
    op.drop_table('subscription_tiers')
