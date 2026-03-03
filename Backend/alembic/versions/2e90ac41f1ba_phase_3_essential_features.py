"""phase_3_essential_features

Revision ID: 2e90ac41f1ba
Revises: 8383de60f631
Create Date: 2026-03-03 17:16:43.063050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '2e90ac41f1ba'
down_revision: Union[str, Sequence[str], None] = '8383de60f631'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Phase 3: Essential Missing Features.
    
    This migration adds:
    1. Audit fields (created_at, updated_at, created_by, updated_by, deleted_at) to all existing tables
    2. Role table for RBAC
    3. UserRole table for user-role assignments
    4. AuditLog table for audit trail
    5. NotificationPreference table for user notification settings
    6. All necessary indexes and constraints
    """
    
    # Create Role table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    
    # Create UserRole table
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', 'tenant_id', name='uq_user_role_tenant')
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    op.create_index(op.f('ix_user_roles_user_id'), 'user_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_roles_role_id'), 'user_roles', ['role_id'], unique=False)
    op.create_index(op.f('ix_user_roles_tenant_id'), 'user_roles', ['tenant_id'], unique=False)
    
    # Create AuditLog table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_tenant_created'), 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_table_record'), 'audit_logs', ['table_name', 'record_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    
    # Create NotificationPreference table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('delivery_method', sa.String(length=50), nullable=False, server_default='email'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'notification_type', name='uq_user_notification_type')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)
    
    # Add audit fields to existing tables
    tables_to_update = [
        'users', 'organizations', 'clients', 'products', 'bom_items',
        'orders', 'order_items', 'order_evaluations', 'scenarios',
        'ledgers', 'integration_syncs', 'financial_statements',
        'financial_ratios', 'chat_messages'
    ]
    
    for table_name in tables_to_update:
        # Use batch mode for SQLite compatibility
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            # Add created_by and updated_by columns (nullable for existing records)
            batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('updated_by', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
            
            # Add foreign key constraints for created_by and updated_by
            batch_op.create_foreign_key(
                f'fk_{table_name}_created_by',
                'users',
                ['created_by'], ['id'],
                ondelete='SET NULL'
            )
            batch_op.create_foreign_key(
                f'fk_{table_name}_updated_by',
                'users',
                ['updated_by'], ['id'],
                ondelete='SET NULL'
            )
            
            # Add updated_at column if it doesn't exist (some tables already have created_at)
            # Check if the table already has these columns
            if table_name not in ['users', 'organizations', 'clients', 'products', 'orders', 
                                   'order_evaluations', 'scenarios', 'ledgers', 'financial_statements',
                                   'financial_ratios', 'chat_messages']:
                batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, 
                                                    server_default=sa.text('CURRENT_TIMESTAMP')))
            
            if table_name not in ['financial_statements']:
                batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False,
                                                    server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Add indexes for performance (Requirements 18.1-18.8)
    
    # 18.1: Indexes on all foreign key columns
    op.create_index(op.f('ix_clients_organization_id'), 'clients', ['organization_id'], unique=False)
    op.create_index(op.f('ix_products_client_id'), 'products', ['client_id'], unique=False)
    op.create_index(op.f('ix_bom_items_product_id'), 'bom_items', ['product_id'], unique=False)
    op.create_index(op.f('ix_orders_client_id'), 'orders', ['client_id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_product_id'), 'order_items', ['product_id'], unique=False)
    op.create_index(op.f('ix_ledgers_client_id'), 'ledgers', ['client_id'], unique=False)
    op.create_index(op.f('ix_order_evaluations_order_id'), 'order_evaluations', ['order_id'], unique=False)
    op.create_index(op.f('ix_scenarios_client_id'), 'scenarios', ['client_id'], unique=False)
    op.create_index(op.f('ix_integration_syncs_client_id'), 'integration_syncs', ['client_id'], unique=False)
    op.create_index(op.f('ix_financial_statements_client_id'), 'financial_statements', ['client_id'], unique=False)
    op.create_index(op.f('ix_financial_ratios_client_id'), 'financial_ratios', ['client_id'], unique=False)
    op.create_index(op.f('ix_financial_ratios_statement_id'), 'financial_ratios', ['statement_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_client_id'), 'chat_messages', ['client_id'], unique=False)
    
    # 18.2: Composite index on (tenant_id, created_at) for all tenant-scoped tables
    # Note: Using organization_id as tenant_id for clients table, client_id for others
    op.create_index(op.f('ix_clients_org_created'), 'clients', ['organization_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_products_client_created'), 'products', ['client_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_orders_client_created'), 'orders', ['client_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_ledgers_client_created'), 'ledgers', ['client_id', 'transaction_date'], unique=False)
    op.create_index(op.f('ix_scenarios_client_created'), 'scenarios', ['client_id', 'created_at'], unique=False)
    
    # 18.3: Index on User.email (already exists in model definition)
    
    # 18.4: Index on Order.order_date for date range queries
    op.create_index(op.f('ix_orders_order_date'), 'orders', ['order_date'], unique=False)
    
    # 18.5: Index on Product.sku - Note: sku column doesn't exist in current schema
    # This would require adding the sku column first, which is out of scope for this task
    # Commenting out for now: op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=False)
    
    # 18.6: Composite index on (tenant_id, status) for filtered list queries
    op.create_index(op.f('ix_orders_client_status'), 'orders', ['client_id', 'status'], unique=False)
    op.create_index(op.f('ix_products_client_active'), 'products', ['client_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_ledgers_client_status'), 'ledgers', ['client_id', 'status'], unique=False)
    
    # 18.7: Index on Invoice.due_date (using Ledger.due_date as invoice equivalent)
    op.create_index(op.f('ix_ledgers_due_date'), 'ledgers', ['due_date'], unique=False)
    op.create_index(op.f('ix_orders_due_date'), 'orders', ['due_date'], unique=False)
    
    # Additional composite indexes for overdue receivables queries
    op.create_index(op.f('ix_ledgers_type_status_due'), 'ledgers', ['ledger_type', 'status', 'due_date'], unique=False)
    
    # Populate predefined roles
    op.execute("""
        INSERT INTO roles (name, description, permissions) VALUES
        ('Owner', 'Full system access including billing operations', 
         '{"all": true, "billing": true, "user_management": true, "integrations": true, "reports": true, "audit_logs": true}'),
        ('Admin', 'All access except billing operations',
         '{"all": true, "billing": false, "user_management": true, "integrations": true, "reports": true, "audit_logs": true}'),
        ('Accountant', 'Access to financial data and reports',
         '{"financial_data": true, "reports": true, "costing": true, "orders": true, "billing": false, "user_management": false}'),
        ('Viewer', 'Read-only access to all data',
         '{"read_only": true, "write": false, "delete": false, "billing": false, "user_management": false}')
    """)
    
    # Assign Owner role to existing users (first user in each organization)
    # SQLite-compatible version without DISTINCT ON
    op.execute("""
        INSERT INTO user_roles (user_id, role_id, tenant_id, assigned_at)
        SELECT 
            u.id, 
            r.id, 
            u.organization_id,
            CURRENT_TIMESTAMP
        FROM users u
        CROSS JOIN roles r
        WHERE r.name = 'Owner'
        AND u.organization_id IS NOT NULL
        AND u.id IN (
            SELECT MIN(id)
            FROM users
            WHERE organization_id IS NOT NULL
            GROUP BY organization_id
        )
    """)
    
    # Create default notification preferences for existing users
    # Initialize all notification types as enabled by default
    notification_types = [
        'order_evaluation_complete',
        'scenario_analysis_ready',
        'sync_status',
        'low_margin_alert',
        'overdue_receivables'
    ]
    
    for notification_type in notification_types:
        op.execute(f"""
            INSERT INTO notification_preferences (user_id, notification_type, enabled, delivery_method)
            SELECT 
                id,
                '{notification_type}',
                true,
                'email'
            FROM users
            WHERE id NOT IN (
                SELECT user_id 
                FROM notification_preferences 
                WHERE notification_type = '{notification_type}'
            )
        """)
    
    # Add database integrity constraints (Requirements 19.1-19.8)
    
    # 19.1: CHECK constraints for non-negative cost fields
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_products_raw_material_cost_non_negative',
            'raw_material_cost >= 0'
        )
        batch_op.create_check_constraint(
            'ck_products_labour_cost_non_negative',
            'labour_cost_per_unit >= 0'
        )
    
    with op.batch_alter_table('bom_items', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_bom_items_unit_cost_non_negative',
            'unit_cost >= 0'
        )
    
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_orders_total_cost_non_negative',
            'total_cost >= 0'
        )
        batch_op.create_check_constraint(
            'ck_orders_total_selling_price_non_negative',
            'total_selling_price >= 0'
        )
        batch_op.create_check_constraint(
            'ck_orders_amount_paid_non_negative',
            'amount_paid >= 0'
        )
        batch_op.create_check_constraint(
            'ck_orders_working_capital_blocked_non_negative',
            'working_capital_blocked >= 0'
        )
    
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_order_items_unit_cost_non_negative',
            'unit_cost IS NULL OR unit_cost >= 0'
        )
        batch_op.create_check_constraint(
            'ck_order_items_unit_selling_price_non_negative',
            'unit_selling_price IS NULL OR unit_selling_price >= 0'
        )
        batch_op.create_check_constraint(
            'ck_order_items_total_cost_non_negative',
            'total_cost IS NULL OR total_cost >= 0'
        )
        batch_op.create_check_constraint(
            'ck_order_items_total_selling_price_non_negative',
            'total_selling_price IS NULL OR total_selling_price >= 0'
        )
    
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_clients_annual_revenue_non_negative',
            'annual_revenue IS NULL OR annual_revenue >= 0'
        )
        batch_op.create_check_constraint(
            'ck_clients_current_debtors_non_negative',
            'current_debtors IS NULL OR current_debtors >= 0'
        )
    
    with op.batch_alter_table('ledgers', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_ledgers_amount_non_negative',
            'amount >= 0'
        )
    
    # 19.2: CHECK constraints for positive quantity fields
    with op.batch_alter_table('bom_items', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_bom_items_quantity_positive',
            'quantity > 0'
        )
    
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_order_items_quantity_positive',
            'quantity > 0'
        )
    
    # 19.3: CHECK constraints for percentage fields (0-100 range)
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_products_overhead_percentage_range',
            'overhead_percentage >= 0 AND overhead_percentage <= 100'
        )
        batch_op.create_check_constraint(
            'ck_products_target_margin_percentage_range',
            'target_margin_percentage >= 0 AND target_margin_percentage <= 100'
        )
        batch_op.create_check_constraint(
            'ck_products_tax_rate_range',
            'tax_rate >= 0 AND tax_rate <= 100'
        )
    
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_orders_margin_percentage_range',
            'margin_percentage >= 0 AND margin_percentage <= 100'
        )
    
    with op.batch_alter_table('order_evaluations', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_order_evaluations_profitability_score_range',
            'profitability_score IS NULL OR (profitability_score >= 0 AND profitability_score <= 100)'
        )
    
    with op.batch_alter_table('financial_statements', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_financial_statements_gross_margin_range',
            'gross_margin IS NULL OR (gross_margin >= 0 AND gross_margin <= 100)'
        )
        batch_op.create_check_constraint(
            'ck_financial_statements_net_margin_range',
            'net_margin IS NULL OR (net_margin >= 0 AND net_margin <= 100)'
        )
    
    # 19.4: CHECK constraints for date ranges (end_date >= start_date)
    with op.batch_alter_table('financial_statements', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_financial_statements_period_dates',
            'period_end >= period_start'
        )
    
    # 19.5: NOT NULL constraints to required fields (already enforced in model definitions)
    # The models already have nullable=False for required fields, so no additional changes needed
    
    # 19.7: CHECK constraint for email format validation
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_users_email_format',
            "email LIKE '%@%.%'"
        )
    
    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_organizations_email_format',
            "email IS NULL OR email LIKE '%@%.%'"
        )
    
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_clients_email_format',
            "email IS NULL OR email LIKE '%@%.%'"
        )
    
    # Additional CHECK constraints for credit days to be positive
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_clients_average_credit_days_positive',
            'average_credit_days > 0'
        )
    
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_orders_credit_days_positive',
            'credit_days > 0'
        )


def downgrade() -> None:
    """Downgrade schema - remove Phase 3 changes."""
    
    # Remove CHECK constraints (in reverse order of creation)
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('ck_orders_credit_days_positive', type_='check')
    
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.drop_constraint('ck_clients_average_credit_days_positive', type_='check')
        batch_op.drop_constraint('ck_clients_email_format', type_='check')
    
    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.drop_constraint('ck_organizations_email_format', type_='check')
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('ck_users_email_format', type_='check')
    
    with op.batch_alter_table('financial_statements', schema=None) as batch_op:
        batch_op.drop_constraint('ck_financial_statements_period_dates', type_='check')
        batch_op.drop_constraint('ck_financial_statements_net_margin_range', type_='check')
        batch_op.drop_constraint('ck_financial_statements_gross_margin_range', type_='check')
    
    with op.batch_alter_table('order_evaluations', schema=None) as batch_op:
        batch_op.drop_constraint('ck_order_evaluations_profitability_score_range', type_='check')
    
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('ck_orders_margin_percentage_range', type_='check')
    
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('ck_products_tax_rate_range', type_='check')
        batch_op.drop_constraint('ck_products_target_margin_percentage_range', type_='check')
        batch_op.drop_constraint('ck_products_overhead_percentage_range', type_='check')
    
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_constraint('ck_order_items_quantity_positive', type_='check')
    
    with op.batch_alter_table('bom_items', schema=None) as batch_op:
        batch_op.drop_constraint('ck_bom_items_quantity_positive', type_='check')
    
    with op.batch_alter_table('ledgers', schema=None) as batch_op:
        batch_op.drop_constraint('ck_ledgers_amount_non_negative', type_='check')
    
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.drop_constraint('ck_clients_current_debtors_non_negative', type_='check')
        batch_op.drop_constraint('ck_clients_annual_revenue_non_negative', type_='check')
    
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_constraint('ck_order_items_total_selling_price_non_negative', type_='check')
        batch_op.drop_constraint('ck_order_items_total_cost_non_negative', type_='check')
        batch_op.drop_constraint('ck_order_items_unit_selling_price_non_negative', type_='check')
        batch_op.drop_constraint('ck_order_items_unit_cost_non_negative', type_='check')
    
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('ck_orders_working_capital_blocked_non_negative', type_='check')
        batch_op.drop_constraint('ck_orders_amount_paid_non_negative', type_='check')
        batch_op.drop_constraint('ck_orders_total_selling_price_non_negative', type_='check')
        batch_op.drop_constraint('ck_orders_total_cost_non_negative', type_='check')
    
    with op.batch_alter_table('bom_items', schema=None) as batch_op:
        batch_op.drop_constraint('ck_bom_items_unit_cost_non_negative', type_='check')
    
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('ck_products_labour_cost_non_negative', type_='check')
        batch_op.drop_constraint('ck_products_raw_material_cost_non_negative', type_='check')
    
    # Remove audit fields from existing tables
    tables_to_update = [
        'users', 'organizations', 'clients', 'products', 'bom_items',
        'orders', 'order_items', 'order_evaluations', 'scenarios',
        'ledgers', 'integration_syncs', 'financial_statements',
        'financial_ratios', 'chat_messages'
    ]
    
    for table_name in tables_to_update:
        # Use batch mode for SQLite compatibility
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            # Drop foreign key constraints first
            batch_op.drop_constraint(f'fk_{table_name}_created_by', type_='foreignkey')
            batch_op.drop_constraint(f'fk_{table_name}_updated_by', type_='foreignkey')
            
            # Drop columns
            batch_op.drop_column('deleted_at')
            batch_op.drop_column('updated_by')
            batch_op.drop_column('created_by')
            
            # Drop updated_at if it was added (not for tables that already had it)
            if table_name not in ['financial_statements']:
                try:
                    batch_op.drop_column('updated_at')
                except:
                    pass  # Column might not have been added
            
            # Drop created_at if it was added
            if table_name not in ['users', 'organizations', 'clients', 'products', 'orders', 
                                   'order_evaluations', 'scenarios', 'ledgers', 'financial_statements',
                                   'financial_ratios', 'chat_messages']:
                try:
                    batch_op.drop_column('created_at')
                except:
                    pass  # Column might not have been added
    
    # Drop indexes (in reverse order of creation)
    op.drop_index(op.f('ix_ledgers_type_status_due'), table_name='ledgers')
    op.drop_index(op.f('ix_orders_due_date'), table_name='orders')
    op.drop_index(op.f('ix_ledgers_due_date'), table_name='ledgers')
    op.drop_index(op.f('ix_ledgers_client_status'), table_name='ledgers')
    op.drop_index(op.f('ix_products_client_active'), table_name='products')
    op.drop_index(op.f('ix_orders_client_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_date'), table_name='orders')
    op.drop_index(op.f('ix_scenarios_client_created'), table_name='scenarios')
    op.drop_index(op.f('ix_ledgers_client_created'), table_name='ledgers')
    op.drop_index(op.f('ix_orders_client_created'), table_name='orders')
    op.drop_index(op.f('ix_products_client_created'), table_name='products')
    op.drop_index(op.f('ix_clients_org_created'), table_name='clients')
    op.drop_index(op.f('ix_chat_messages_client_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_financial_ratios_statement_id'), table_name='financial_ratios')
    op.drop_index(op.f('ix_financial_ratios_client_id'), table_name='financial_ratios')
    op.drop_index(op.f('ix_financial_statements_client_id'), table_name='financial_statements')
    op.drop_index(op.f('ix_integration_syncs_client_id'), table_name='integration_syncs')
    op.drop_index(op.f('ix_scenarios_client_id'), table_name='scenarios')
    op.drop_index(op.f('ix_order_evaluations_order_id'), table_name='order_evaluations')
    op.drop_index(op.f('ix_ledgers_client_id'), table_name='ledgers')
    op.drop_index(op.f('ix_order_items_product_id'), table_name='order_items')
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_index(op.f('ix_orders_client_id'), table_name='orders')
    op.drop_index(op.f('ix_bom_items_product_id'), table_name='bom_items')
    op.drop_index(op.f('ix_products_client_id'), table_name='products')
    op.drop_index(op.f('ix_clients_organization_id'), table_name='clients')
    
    # Drop new tables
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
    
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_table_record'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_tenant_created'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index(op.f('ix_user_roles_tenant_id'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_role_id'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_user_id'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_id'), table_name='user_roles')
    op.drop_table('user_roles')
    
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')
