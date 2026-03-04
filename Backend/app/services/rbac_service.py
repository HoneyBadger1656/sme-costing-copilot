"""Role-Based Access Control (RBAC) service layer"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.models import Role, UserRole, User
from app.schemas.rbac import RoleCreate, RoleResponse, UserRoleCreate, UserRoleResponse
from app.exceptions import ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class RBACService:
    """Service for managing roles and role assignments"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_role(self, role_data: RoleCreate) -> Role:
        """
        Create a new custom role.
        
        Args:
            role_data: Role creation data
            
        Returns:
            Created Role object
            
        Raises:
            ValidationError: If role name already exists
        """
        # Check if role name already exists
        existing_role = self.db.query(Role).filter(Role.name == role_data.name).first()
        if existing_role:
            logger.warning("role_creation_failed", name=role_data.name, reason="name_exists")
            raise ValidationError(f"Role with name '{role_data.name}' already exists")
        
        # Create new role
        role = Role(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions
        )
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        
        logger.info("role_created", role_id=role.id, name=role.name)
        return role
    
    def get_roles(self) -> List[Role]:
        """
        Get all roles in the system.
        
        Returns:
            List of all Role objects
        """
        roles = self.db.query(Role).order_by(Role.name).all()
        return roles
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """
        Get a role by its ID.
        
        Args:
            role_id: Role ID to fetch
            
        Returns:
            Role object if found, None otherwise
        """
        role = self.db.query(Role).filter(Role.id == role_id).first()
        return role
    
    def assign_role(
        self, 
        user_id: int, 
        role_id: int, 
        tenant_id: str, 
        assigned_by_user_id: int
    ) -> UserRole:
        """
        Assign a role to a user within a tenant.
        
        Args:
            user_id: User ID to assign role to
            role_id: Role ID to assign
            tenant_id: Tenant/Organization ID
            assigned_by_user_id: User ID of the person assigning the role
            
        Returns:
            Created UserRole object
            
        Raises:
            ValidationError: If user, role, or tenant doesn't exist, or if assignment already exists
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("role_assignment_failed", user_id=user_id, reason="user_not_found")
            raise ValidationError(f"User with ID {user_id} not found")
        
        # Validate role exists
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            logger.warning("role_assignment_failed", role_id=role_id, reason="role_not_found")
            raise ValidationError(f"Role with ID {role_id} not found")
        
        # Check if assignment already exists
        existing_assignment = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.tenant_id == tenant_id
        ).first()
        
        if existing_assignment:
            logger.warning(
                "role_assignment_failed",
                user_id=user_id,
                role_id=role_id,
                tenant_id=tenant_id,
                reason="assignment_exists"
            )
            raise ValidationError(f"User already has role '{role.name}' in this tenant")
        
        # Create role assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            assigned_by=assigned_by_user_id,
            assigned_at=datetime.utcnow()
        )
        
        self.db.add(user_role)
        
        try:
            self.db.commit()
            self.db.refresh(user_role)
            logger.info(
                "role_assigned",
                user_id=user_id,
                role_id=role_id,
                role_name=role.name,
                tenant_id=tenant_id,
                assigned_by=assigned_by_user_id
            )
            return user_role
        except IntegrityError as e:
            self.db.rollback()
            logger.error("role_assignment_failed", error=str(e))
            raise ValidationError("Failed to assign role due to database constraint")
    
    def revoke_role(
        self, 
        user_id: int, 
        role_id: int, 
        tenant_id: str,
        requesting_user_id: int
    ) -> bool:
        """
        Revoke a role from a user within a tenant.
        
        Args:
            user_id: User ID to revoke role from
            role_id: Role ID to revoke
            tenant_id: Tenant/Organization ID
            requesting_user_id: User ID of the person revoking the role
            
        Returns:
            True if role was revoked, False if assignment didn't exist
            
        Raises:
            ValidationError: If attempting to revoke Owner role from self
        """
        # Prevent self-modification of Owner role
        if user_id == requesting_user_id:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if role and role.name == "Owner":
                logger.warning(
                    "role_revocation_failed",
                    user_id=user_id,
                    role_id=role_id,
                    reason="self_modification_owner_role"
                )
                raise ValidationError("Cannot revoke your own Owner role")
        
        # Find the role assignment
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.tenant_id == tenant_id
        ).first()
        
        if not user_role:
            logger.warning(
                "role_revocation_failed",
                user_id=user_id,
                role_id=role_id,
                tenant_id=tenant_id,
                reason="assignment_not_found"
            )
            return False
        
        # Delete the role assignment
        self.db.delete(user_role)
        self.db.commit()
        
        logger.info(
            "role_revoked",
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            revoked_by=requesting_user_id
        )
        return True
    
    def get_user_roles(self, user_id: int, tenant_id: str) -> List[UserRole]:
        """
        Get all role assignments for a user within a tenant.
        
        Args:
            user_id: User ID to fetch roles for
            tenant_id: Tenant/Organization ID
            
        Returns:
            List of UserRole objects with role relationships loaded
        """
        user_roles = self.db.query(UserRole).options(
            joinedload(UserRole.role)
        ).filter(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id
        ).all()
        
        return user_roles
