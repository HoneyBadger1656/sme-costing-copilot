"""phase4_gst_payments

Revision ID: a1b2c3d4e5f6
Revises: 2e90ac41f1ba
Create Date: 2026-03-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2e90ac41f1ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Phase 4: GST Compliance, E-Invoicing, E-Way Bills & Payments.

    Creates 10 new tables and adds columns to products and orders.
    """

    # 1. hsn_sac_master
    op.create_table(
        'hsn_sac_master',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=8), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=3), nullable=False),
        sa.Column('cgst_rate', sa.Float(), nullable=True, server_default='0'),
        sa.Column('sgst_rate', sa.Float(), nullable=True, server_default='0'),
        sa.Column('igst_rate', sa.Float(), nullable=True, server_default='0'),
        sa.Column('cess_rate', sa.Float(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_hsn_sac_master_id'), 'hsn_sac_master', ['id'], unique=False)
    op.create_index(op.f('ix_hsn_sac_master_code'), 'hsn_sac_master', ['code'], unique=True)

    # 2. gst_configurations
    op.create_table(
        'gst_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('trade_name', sa.String(length=255), nullable=True),
        sa.Column('state_code', sa.String(length=2), nullable=False),
        sa.Column('filing_frequency', sa.String(length=20), nullable=True, server_default='monthly'),
        sa.Column('registration_type', sa.String(length=50), nullable=True, server_default='regular'),
        sa.Column('gsp_username', sa.String(length=255), nullable=True),
        sa.Column('gsp_api_key', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gst_configurations_id'), 'gst_configurations', ['id'], unique=False)
    op.create_index(op.f('ix_gst_configurations_client_id'), 'gst_configurations', ['client_id'], unique=False)
    op.create_index(op.f('ix_gst_configurations_organization_id'), 'gst_configurations', ['organization_id'], unique=False)

    # 3. gst_returns
    op.create_table(
        'gst_returns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('return_type', sa.String(length=10), nullable=False),
        sa.Column('period', sa.String(length=6), nullable=False),
        sa.Column('filing_status', sa.String(length=20), nullable=True, server_default='draft'),
        sa.Column('return_data', sa.JSON(), nullable=True),
        sa.Column('arn', sa.String(length=50), nullable=True),
        sa.Column('filed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gst_returns_id'), 'gst_returns', ['id'], unique=False)
    op.create_index(op.f('ix_gst_returns_client_period'), 'gst_returns', ['client_id', 'period'], unique=False)
    op.create_index(op.f('ix_gst_returns_organization_id'), 'gst_returns', ['organization_id'], unique=False)

    # 4. gst_reconciliation
    op.create_table(
        'gst_reconciliation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('period', sa.String(length=6), nullable=False),
        sa.Column('source', sa.String(length=2), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('reconciliation_result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gst_reconciliation_id'), 'gst_reconciliation', ['id'], unique=False)
    op.create_index(op.f('ix_gst_reconciliation_client_period'), 'gst_reconciliation', ['client_id', 'period'], unique=False)

    # 5. einvoices
    op.create_table(
        'einvoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('irn', sa.String(length=64), nullable=True),
        sa.Column('ack_no', sa.String(length=50), nullable=True),
        sa.Column('ack_date', sa.DateTime(), nullable=True),
        sa.Column('signed_qr_code', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index(op.f('ix_einvoices_id'), 'einvoices', ['id'], unique=False)
    op.create_index(op.f('ix_einvoices_order_id'), 'einvoices', ['order_id'], unique=True)
    op.create_index(op.f('ix_einvoices_organization_id'), 'einvoices', ['organization_id'], unique=False)

    # 6. ewaybills
    op.create_table(
        'ewaybills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('ewb_number', sa.String(length=50), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('transporter_gstin', sa.String(length=15), nullable=True),
        sa.Column('vehicle_number', sa.String(length=20), nullable=True),
        sa.Column('transport_mode', sa.String(length=10), nullable=True),
        sa.Column('distance_km', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ewaybills_id'), 'ewaybills', ['id'], unique=False)
    op.create_index(op.f('ix_ewaybills_order_id'), 'ewaybills', ['order_id'], unique=False)
    op.create_index(op.f('ix_ewaybills_valid_until'), 'ewaybills', ['valid_until'], unique=False)

    # 7. transporters
    op.create_table(
        'transporters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('vehicle_number', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transporters_id'), 'transporters', ['id'], unique=False)
    op.create_index(op.f('ix_transporters_organization_id'), 'transporters', ['organization_id'], unique=False)

    # 8. invoice_payment_links
    op.create_table(
        'invoice_payment_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('razorpay_link_id', sa.String(length=100), nullable=True),
        sa.Column('short_url', sa.String(length=500), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='created'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_payment_links_id'), 'invoice_payment_links', ['id'], unique=False)
    op.create_index(op.f('ix_invoice_payment_links_order_id'), 'invoice_payment_links', ['order_id'], unique=False)

    # 9. payment_reminders
    op.create_table(
        'payment_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('reminder_type', sa.String(length=10), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_reminders_id'), 'payment_reminders', ['id'], unique=False)
    op.create_index(op.f('ix_payment_reminders_order_id'), 'payment_reminders', ['order_id'], unique=False)
    op.create_index(op.f('ix_payment_reminders_scheduled_at'), 'payment_reminders', ['scheduled_at'], unique=False)

    # 10. credit_limits
    op.create_table(
        'credit_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('limit_amount', sa.Float(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index(op.f('ix_credit_limits_id'), 'credit_limits', ['id'], unique=False)
    op.create_index(op.f('ix_credit_limits_client_id'), 'credit_limits', ['client_id'], unique=True)
    op.create_index(op.f('ix_credit_limits_organization_id'), 'credit_limits', ['organization_id'], unique=False)

    # Add hsn_sac_id to products
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hsn_sac_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_products_hsn_sac_id',
            'hsn_sac_master',
            ['hsn_sac_id'], ['id']
        )

    # Add organization_id to orders
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(
            'fk_orders_organization_id',
            'organizations',
            ['organization_id'], ['id']
        )


def downgrade() -> None:
    """Remove Phase 4 changes."""

    # Remove columns from existing tables
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_orders_organization_id', type_='foreignkey')
        batch_op.drop_column('organization_id')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('fk_products_hsn_sac_id', type_='foreignkey')
        batch_op.drop_column('hsn_sac_id')

    # Drop new tables (reverse dependency order)
    op.drop_index(op.f('ix_credit_limits_organization_id'), table_name='credit_limits')
    op.drop_index(op.f('ix_credit_limits_client_id'), table_name='credit_limits')
    op.drop_index(op.f('ix_credit_limits_id'), table_name='credit_limits')
    op.drop_table('credit_limits')

    op.drop_index(op.f('ix_payment_reminders_scheduled_at'), table_name='payment_reminders')
    op.drop_index(op.f('ix_payment_reminders_order_id'), table_name='payment_reminders')
    op.drop_index(op.f('ix_payment_reminders_id'), table_name='payment_reminders')
    op.drop_table('payment_reminders')

    op.drop_index(op.f('ix_invoice_payment_links_order_id'), table_name='invoice_payment_links')
    op.drop_index(op.f('ix_invoice_payment_links_id'), table_name='invoice_payment_links')
    op.drop_table('invoice_payment_links')

    op.drop_index(op.f('ix_transporters_organization_id'), table_name='transporters')
    op.drop_index(op.f('ix_transporters_id'), table_name='transporters')
    op.drop_table('transporters')

    op.drop_index(op.f('ix_ewaybills_valid_until'), table_name='ewaybills')
    op.drop_index(op.f('ix_ewaybills_order_id'), table_name='ewaybills')
    op.drop_index(op.f('ix_ewaybills_id'), table_name='ewaybills')
    op.drop_table('ewaybills')

    op.drop_index(op.f('ix_einvoices_organization_id'), table_name='einvoices')
    op.drop_index(op.f('ix_einvoices_order_id'), table_name='einvoices')
    op.drop_index(op.f('ix_einvoices_id'), table_name='einvoices')
    op.drop_table('einvoices')

    op.drop_index(op.f('ix_gst_reconciliation_client_period'), table_name='gst_reconciliation')
    op.drop_index(op.f('ix_gst_reconciliation_id'), table_name='gst_reconciliation')
    op.drop_table('gst_reconciliation')

    op.drop_index(op.f('ix_gst_returns_organization_id'), table_name='gst_returns')
    op.drop_index(op.f('ix_gst_returns_client_period'), table_name='gst_returns')
    op.drop_index(op.f('ix_gst_returns_id'), table_name='gst_returns')
    op.drop_table('gst_returns')

    op.drop_index(op.f('ix_gst_configurations_organization_id'), table_name='gst_configurations')
    op.drop_index(op.f('ix_gst_configurations_client_id'), table_name='gst_configurations')
    op.drop_index(op.f('ix_gst_configurations_id'), table_name='gst_configurations')
    op.drop_table('gst_configurations')

    op.drop_index(op.f('ix_hsn_sac_master_code'), table_name='hsn_sac_master')
    op.drop_index(op.f('ix_hsn_sac_master_id'), table_name='hsn_sac_master')
    op.drop_table('hsn_sac_master')
