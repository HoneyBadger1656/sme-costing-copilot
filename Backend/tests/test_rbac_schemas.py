"""Tests for RBAC Pydantic schemas"""

import pytest
from pydantic import ValidationError
from app.schemas.rbac import (
    RoleCreate, RoleResponse, UserRoleCreate, 
    UserRoleResponse, RoleAssignmentRequest
)


def test_role_create_valid():
    """Test creating a valid RoleCreate schema"""
    role = RoleCreate(
        name="TestRole",
        description="A test role",
        permissions={"reports": True, "billing": False}
    )
    assert role.name == "TestRole"
    assert role.description == "A test role"
    assert role.permissions == {"reports": True, "billing": False}


def test_role_create_name_validation():
    """Test RoleCreate name validation"""
    # Test empty name (caught by min_length constraint)
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="",
            permissions={"reports": True}
        )
    assert "at least 2 characters" in str(exc_info.value)
    
    # Test short name
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="A",
            permissions={"reports": True}
        )
    assert "at least 2 characters" in str(exc_info.value)
    
    # Test invalid characters
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="Test@Role!",
            permissions={"reports": True}
        )
    assert "can only contain letters, numbers, underscores, hyphens, and spaces" in str(exc_info.value)


def test_role_create_permissions_validation():
    """Test RoleCreate permissions validation"""
    # Test empty permissions
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="TestRole",
            permissions={}
        )
    assert "Permissions cannot be empty" in str(exc_info.value)
    
    # Test invalid permission keys
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="TestRole",
            permissions={"invalid_key": True}
        )
    assert "Invalid permission keys" in str(exc_info.value)
    
    # Test non-boolean permission values
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="TestRole",
            permissions={"reports": "yes"}
        )
    assert "must be boolean" in str(exc_info.value)


def test_role_create_valid_permission_keys():
    """Test RoleCreate with all valid permission keys"""
    valid_permissions = {
        "all": True,
        "read_only": False,
        "billing": True,
        "user_management": False,
        "financial_data": True,
        "reports": True,
        "costing": False,
        "integrations": True,
        "write": True,
        "delete": False
    }
    
    role = RoleCreate(
        name="CompleteRole",
        permissions=valid_permissions
    )
    assert role.permissions == valid_permissions


def test_user_role_create_valid():
    """Test creating a valid UserRoleCreate schema"""
    user_role = UserRoleCreate(
        user_id=1,
        role_id=2,
        tenant_id="org-123"
    )
    assert user_role.user_id == 1
    assert user_role.role_id == 2
    assert user_role.tenant_id == "org-123"


def test_user_role_create_validation():
    """Test UserRoleCreate validation"""
    # Test invalid user_id (zero)
    with pytest.raises(ValidationError) as exc_info:
        UserRoleCreate(
            user_id=0,
            role_id=1,
            tenant_id="org-123"
        )
    assert "greater than 0" in str(exc_info.value)
    
    # Test invalid role_id (negative)
    with pytest.raises(ValidationError) as exc_info:
        UserRoleCreate(
            user_id=1,
            role_id=-1,
            tenant_id="org-123"
        )
    assert "greater than 0" in str(exc_info.value)
    
    # Test empty tenant_id (caught by min_length constraint)
    with pytest.raises(ValidationError) as exc_info:
        UserRoleCreate(
            user_id=1,
            role_id=1,
            tenant_id=""
        )
    assert "at least 1 character" in str(exc_info.value)


def test_role_assignment_request_valid():
    """Test creating a valid RoleAssignmentRequest schema"""
    request = RoleAssignmentRequest(role_id=5)
    assert request.role_id == 5


def test_role_assignment_request_validation():
    """Test RoleAssignmentRequest validation"""
    # Test invalid role_id (zero)
    with pytest.raises(ValidationError) as exc_info:
        RoleAssignmentRequest(role_id=0)
    assert "greater than 0" in str(exc_info.value)
    
    # Test invalid role_id (negative)
    with pytest.raises(ValidationError) as exc_info:
        RoleAssignmentRequest(role_id=-5)
    assert "greater than 0" in str(exc_info.value)


def test_role_create_name_trimming():
    """Test that role names are trimmed of whitespace"""
    role = RoleCreate(
        name="  TestRole  ",
        permissions={"reports": True}
    )
    assert role.name == "TestRole"


def test_user_role_create_tenant_id_trimming():
    """Test that tenant_id is trimmed of whitespace"""
    user_role = UserRoleCreate(
        user_id=1,
        role_id=2,
        tenant_id="  org-123  "
    )
    assert user_role.tenant_id == "org-123"
