"""Role-Based Access Control (RBAC) utility functions"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.models import User, Role, UserRole


def get_user_roles(db: Session, user_id: int, tenant_id: str) -> List[Role]:
    """
    Get all roles assigned to a user within a specific tenant.
    
    Args:
        db: Database session
        user_id: User ID to fetch roles for
        tenant_id: Tenant/Organization ID for context isolation
    
    Returns:
        List of Role objects assigned to the user in the tenant
        
    Example:
        >>> roles = get_user_roles(db, user_id=1, tenant_id="org-123")
        >>> role_names = [role.name for role in roles]
        >>> print(role_names)  # ['Owner', 'Admin']
    """
    user_roles = db.query(UserRole).options(
        joinedload(UserRole.role)
    ).filter(
        UserRole.user_id == user_id,
        UserRole.tenant_id == tenant_id
    ).all()
    
    return [ur.role for ur in user_roles]


def check_permission(db: Session, user: User, permission: str, tenant_id: Optional[str] = None) -> bool:
    """
    Check if a user has a specific permission within their tenant context.
    
    This function checks all roles assigned to the user and returns True if any
    of those roles grant the requested permission.
    
    Args:
        db: Database session
        user: User object to check permissions for
        permission: Permission name to check (e.g., 'billing', 'user_management', 'reports')
        tenant_id: Optional tenant ID (defaults to user.organization_id)
    
    Returns:
        bool: True if user has the permission, False otherwise
        
    Example:
        >>> has_billing = check_permission(db, user, 'billing')
        >>> if has_billing:
        ...     # User can access billing operations
        ...     pass
    """
    # Use user's organization_id if tenant_id not provided
    if tenant_id is None:
        tenant_id = user.organization_id
    
    # If user has no organization, they have no permissions
    if not tenant_id:
        return False
    
    # Get all roles for the user in this tenant
    roles = get_user_roles(db, user.id, tenant_id)
    
    # Check if any role grants the permission
    for role in roles:
        if role.has_permission(permission):
            return True
    
    return False


def check_role(db: Session, user: User, role_name: str, tenant_id: Optional[str] = None) -> bool:
    """
    Check if a user has a specific role within their tenant context.
    
    Args:
        db: Database session
        user: User object to check role for
        role_name: Role name to check (e.g., 'Owner', 'Admin', 'Accountant', 'Viewer')
        tenant_id: Optional tenant ID (defaults to user.organization_id)
    
    Returns:
        bool: True if user has the role, False otherwise
        
    Example:
        >>> is_owner = check_role(db, user, 'Owner')
        >>> if is_owner:
        ...     # User has Owner role
        ...     pass
    """
    # Use user's organization_id if tenant_id not provided
    if tenant_id is None:
        tenant_id = user.organization_id
    
    # If user has no organization, they have no roles
    if not tenant_id:
        return False
    
    # Get all roles for the user in this tenant
    roles = get_user_roles(db, user.id, tenant_id)
    
    # Check if any role matches the requested role name
    for role in roles:
        if role.name == role_name:
            return True
    
    return False


# FastAPI dependency decorators for RBAC
from functools import wraps
from typing import List, Union
from fastapi import Depends, HTTPException, status, Request
from app.core.database import get_db
from app.api.auth import get_current_user
from app.logging_config import get_logger

logger = get_logger(__name__)


def require_role(*role_names: str):
    """
    FastAPI dependency decorator that enforces role-based access control.
    
    This decorator verifies that the current user has at least one of the specified
    roles within their tenant context. If the user lacks all required roles, it
    returns HTTP 403 Forbidden and logs the authorization failure.
    
    Args:
        *role_names: One or more role names that are allowed (e.g., 'Owner', 'Admin')
    
    Returns:
        FastAPI dependency function that can be used with Depends()
    
    Example:
        >>> @router.get("/admin/users")
        >>> async def list_users(
        ...     current_user: User = Depends(require_role("Owner", "Admin")),
        ...     db: Session = Depends(get_db)
        ... ):
        ...     # Only Owner or Admin can access this endpoint
        ...     pass
    
    Raises:
        HTTPException: 403 Forbidden if user lacks required role
    """
    async def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has required role"""
        # Check if user has any of the required roles
        for role_name in role_names:
            if check_role(db, current_user, role_name):
                return current_user
        
        # User doesn't have any of the required roles - log and deny
        logger.warning(
            "authorization_failed",
            user_id=current_user.id,
            email=current_user.email,
            endpoint=request.url.path,
            method=request.method,
            required_roles=list(role_names),
            reason="missing_required_role"
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {' or '.join(role_names)}"
        )
    
    return role_checker


def require_permission(*permission_names: str):
    """
    FastAPI dependency decorator that enforces permission-based access control.
    
    This decorator verifies that the current user has at least one of the specified
    permissions within their tenant context. Permissions are checked across all roles
    assigned to the user. If the user lacks all required permissions, it returns
    HTTP 403 Forbidden and logs the authorization failure.
    
    Args:
        *permission_names: One or more permission names that are allowed 
                          (e.g., 'billing', 'reports', 'user_management')
    
    Returns:
        FastAPI dependency function that can be used with Depends()
    
    Example:
        >>> @router.post("/billing/invoice")
        >>> async def create_invoice(
        ...     invoice_data: InvoiceCreate,
        ...     current_user: User = Depends(require_permission("billing")),
        ...     db: Session = Depends(get_db)
        ... ):
        ...     # Only users with billing permission can access this endpoint
        ...     pass
    
    Raises:
        HTTPException: 403 Forbidden if user lacks required permission
    """
    async def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has required permission"""
        # Check if user has any of the required permissions
        for permission_name in permission_names:
            if check_permission(db, current_user, permission_name):
                return current_user
        
        # User doesn't have any of the required permissions - log and deny
        logger.warning(
            "authorization_failed",
            user_id=current_user.id,
            email=current_user.email,
            endpoint=request.url.path,
            method=request.method,
            required_permissions=list(permission_names),
            reason="missing_required_permission"
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required permission: {' or '.join(permission_names)}"
        )
    
    return permission_checker
