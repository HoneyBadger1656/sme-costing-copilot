"""Tests for RBAC utility functions"""

import pytest
from app.models.models import User, Organization, Role, UserRole
from app.utils.rbac import get_user_roles, check_permission, check_role


@pytest.fixture
def test_roles(test_db):
    """Create test roles with different permission sets"""
    roles = {
        'Owner': Role(
            name='Owner',
            description='Full system access including billing',
            permissions={'all': True, 'billing': True}
        ),
        'Admin': Role(
            name='Admin',
            description='All access except billing',
            permissions={'all': True, 'billing': False}
        ),
        'Accountant': Role(
            name='Accountant',
            description='Financial data and reports access',
            permissions={'reports': True, 'financial_data': True, 'costing': True}
        ),
        'Viewer': Role(
            name='Viewer',
            description='Read-only access',
            permissions={'read_only': True}
        )
    }
    
    for role in roles.values():
        test_db.add(role)
    test_db.commit()
    
    for role in roles.values():
        test_db.refresh(role)
    
    return roles


class TestGetUserRoles:
    """Tests for get_user_roles function"""
    
    def test_get_user_roles_single_role(self, test_db, test_user, test_organization, test_roles):
        """Test getting a single role for a user"""
        # Assign Owner role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Get user roles
        roles = get_user_roles(test_db, test_user.id, test_organization.id)
        
        assert len(roles) == 1
        assert roles[0].name == 'Owner'
    
    def test_get_user_roles_multiple_roles(self, test_db, test_user, test_organization, test_roles):
        """Test getting multiple roles for a user"""
        # Assign multiple roles to user
        for role_name in ['Admin', 'Accountant']:
            user_role = UserRole(
                user_id=test_user.id,
                role_id=test_roles[role_name].id,
                tenant_id=test_organization.id,
                assigned_by=test_user.id
            )
            test_db.add(user_role)
        test_db.commit()
        
        # Get user roles
        roles = get_user_roles(test_db, test_user.id, test_organization.id)
        
        assert len(roles) == 2
        role_names = {role.name for role in roles}
        assert role_names == {'Admin', 'Accountant'}
    
    def test_get_user_roles_no_roles(self, test_db, test_user, test_organization):
        """Test getting roles for a user with no role assignments"""
        roles = get_user_roles(test_db, test_user.id, test_organization.id)
        
        assert len(roles) == 0
    
    def test_get_user_roles_different_tenant(self, test_db, test_user, test_organization, test_roles):
        """Test that roles are isolated by tenant"""
        # Create another organization
        other_org = Organization(
            name="Other Organization",
            email="other@example.com",
            subscription_status="trial"
        )
        test_db.add(other_org)
        test_db.commit()
        test_db.refresh(other_org)
        
        # Assign role in first organization
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Query for roles in different organization
        roles = get_user_roles(test_db, test_user.id, other_org.id)
        
        assert len(roles) == 0


class TestCheckPermission:
    """Tests for check_permission function"""
    
    def test_check_permission_owner_has_all_permissions(self, test_db, test_user, test_organization, test_roles):
        """Test that Owner role has all permissions including billing"""
        # Assign Owner role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check various permissions
        assert check_permission(test_db, test_user, 'billing') is True
        assert check_permission(test_db, test_user, 'user_management') is True
        assert check_permission(test_db, test_user, 'reports') is True
        assert check_permission(test_db, test_user, 'write') is True
    
    def test_check_permission_admin_no_billing(self, test_db, test_user, test_organization, test_roles):
        """Test that Admin role has all permissions except billing"""
        # Assign Admin role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Admin'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check permissions
        assert check_permission(test_db, test_user, 'billing') is False
        assert check_permission(test_db, test_user, 'user_management') is True
        assert check_permission(test_db, test_user, 'reports') is True
    
    def test_check_permission_accountant_specific_permissions(self, test_db, test_user, test_organization, test_roles):
        """Test that Accountant role has specific financial permissions"""
        # Assign Accountant role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Accountant'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check permissions
        assert check_permission(test_db, test_user, 'reports') is True
        assert check_permission(test_db, test_user, 'financial_data') is True
        assert check_permission(test_db, test_user, 'costing') is True
        assert check_permission(test_db, test_user, 'billing') is False
        assert check_permission(test_db, test_user, 'user_management') is False
    
    def test_check_permission_viewer_read_only(self, test_db, test_user, test_organization, test_roles):
        """Test that Viewer role has read-only access"""
        # Assign Viewer role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Viewer'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check permissions - Viewer should not have write/delete/admin permissions
        assert check_permission(test_db, test_user, 'write') is False
        assert check_permission(test_db, test_user, 'delete') is False
        assert check_permission(test_db, test_user, 'billing') is False
        assert check_permission(test_db, test_user, 'user_management') is False
    
    def test_check_permission_no_roles(self, test_db, test_user, test_organization):
        """Test that user with no roles has no permissions"""
        assert check_permission(test_db, test_user, 'billing') is False
        assert check_permission(test_db, test_user, 'reports') is False
        assert check_permission(test_db, test_user, 'write') is False
    
    def test_check_permission_no_organization(self, test_db):
        """Test that user without organization has no permissions"""
        # Create user without organization
        user = User(
            email="noorg@example.com",
            hashed_password="hashed",
            full_name="No Org User",
            organization_id=None
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert check_permission(test_db, user, 'billing') is False
    
    def test_check_permission_multiple_roles(self, test_db, test_user, test_organization, test_roles):
        """Test that user with multiple roles gets combined permissions"""
        # Assign both Accountant and Viewer roles
        for role_name in ['Accountant', 'Viewer']:
            user_role = UserRole(
                user_id=test_user.id,
                role_id=test_roles[role_name].id,
                tenant_id=test_organization.id,
                assigned_by=test_user.id
            )
            test_db.add(user_role)
        test_db.commit()
        
        # Should have Accountant permissions
        assert check_permission(test_db, test_user, 'reports') is True
        assert check_permission(test_db, test_user, 'financial_data') is True
    
    def test_check_permission_explicit_tenant_id(self, test_db, test_user, test_organization, test_roles):
        """Test check_permission with explicit tenant_id parameter"""
        # Assign Owner role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check with explicit tenant_id
        assert check_permission(test_db, test_user, 'billing', tenant_id=test_organization.id) is True


class TestCheckRole:
    """Tests for check_role function"""
    
    def test_check_role_has_role(self, test_db, test_user, test_organization, test_roles):
        """Test checking for a role that user has"""
        # Assign Owner role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        assert check_role(test_db, test_user, 'Owner') is True
    
    def test_check_role_does_not_have_role(self, test_db, test_user, test_organization, test_roles):
        """Test checking for a role that user does not have"""
        # Assign Viewer role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Viewer'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        assert check_role(test_db, test_user, 'Owner') is False
        assert check_role(test_db, test_user, 'Viewer') is True
    
    def test_check_role_no_roles(self, test_db, test_user, test_organization):
        """Test checking role for user with no role assignments"""
        assert check_role(test_db, test_user, 'Owner') is False
        assert check_role(test_db, test_user, 'Admin') is False
    
    def test_check_role_no_organization(self, test_db):
        """Test that user without organization has no roles"""
        # Create user without organization
        user = User(
            email="noorg@example.com",
            hashed_password="hashed",
            full_name="No Org User",
            organization_id=None
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert check_role(test_db, user, 'Owner') is False
    
    def test_check_role_multiple_roles(self, test_db, test_user, test_organization, test_roles):
        """Test checking roles when user has multiple roles"""
        # Assign multiple roles
        for role_name in ['Admin', 'Accountant']:
            user_role = UserRole(
                user_id=test_user.id,
                role_id=test_roles[role_name].id,
                tenant_id=test_organization.id,
                assigned_by=test_user.id
            )
            test_db.add(user_role)
        test_db.commit()
        
        assert check_role(test_db, test_user, 'Admin') is True
        assert check_role(test_db, test_user, 'Accountant') is True
        assert check_role(test_db, test_user, 'Owner') is False
    
    def test_check_role_explicit_tenant_id(self, test_db, test_user, test_organization, test_roles):
        """Test check_role with explicit tenant_id parameter"""
        # Assign Owner role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check with explicit tenant_id
        assert check_role(test_db, test_user, 'Owner', tenant_id=test_organization.id) is True
    
    def test_check_role_tenant_isolation(self, test_db, test_user, test_organization, test_roles):
        """Test that role checks are isolated by tenant"""
        # Create another organization
        other_org = Organization(
            name="Other Organization",
            email="other@example.com",
            subscription_status="trial"
        )
        test_db.add(other_org)
        test_db.commit()
        test_db.refresh(other_org)
        
        # Assign role in first organization
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Check role in different organization
        assert check_role(test_db, test_user, 'Owner', tenant_id=other_org.id) is False



