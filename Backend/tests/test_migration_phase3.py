"""
Tests for Phase 3 migration script (2e90ac41f1ba_phase_3_essential_features.py)

This test suite verifies:
- Migration script structure and content
- Migration can be imported without errors
- Migration has proper upgrade and downgrade functions
- Key migration operations are present in the script

Note: Full migration testing requires a real database environment.
For comprehensive migration testing, run: alembic upgrade head
"""

import pytest
from pathlib import Path
import importlib.util


class TestPhase3MigrationScript:
    """Test suite for Phase 3 migration script structure and content"""
    
    @pytest.fixture(scope="class")
    def migration_module(self):
        """Load the Phase 3 migration module"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        spec = importlib.util.spec_from_file_location("migration_module", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def test_migration_has_correct_metadata(self, migration_module):
        """Test that migration has correct revision identifiers"""
        assert migration_module.revision == '2e90ac41f1ba'
        assert migration_module.down_revision == '8383de60f631'
        assert migration_module.branch_labels is None
        assert migration_module.depends_on is None
    
    def test_migration_has_upgrade_function(self, migration_module):
        """Test that migration has an upgrade function"""
        assert hasattr(migration_module, 'upgrade')
        assert callable(migration_module.upgrade)
    
    def test_migration_has_downgrade_function(self, migration_module):
        """Test that migration has a downgrade function"""
        assert hasattr(migration_module, 'downgrade')
        assert callable(migration_module.downgrade)
    
    def test_migration_script_contains_role_table_creation(self):
        """Test that migration script creates roles table"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for roles table creation
        assert "create_table" in content and "'roles'" in content
        assert "'name'" in content or '"name"' in content
        assert "'permissions'" in content or '"permissions"' in content
        assert "sa.JSON()" in content
    
    def test_migration_script_contains_user_roles_table_creation(self):
        """Test that migration script creates user_roles table"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for user_roles table creation
        assert "create_table" in content and "'user_roles'" in content
        assert "'user_id'" in content or '"user_id"' in content
        assert "'role_id'" in content or '"role_id"' in content
        assert "'tenant_id'" in content or '"tenant_id"' in content
    
    def test_migration_script_contains_audit_log_table_creation(self):
        """Test that migration script creates audit_logs table"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for audit_logs table creation
        assert "create_table" in content and "'audit_logs'" in content
        assert "'action'" in content or '"action"' in content
        assert "'table_name'" in content or '"table_name"' in content
        assert "'old_values'" in content or '"old_values"' in content
        assert "'new_values'" in content or '"new_values"' in content
    
    def test_migration_script_contains_notification_preferences_table_creation(self):
        """Test that migration script creates notification_preferences table"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for notification_preferences table creation
        assert "create_table" in content and "'notification_preferences'" in content
        assert "'notification_type'" in content or '"notification_type"' in content
        assert "'enabled'" in content or '"enabled"' in content
    
    def test_migration_script_adds_audit_fields(self):
        """Test that migration script adds audit fields to existing tables"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for audit field additions
        assert "'created_by'" in content or '"created_by"' in content
        assert "'updated_by'" in content or '"updated_by"' in content
        assert "'deleted_at'" in content or '"deleted_at"' in content
    
    def test_migration_script_creates_indexes(self):
        """Test that migration script creates performance indexes"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for index creation
        assert "op.create_index" in content
        assert "ix_roles_id" in content
        assert "ix_user_roles" in content
        assert "ix_audit_logs" in content
        assert "ix_orders_order_date" in content
    
    def test_migration_script_creates_constraints(self):
        """Test that migration script creates CHECK constraints"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for constraint creation
        assert "create_check_constraint" in content
        assert "non_negative" in content or "positive" in content
        assert "email_format" in content
    
    def test_migration_script_populates_predefined_roles(self):
        """Test that migration script populates predefined roles"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for role population
        assert "INSERT INTO roles" in content
        assert "Owner" in content
        assert "Admin" in content
        assert "Accountant" in content
        assert "Viewer" in content
    
    def test_migration_script_assigns_owner_role(self):
        """Test that migration script assigns Owner role to existing users"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for owner role assignment
        assert "INSERT INTO user_roles" in content
        assert "Owner" in content or "'Owner'" in content
    
    def test_migration_script_creates_notification_preferences(self):
        """Test that migration script creates default notification preferences"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for notification preference creation
        assert "INSERT INTO notification_preferences" in content
        assert "order_evaluation_complete" in content
        assert "scenario_analysis_ready" in content
        assert "sync_status" in content
        assert "low_margin_alert" in content
        assert "overdue_receivables" in content
    
    def test_migration_downgrade_removes_tables(self):
        """Test that downgrade function removes Phase 3 tables"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Find downgrade function
        downgrade_start = content.find("def downgrade()")
        assert downgrade_start > 0
        
        downgrade_content = content[downgrade_start:]
        
        # Check for table drops in downgrade
        assert "op.drop_table('roles')" in downgrade_content or 'op.drop_table("roles")' in downgrade_content
        assert "op.drop_table('user_roles')" in downgrade_content or 'op.drop_table("user_roles")' in downgrade_content
        assert "op.drop_table('audit_logs')" in downgrade_content or 'op.drop_table("audit_logs")' in downgrade_content
        assert "op.drop_table('notification_preferences')" in downgrade_content or 'op.drop_table("notification_preferences")' in downgrade_content
    
    def test_migration_downgrade_removes_audit_fields(self):
        """Test that downgrade function removes audit fields"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Find downgrade function
        downgrade_start = content.find("def downgrade()")
        assert downgrade_start > 0
        
        downgrade_content = content[downgrade_start:]
        
        # Check for audit field drops in downgrade
        assert "drop_column" in downgrade_content
        assert "'created_by'" in downgrade_content or '"created_by"' in downgrade_content
        assert "'updated_by'" in downgrade_content or '"updated_by"' in downgrade_content
        assert "'deleted_at'" in downgrade_content or '"deleted_at"' in downgrade_content
    
    def test_migration_script_has_foreign_key_constraints(self):
        """Test that migration script creates foreign key constraints"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for foreign key constraints
        assert "sa.ForeignKeyConstraint" in content
        assert "['user_id'], ['users.id']" in content or '["user_id"], ["users.id"]' in content
        assert "['role_id'], ['roles.id']" in content or '["role_id"], ["roles.id"]' in content
    
    def test_migration_script_has_unique_constraints(self):
        """Test that migration script creates unique constraints"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for unique constraints
        assert "sa.UniqueConstraint" in content
        assert "uq_user_role_tenant" in content
        assert "uq_user_notification_type" in content


class TestMigrationDocumentation:
    """Test that migration is properly documented"""
    
    def test_migration_has_docstring(self):
        """Test that migration functions have docstrings"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for docstrings
        assert '"""Upgrade schema for Phase 3' in content or "'''Upgrade schema for Phase 3" in content
        assert '"""Downgrade schema' in content or "'''Downgrade schema" in content
    
    def test_migration_file_has_header_comment(self):
        """Test that migration file has proper header"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for header information
        assert "phase_3_essential_features" in content
        assert "Revision ID: 2e90ac41f1ba" in content
        assert "Revises: 8383de60f631" in content


class TestMigrationRequirementsCoverage:
    """Test that migration covers all requirements"""
    
    def test_migration_covers_requirement_1_rbac_tables(self):
        """Test migration creates RBAC tables (Req 1.1, 1.2)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "create_table" in content and "'roles'" in content
        assert "create_table" in content and "'user_roles'" in content
    
    def test_migration_covers_requirement_5_audit_log_table(self):
        """Test migration creates audit log table (Req 5.1-5.8)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "create_table" in content and "'audit_logs'" in content
        assert "'old_values'" in content
        assert "'new_values'" in content
        assert "sa.JSON()" in content
    
    def test_migration_covers_requirement_16_notification_preferences(self):
        """Test migration creates notification preferences table (Req 16.1)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "create_table" in content and "'notification_preferences'" in content
    
    def test_migration_covers_requirement_18_performance_indexes(self):
        """Test migration creates performance indexes (Req 18.1-18.8)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Check for various indexes mentioned in requirement 18
        assert "ix_orders_order_date" in content
        assert "ix_products_client_id" in content
        assert "ix_audit_logs_tenant_created" in content
    
    def test_migration_covers_requirement_19_integrity_constraints(self):
        """Test migration creates integrity constraints (Req 19.1-19.8)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "create_check_constraint" in content
        assert "non_negative" in content
        assert "positive" in content
        assert "email_format" in content
    
    def test_migration_covers_requirement_20_audit_fields(self):
        """Test migration adds audit fields (Req 20.1-20.5)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "'created_at'" in content
        assert "'updated_at'" in content
        assert "'created_by'" in content
        assert "'updated_by'" in content
        assert "'deleted_at'" in content
    
    def test_migration_covers_requirement_22_predefined_roles(self):
        """Test migration populates predefined roles (Req 22.5, 22.6)"""
        backend_path = Path(__file__).parent.parent
        migration_path = backend_path / "alembic" / "versions" / "2e90ac41f1ba_phase_3_essential_features.py"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "INSERT INTO roles" in content
        assert "Owner" in content
        assert "Admin" in content
        assert "Accountant" in content
        assert "Viewer" in content
        assert "INSERT INTO user_roles" in content
