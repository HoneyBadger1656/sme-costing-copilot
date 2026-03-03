"""RBAC (Role-Based Access Control) schemas with validation"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class RoleCreate(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., min_length=2, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: Dict[str, Any] = Field(..., description="Role permissions as JSON structure")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name format"""
        if not v.strip():
            raise ValueError('Role name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Role name must be at least 2 characters long')
        # Ensure role name is alphanumeric with underscores/spaces
        if not all(c.isalnum() or c in ('_', ' ', '-') for c in v):
            raise ValueError('Role name can only contain letters, numbers, underscores, hyphens, and spaces')
        return v.strip()
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate permissions structure"""
        if not isinstance(v, dict):
            raise ValueError('Permissions must be a dictionary')
        if not v:
            raise ValueError('Permissions cannot be empty')
        
        # Valid permission keys
        valid_keys = {
            'all', 'read_only', 'billing', 'user_management', 
            'financial_data', 'reports', 'costing', 'integrations',
            'write', 'delete'
        }
        
        # Check for invalid keys
        invalid_keys = set(v.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f'Invalid permission keys: {", ".join(invalid_keys)}')
        
        # Ensure all values are boolean
        for key, value in v.items():
            if not isinstance(value, bool):
                raise ValueError(f'Permission value for "{key}" must be boolean')
        
        return v


class RoleResponse(BaseModel):
    """Schema for role response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    permissions: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class UserRoleCreate(BaseModel):
    """Schema for assigning a role to a user"""
    user_id: int = Field(..., gt=0, description="User ID to assign role to")
    role_id: int = Field(..., gt=0, description="Role ID to assign")
    tenant_id: str = Field(..., min_length=1, description="Tenant/Organization ID")
    
    @field_validator('tenant_id')
    @classmethod
    def validate_tenant_id(cls, v: str) -> str:
        """Validate tenant ID format"""
        if not v.strip():
            raise ValueError('Tenant ID cannot be empty')
        return v.strip()


class UserRoleResponse(BaseModel):
    """Schema for user role assignment response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    role_id: int
    tenant_id: str
    assigned_by: Optional[int]
    assigned_at: datetime
    created_at: datetime
    updated_at: datetime


class RoleAssignmentRequest(BaseModel):
    """Schema for role assignment request (simplified)"""
    role_id: int = Field(..., gt=0, description="Role ID to assign")
    
    @field_validator('role_id')
    @classmethod
    def validate_role_id(cls, v: int) -> int:
        """Validate role ID"""
        if v <= 0:
            raise ValueError('Role ID must be positive')
        return v
