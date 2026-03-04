"""Role management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Role, UserRole
from app.schemas.rbac import (
    RoleCreate, 
    RoleResponse, 
    UserRoleCreate, 
    UserRoleResponse,
    RoleAssignmentRequest
)
from app.services.rbac_service import RBACService
from app.utils.rbac import require_role
from app.exceptions import ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_role("Owner", "Admin")),
    db: Session = Depends(get_db)
):
    """
    Create a new custom role.
    
    **Required Role:** Owner or Admin
    
    Creates a new role with specified permissions. Role names must be unique.
    """
    try:
        service = RBACService(db)
        role = service.create_role(role_data)
        return role
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("role_creation_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create role")


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all roles in the system.
    
    Returns all available roles that can be assigned to users.
    """
    try:
        service = RBACService(db)
        roles = service.get_roles()
        return roles
    except Exception as e:
        logger.exception("role_listing_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list roles")


@router.post("/users/{user_id}/roles", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: int,
    assignment: RoleAssignmentRequest,
    current_user: User = Depends(require_role("Owner", "Admin")),
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user.
    
    **Required Role:** Owner or Admin
    
    Assigns the specified role to the user within the current tenant context.
    """
    try:
        service = RBACService(db)
        
        # Use current user's organization as tenant_id
        tenant_id = current_user.organization_id
        
        user_role = service.assign_role(
            user_id=user_id,
            role_id=assignment.role_id,
            tenant_id=tenant_id,
            assigned_by_user_id=current_user.id
        )
        return user_role
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("role_assignment_error", error=str(e), user_id=user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign role")


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(require_role("Owner", "Admin")),
    db: Session = Depends(get_db)
):
    """
    Revoke a role from a user.
    
    **Required Role:** Owner or Admin
    
    Removes the specified role from the user within the current tenant context.
    Users cannot revoke their own Owner role.
    """
    try:
        service = RBACService(db)
        
        # Use current user's organization as tenant_id
        tenant_id = current_user.organization_id
        
        success = service.revoke_role(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            requesting_user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role assignment not found"
            )
        
        return None
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("role_revocation_error", error=str(e), user_id=user_id, role_id=role_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke role")


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse])
async def list_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all roles assigned to a user.
    
    Returns all role assignments for the specified user within the current tenant.
    """
    try:
        service = RBACService(db)
        
        # Use current user's organization as tenant_id
        tenant_id = current_user.organization_id
        
        user_roles = service.get_user_roles(user_id, tenant_id)
        return user_roles
    except Exception as e:
        logger.exception("user_roles_listing_error", error=str(e), user_id=user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list user roles")
