"""Tests for RBAC decorator functions (require_role and require_permission)"""

import pytest
from app.models.models import User, Organization, Role, UserRole
from app.utils.rbac import require_role, require_permission
from fastapi import HTTPException
from unittest.mock import Mock


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


class TestRequireRoleDecorator:
    """Tests for require_role decorator"""
    
    def test_require_role_returns_user_with_valid_role(self, test_db, test_user, test_organization, test_roles):
        """Test that require_role returns user when they have the required role"""
        # Assign Owner role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function
        role_checker = require_role("Owner")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Call the dependency function directly
        import asyncio
        result = asyncio.run(role_checker(mock_request, test_user, test_db))
        
        # Should return the user
        assert result == test_user
    
    def test_require_role_raises_403_with_invalid_role(self, test_db, test_user, test_organization, test_roles):
        """Test that require_role raises HTTPException when user lacks required role"""
        # Assign Viewer role to user (not Owner)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Viewer'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function
        role_checker = require_role("Owner")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Call the dependency function and expect exception
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(role_checker(mock_request, test_user, test_db))
        
        # Should be 403 Forbidden
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
        assert "Owner" in exc_info.value.detail
    
    def test_require_role_accepts_multiple_roles(self, test_db, test_user, test_organization, test_roles):
        """Test that require_role accepts user with any of multiple allowed roles"""
        # Assign Admin role to user (one of the allowed roles)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Admin'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function with multiple allowed roles
        role_checker = require_role("Owner", "Admin")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Call the dependency function
        import asyncio
        result = asyncio.run(role_checker(mock_request, test_user, test_db))
        
        # Should return the user because they have Admin role
        assert result == test_user
    
    def test_require_role_raises_403_with_no_roles(self, test_db, test_user, test_organization):
        """Test that require_role raises HTTPException when user has no roles"""
        # Don't assign any roles to user
        
        # Create the dependency function
        role_checker = require_role("Viewer")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Call the dependency function and expect exception
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(role_checker(mock_request, test_user, test_db))
        
        # Should be 403 Forbidden
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail


class TestRequirePermissionDecorator:
    """Tests for require_permission decorator"""
    
    def test_require_permission_returns_user_with_valid_permission(self, test_db, test_user, test_organization, test_roles):
        """Test that require_permission returns user when they have the required permission"""
        # Assign Owner role to user (has billing permission)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Owner'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function
        permission_checker = require_permission("billing")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "POST"
        
        # Call the dependency function
        import asyncio
        result = asyncio.run(permission_checker(mock_request, test_user, test_db))
        
        # Should return the user
        assert result == test_user
    
    def test_require_permission_raises_403_without_permission(self, test_db, test_user, test_organization, test_roles):
        """Test that require_permission raises HTTPException when user lacks permission"""
        # Assign Accountant role to user (no billing permission)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Accountant'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function
        permission_checker = require_permission("billing")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "POST"
        
        # Call the dependency function and expect exception
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(permission_checker(mock_request, test_user, test_db))
        
        # Should be 403 Forbidden
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
        assert "billing" in exc_info.value.detail
    
    def test_require_permission_accepts_multiple_permissions(self, test_db, test_user, test_organization, test_roles):
        """Test that require_permission accepts user with any of multiple allowed permissions"""
        # Assign Accountant role to user (has reports permission)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Accountant'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function with multiple allowed permissions
        permission_checker = require_permission("reports", "billing")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Call the dependency function
        import asyncio
        result = asyncio.run(permission_checker(mock_request, test_user, test_db))
        
        # Should return the user because they have reports permission
        assert result == test_user
    
    def test_require_permission_accountant_has_financial_permissions(self, test_db, test_user, test_organization, test_roles):
        """Test that Accountant role has specific financial permissions"""
        # Assign Accountant role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Accountant'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Test financial_data permission
        permission_checker = require_permission("financial_data")
        import asyncio
        result = asyncio.run(permission_checker(mock_request, test_user, test_db))
        assert result == test_user
        
        # Test costing permission
        permission_checker = require_permission("costing")
        result = asyncio.run(permission_checker(mock_request, test_user, test_db))
        assert result == test_user
    
    def test_require_permission_raises_403_with_no_permissions(self, test_db, test_user, test_organization):
        """Test that require_permission raises HTTPException when user has no permissions"""
        # Don't assign any roles to user
        
        # Create the dependency function
        permission_checker = require_permission("reports")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Call the dependency function and expect exception
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(permission_checker(mock_request, test_user, test_db))
        
        # Should be 403 Forbidden
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail


class TestAuthorizationLogging:
    """Tests for authorization failure logging"""
    
    def test_require_role_logs_authorization_failure(self, test_db, test_user, test_organization, test_roles, caplog):
        """Test that authorization failures are logged with proper details"""
        import logging
        
        # Assign Viewer role to user (not Owner)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Viewer'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function
        role_checker = require_role("Owner")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "GET"
        
        # Capture logs
        with caplog.at_level(logging.WARNING):
            import asyncio
            with pytest.raises(HTTPException):
                asyncio.run(role_checker(mock_request, test_user, test_db))
        
        # Check that authorization failure was logged
        assert any("authorization_failed" in record.message for record in caplog.records)
    
    def test_require_permission_logs_authorization_failure(self, test_db, test_user, test_organization, test_roles, caplog):
        """Test that permission check failures are logged with proper details"""
        import logging
        
        # Assign Viewer role to user (no billing permission)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_roles['Viewer'].id,
            tenant_id=test_organization.id,
            assigned_by=test_user.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Create the dependency function
        permission_checker = require_permission("billing")
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.method = "POST"
        
        # Capture logs
        with caplog.at_level(logging.WARNING):
            import asyncio
            with pytest.raises(HTTPException):
                asyncio.run(permission_checker(mock_request, test_user, test_db))
        
        # Check that authorization failure was logged
        assert any("authorization_failed" in record.message for record in caplog.records)
