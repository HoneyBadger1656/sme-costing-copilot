"""Integration tests for role management API endpoints"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import User, Organization, Role, UserRole

# Set DEBUG mode for tests to disable TrustedHostMiddleware
os.environ["DEBUG"] = "true"


@pytest.fixture
def owner_role(test_db):
    """Create Owner role"""
    role = Role(
        name="Owner",
        description="Full system access including billing",
        permissions={
            "all": True,
            "billing": True,
            "user_management": True,
            "financial_data": True,
            "reports": True,
            "costing": True,
            "integrations": True,
            "write": True,
            "delete": True
        }
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def admin_role(test_db):
    """Create Admin role"""
    role = Role(
        name="Admin",
        description="All access except billing",
        permissions={
            "all": True,
            "billing": False,
            "user_management": True,
            "financial_data": True,
            "reports": True,
            "costing": True,
            "integrations": True,
            "write": True,
            "delete": True
        }
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def viewer_role(test_db):
    """Create Viewer role"""
    role = Role(
        name="Viewer",
        description="Read-only access",
        permissions={
            "read_only": True,
            "billing": False,
            "user_management": False,
            "write": False,
            "delete": False
        }
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def owner_user(test_db, test_organization, owner_role):
    """Create a user with Owner role"""
    from werkzeug.security import generate_password_hash
    
    user = User(
        email="owner@example.com",
        hashed_password=generate_password_hash("OwnerPassword123"),
        full_name="Owner User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Owner role
    user_role = UserRole(
        user_id=user.id,
        role_id=owner_role.id,
        tenant_id=test_organization.id,
        assigned_by=user.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user


@pytest.fixture
def viewer_user(test_db, test_organization, viewer_role):
    """Create a user with Viewer role"""
    from werkzeug.security import generate_password_hash
    
    user = User(
        email="viewer@example.com",
        hashed_password=generate_password_hash("ViewerPassword123"),
        full_name="Viewer User",
        organization_id=test_organization.id,
        role="viewer",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Viewer role
    user_role = UserRole(
        user_id=user.id,
        role_id=viewer_role.id,
        tenant_id=test_organization.id,
        assigned_by=user.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user


@pytest.fixture
def owner_auth_headers(client, owner_user):
    """Get authentication headers for owner user"""
    response = client.post(
        "/api/auth/login",
        data={"username": owner_user.email, "password": "OwnerPassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers(client, viewer_user):
    """Get authentication headers for viewer user"""
    response = client.post(
        "/api/auth/login",
        data={"username": viewer_user.email, "password": "ViewerPassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestRoleCreation:
    """Tests for role creation endpoint"""
    
    def test_create_role_as_owner(self, client, owner_auth_headers):
        """Test that Owner can create a custom role"""
        role_data = {
            "name": "Custom Manager",
            "description": "Custom role for managers",
            "permissions": {
                "financial_data": True,
                "reports": True,
                "write": True,
                "delete": False
            }
        }
        
        response = client.post(
            "/api/roles/",
            json=role_data,
            headers=owner_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Manager"
        assert data["description"] == "Custom role for managers"
        assert data["permissions"]["financial_data"] is True
        assert "id" in data
        assert "created_at" in data
    
    def test_create_role_as_viewer_forbidden(self, client, viewer_auth_headers):
        """Test that Viewer cannot create roles"""
        role_data = {
            "name": "Unauthorized Role",
            "description": "Should not be created",
            "permissions": {"read_only": True}
        }
        
        response = client.post(
            "/api/roles/",
            json=role_data,
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_create_duplicate_role_name(self, client, owner_auth_headers, owner_role):
        """Test that duplicate role names are rejected"""
        role_data = {
            "name": "Owner",  # Already exists
            "description": "Duplicate role",
            "permissions": {"all": True}
        }
        
        response = client.post(
            "/api/roles/",
            json=role_data,
            headers=owner_auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestRoleListing:
    """Tests for role listing endpoint"""
    
    def test_list_roles(self, client, owner_auth_headers, owner_role, admin_role, viewer_role):
        """Test listing all roles"""
        response = client.get(
            "/api/roles/",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        role_names = [role["name"] for role in data]
        assert "Owner" in role_names
        assert "Admin" in role_names
        assert "Viewer" in role_names
    
    def test_list_roles_as_viewer(self, client, viewer_auth_headers, owner_role, viewer_role):
        """Test that Viewer can list roles"""
        response = client.get(
            "/api/roles/",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


class TestRoleAssignment:
    """Tests for role assignment endpoint"""
    
    def test_assign_role_to_user(self, client, owner_auth_headers, test_user, admin_role):
        """Test assigning a role to a user"""
        response = client.post(
            f"/api/roles/users/{test_user.id}/roles",
            json={"role_id": admin_role.id},
            headers=owner_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["role_id"] == admin_role.id
        assert "assigned_at" in data
        assert "assigned_by" in data
    
    def test_assign_role_as_viewer_forbidden(self, client, viewer_auth_headers, test_user, admin_role):
        """Test that Viewer cannot assign roles"""
        response = client.post(
            f"/api/roles/users/{test_user.id}/roles",
            json={"role_id": admin_role.id},
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_assign_duplicate_role(self, client, owner_auth_headers, owner_user, owner_role):
        """Test that assigning duplicate role is rejected"""
        # Owner user already has Owner role from fixture
        response = client.post(
            f"/api/roles/users/{owner_user.id}/roles",
            json={"role_id": owner_role.id},
            headers=owner_auth_headers
        )
        
        assert response.status_code == 400
        assert "already has role" in response.json()["detail"]
    
    def test_assign_nonexistent_role(self, client, owner_auth_headers, test_user):
        """Test assigning a non-existent role"""
        response = client.post(
            f"/api/roles/users/{test_user.id}/roles",
            json={"role_id": 99999},
            headers=owner_auth_headers
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]


class TestRoleRevocation:
    """Tests for role revocation endpoint"""
    
    def test_revoke_role_from_user(self, client, owner_auth_headers, test_db, test_user, admin_role, test_organization):
        """Test revoking a role from a user"""
        # First assign the role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=admin_role.id,
            tenant_id=test_organization.id,
            assigned_by=1
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Now revoke it
        response = client.delete(
            f"/api/roles/users/{test_user.id}/roles/{admin_role.id}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify role was revoked
        remaining_roles = test_db.query(UserRole).filter(
            UserRole.user_id == test_user.id,
            UserRole.role_id == admin_role.id
        ).all()
        assert len(remaining_roles) == 0
    
    def test_revoke_role_as_viewer_forbidden(self, client, viewer_auth_headers, test_user, admin_role):
        """Test that Viewer cannot revoke roles"""
        response = client.delete(
            f"/api/roles/users/{test_user.id}/roles/{admin_role.id}",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_revoke_own_owner_role_forbidden(self, client, owner_auth_headers, owner_user, owner_role):
        """Test that user cannot revoke their own Owner role"""
        response = client.delete(
            f"/api/roles/users/{owner_user.id}/roles/{owner_role.id}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 400
        assert "Cannot revoke your own Owner role" in response.json()["detail"]
    
    def test_revoke_nonexistent_assignment(self, client, owner_auth_headers, test_user, admin_role):
        """Test revoking a role that wasn't assigned"""
        response = client.delete(
            f"/api/roles/users/{test_user.id}/roles/{admin_role.id}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUserRolesListing:
    """Tests for listing user roles endpoint"""
    
    def test_list_user_roles(self, client, owner_auth_headers, owner_user, owner_role):
        """Test listing roles for a user"""
        response = client.get(
            f"/api/roles/users/{owner_user.id}/roles",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["user_id"] == owner_user.id
        assert data[0]["role_id"] == owner_role.id
    
    def test_list_user_roles_empty(self, client, owner_auth_headers, test_user):
        """Test listing roles for a user with no roles"""
        response = client.get(
            f"/api/roles/users/{test_user.id}/roles",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestTenantIsolation:
    """Tests for tenant isolation in role operations"""
    
    def test_roles_isolated_by_tenant(self, client, test_db, owner_auth_headers, test_user, admin_role):
        """Test that role assignments are isolated by tenant"""
        # Create a second organization
        from app.models.models import Organization
        org2 = Organization(
            name="Second Organization",
            email="org2@example.com",
            subscription_status="trial"
        )
        test_db.add(org2)
        test_db.commit()
        test_db.refresh(org2)
        
        # Assign role in org2
        user_role = UserRole(
            user_id=test_user.id,
            role_id=admin_role.id,
            tenant_id=org2.id,
            assigned_by=1
        )
        test_db.add(user_role)
        test_db.commit()
        
        # List roles for test_user (should not see org2 assignment)
        response = client.get(
            f"/api/roles/users/{test_user.id}/roles",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should not include the role from org2
        for role_assignment in data:
            assert role_assignment["tenant_id"] != org2.id
