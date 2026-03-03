"""Tests for RBAC models (Role and UserRole)"""

import pytest
from app.models.models import Role, UserRole, User, Organization


def test_role_creation(test_db):
    """Test creating a Role"""
    role = Role(
        name="TestRole",
        description="A test role",
        permissions={"reports": True, "billing": False}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    
    assert role.id is not None
    assert role.name == "TestRole"
    assert role.description == "A test role"
    assert role.permissions == {"reports": True, "billing": False}
    assert role.created_at is not None
    assert role.updated_at is not None


def test_role_has_permission(test_db):
    """Test Role.has_permission() method"""
    # Test Owner role with 'all' permission
    owner_role = Role(
        name="Owner",
        description="Full access",
        permissions={"all": True, "billing": True}
    )
    test_db.add(owner_role)
    test_db.commit()
    
    assert owner_role.has_permission("billing") is True
    assert owner_role.has_permission("reports") is True
    assert owner_role.has_permission("user_management") is True
    
    # Test Admin role with 'all' but no billing
    admin_role = Role(
        name="Admin",
        description="All except billing",
        permissions={"all": True, "billing": False}
    )
    test_db.add(admin_role)
    test_db.commit()
    
    assert admin_role.has_permission("billing") is False
    assert admin_role.has_permission("reports") is True
    assert admin_role.has_permission("user_management") is True
    
    # Test Viewer role with read_only
    viewer_role = Role(
        name="Viewer",
        description="Read-only access",
        permissions={"read_only": True, "write": False}
    )
    test_db.add(viewer_role)
    test_db.commit()
    
    assert viewer_role.has_permission("write") is False
    assert viewer_role.has_permission("delete") is False
    assert viewer_role.has_permission("billing") is False
    assert viewer_role.has_permission("user_management") is False
    
    # Test Accountant role with specific permissions
    accountant_role = Role(
        name="Accountant",
        description="Financial access",
        permissions={"financial_data": True, "reports": True, "billing": False}
    )
    test_db.add(accountant_role)
    test_db.commit()
    
    assert accountant_role.has_permission("financial_data") is True
    assert accountant_role.has_permission("reports") is True
    assert accountant_role.has_permission("billing") is False
    assert accountant_role.has_permission("user_management") is False


def test_user_role_creation(test_db, test_user, test_organization):
    """Test creating a UserRole"""
    # Create a role first
    role = Role(
        name="TestRole",
        description="A test role",
        permissions={"reports": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    
    # Create user role assignment
    user_role = UserRole(
        user_id=test_user.id,
        role_id=role.id,
        tenant_id=test_organization.id,
        assigned_by=test_user.id
    )
    test_db.add(user_role)
    test_db.commit()
    test_db.refresh(user_role)
    
    assert user_role.id is not None
    assert user_role.user_id == test_user.id
    assert user_role.role_id == role.id
    assert user_role.tenant_id == test_organization.id
    assert user_role.assigned_by == test_user.id
    assert user_role.assigned_at is not None
    assert user_role.created_at is not None
    assert user_role.updated_at is not None


def test_user_role_relationships(test_db, test_user, test_organization):
    """Test UserRole relationships"""
    # Create a role
    role = Role(
        name="TestRole",
        description="A test role",
        permissions={"reports": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    
    # Create user role assignment
    user_role = UserRole(
        user_id=test_user.id,
        role_id=role.id,
        tenant_id=test_organization.id,
        assigned_by=test_user.id
    )
    test_db.add(user_role)
    test_db.commit()
    test_db.refresh(user_role)
    
    # Test relationships
    assert user_role.user.id == test_user.id
    assert user_role.role.id == role.id
    assert user_role.tenant.id == test_organization.id
    assert user_role.assigner.id == test_user.id


def test_get_user_roles(test_db, test_user, test_organization):
    """Test UserRole.get_user_roles() static method"""
    # Create multiple roles
    role1 = Role(
        name="Role1",
        description="First role",
        permissions={"reports": True}
    )
    role2 = Role(
        name="Role2",
        description="Second role",
        permissions={"billing": True}
    )
    test_db.add_all([role1, role2])
    test_db.commit()
    test_db.refresh(role1)
    test_db.refresh(role2)
    
    # Assign both roles to user
    user_role1 = UserRole(
        user_id=test_user.id,
        role_id=role1.id,
        tenant_id=test_organization.id
    )
    user_role2 = UserRole(
        user_id=test_user.id,
        role_id=role2.id,
        tenant_id=test_organization.id
    )
    test_db.add_all([user_role1, user_role2])
    test_db.commit()
    
    # Get user roles
    roles = UserRole.get_user_roles(test_db, test_user.id, test_organization.id)
    
    assert len(roles) == 2
    role_names = [r.name for r in roles]
    assert "Role1" in role_names
    assert "Role2" in role_names


def test_user_role_has_permission(test_db, test_user, test_organization):
    """Test UserRole.has_permission() method"""
    # Create a role with specific permissions
    role = Role(
        name="TestRole",
        description="A test role",
        permissions={"reports": True, "billing": False}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    
    # Create user role assignment
    user_role = UserRole(
        user_id=test_user.id,
        role_id=role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    test_db.refresh(user_role)
    
    # Test permissions
    assert user_role.has_permission(test_db, "reports") is True
    assert user_role.has_permission(test_db, "billing") is False


def test_role_unique_constraint(test_db):
    """Test that role names must be unique"""
    role1 = Role(
        name="UniqueRole",
        description="First role",
        permissions={"reports": True}
    )
    test_db.add(role1)
    test_db.commit()
    
    # Try to create another role with the same name
    role2 = Role(
        name="UniqueRole",
        description="Second role",
        permissions={"billing": True}
    )
    test_db.add(role2)
    
    with pytest.raises(Exception):  # Should raise IntegrityError
        test_db.commit()


def test_user_role_cascade_delete(test_db, test_user, test_organization):
    """Test that deleting a role cascades to user_roles"""
    # Create a role
    role = Role(
        name="TestRole",
        description="A test role",
        permissions={"reports": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    
    # Create user role assignment
    user_role = UserRole(
        user_id=test_user.id,
        role_id=role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    role_id = role.id
    
    # Delete the role
    test_db.delete(role)
    test_db.commit()
    
    # Verify user_role was also deleted
    remaining_user_roles = test_db.query(UserRole).filter(UserRole.role_id == role_id).all()
    assert len(remaining_user_roles) == 0



def test_user_soft_delete(test_db, test_user):
    """Test User soft delete functionality"""
    user_id = test_user.id
    
    # Soft delete the user
    test_user.soft_delete()
    test_db.commit()
    test_db.refresh(test_user)
    
    # Verify deleted_at is set
    assert test_user.deleted_at is not None
    assert test_user.updated_at is not None


def test_user_soft_delete_with_deleted_by(test_db, test_user, test_organization):
    """Test User soft delete with deleted_by user tracking"""
    # Create another user to act as the deleter
    deleter = User(
        email="deleter@example.com",
        hashed_password="hashedpass",
        full_name="Deleter User",
        organization_id=test_organization.id
    )
    test_db.add(deleter)
    test_db.commit()
    test_db.refresh(deleter)
    
    # Soft delete the user with deleted_by tracking
    test_user.soft_delete(deleted_by_user_id=deleter.id)
    test_db.commit()
    test_db.refresh(test_user)
    
    # Verify deleted_at and updated_by are set
    assert test_user.deleted_at is not None
    assert test_user.updated_by == deleter.id
    assert test_user.updated_at is not None


def test_user_active_query_filter(test_db, test_organization):
    """Test User.active() query method filters out soft-deleted users"""
    # Create multiple users
    user1 = User(
        email="user1@example.com",
        hashed_password="hashedpass",
        full_name="User One",
        organization_id=test_organization.id
    )
    user2 = User(
        email="user2@example.com",
        hashed_password="hashedpass",
        full_name="User Two",
        organization_id=test_organization.id
    )
    user3 = User(
        email="user3@example.com",
        hashed_password="hashedpass",
        full_name="User Three",
        organization_id=test_organization.id
    )
    test_db.add_all([user1, user2, user3])
    test_db.commit()
    
    # Soft delete user2
    user2.soft_delete()
    test_db.commit()
    
    # Query active users only
    active_users = User.active(test_db.query(User)).all()
    active_emails = [u.email for u in active_users]
    
    # Should include user1 and user3, but not user2
    assert "user1@example.com" in active_emails
    assert "user3@example.com" in active_emails
    assert "user2@example.com" not in active_emails


def test_user_with_deleted_query_filter(test_db, test_organization):
    """Test User.with_deleted() query method includes soft-deleted users"""
    # Create multiple users
    user1 = User(
        email="user1@example.com",
        hashed_password="hashedpass",
        full_name="User One",
        organization_id=test_organization.id
    )
    user2 = User(
        email="user2@example.com",
        hashed_password="hashedpass",
        full_name="User Two",
        organization_id=test_organization.id
    )
    test_db.add_all([user1, user2])
    test_db.commit()
    
    # Soft delete user2
    user2.soft_delete()
    test_db.commit()
    
    # Query all users including deleted
    all_users = User.with_deleted(test_db.query(User)).all()
    all_emails = [u.email for u in all_users]
    
    # Should include both users
    assert "user1@example.com" in all_emails
    assert "user2@example.com" in all_emails
    assert len(all_users) >= 2


def test_user_audit_fields_on_creation(test_db, test_organization):
    """Test that audit fields are set on user creation"""
    user = User(
        email="newuser@example.com",
        hashed_password="hashedpass",
        full_name="New User",
        organization_id=test_organization.id
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Verify audit fields
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.deleted_at is None


def test_user_updated_at_on_modification(test_db, test_user):
    """Test that updated_at is automatically updated on modification"""
    import time
    
    original_updated_at = test_user.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(0.1)
    
    # Modify the user
    test_user.full_name = "Modified Name"
    test_db.commit()
    test_db.refresh(test_user)
    
    # Verify updated_at changed
    assert test_user.updated_at > original_updated_at
