#!/usr/bin/env python3
"""
Fix user roles by creating proper RBAC roles and assigning them to existing users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.models import User, Role, UserRole, Organization

def create_default_roles(db: Session):
    """Create default RBAC roles if they don't exist"""
    
    roles_to_create = [
        {
            "name": "Owner",
            "description": "Full system access and organization management",
            "permissions": ["*"]  # All permissions
        },
        {
            "name": "Admin", 
            "description": "Administrative access with user management",
            "permissions": ["user_management", "billing", "reports", "costing", "financial", "scenarios", "integrations"]
        },
        {
            "name": "Accountant",
            "description": "Financial and costing access",
            "permissions": ["costing", "financial", "scenarios", "reports"]
        },
        {
            "name": "Viewer",
            "description": "Read-only access to reports and data",
            "permissions": ["reports"]
        }
    ]
    
    created_roles = {}
    
    for role_data in roles_to_create:
        # Check if role already exists
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        
        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"]
            )
            db.add(role)
            db.flush()
            created_roles[role_data["name"]] = role
            print(f"Created role: {role_data['name']}")
        else:
            created_roles[role_data["name"]] = existing_role
            print(f"Role already exists: {role_data['name']}")
    
    return created_roles

def assign_roles_to_users(db: Session, roles: dict):
    """Assign appropriate RBAC roles to existing users based on their legacy roles"""
    
    users = db.query(User).all()
    
    for user in users:
        print(f"\nProcessing user: {user.email} (legacy role: {user.role})")
        
        # Check if user already has RBAC roles
        existing_user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        if existing_user_roles:
            print(f"  User already has RBAC roles: {[ur.role.name for ur in existing_user_roles]}")
            continue
        
        # Determine which RBAC role to assign based on legacy role
        role_to_assign = None
        
        if user.role in ["admin", "owner"]:
            role_to_assign = roles["Owner"]
        elif user.role in ["accountant", "ca"]:
            role_to_assign = roles["Accountant"]
        elif user.role in ["viewer", "user"]:
            role_to_assign = roles["Viewer"]
        else:
            # Default to Accountant for unknown roles
            role_to_assign = roles["Accountant"]
            print(f"  Unknown legacy role '{user.role}', defaulting to Accountant")
        
        # Create UserRole assignment
        user_role = UserRole(
            user_id=user.id,
            role_id=role_to_assign.id,
            tenant_id=user.organization_id,
            assigned_by=user.id  # Self-assigned for migration
        )
        
        db.add(user_role)
        print(f"  Assigned RBAC role: {role_to_assign.name}")

def main():
    """Main function to fix user roles"""
    print("Starting user role migration...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create default roles
        print("\n1. Creating default RBAC roles...")
        roles = create_default_roles(db)
        
        # Assign roles to users
        print("\n2. Assigning roles to existing users...")
        assign_roles_to_users(db, roles)
        
        # Commit changes
        db.commit()
        print("\n✅ User role migration completed successfully!")
        
        # Show summary
        print("\n📊 Summary:")
        total_users = db.query(User).count()
        total_user_roles = db.query(UserRole).count()
        print(f"  Total users: {total_users}")
        print(f"  Total role assignments: {total_user_roles}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()