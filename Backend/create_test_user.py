"""
Create a test user with full access for immediate login
"""
import sys
import os
from pathlib import Path

# Add the Backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from app.core.database import engine, SessionLocal
from app.models.models import User, Organization, Role, UserRole, Base

def create_test_user():
    """Create a test user with Owner role and full access"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Test user credentials
        test_email = "test@example.com"
        test_password = "TestPass123"  # Meets all requirements: uppercase, lowercase, digit, 8+ chars
        test_name = "Test User"
        test_org_name = "Test Organization"
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            print(f"✓ User already exists: {test_email}")
            print(f"  Password: {test_password}")
            print(f"  User ID: {existing_user.id}")
            print(f"  Organization ID: {existing_user.organization_id}")
            return
        
        # Create organization
        org = Organization(
            name=test_org_name,
            email=test_email,
            subscription_status="trial"
        )
        db.add(org)
        db.flush()
        
        # Create user
        hashed_password = generate_password_hash(test_password)
        user = User(
            email=test_email,
            hashed_password=hashed_password,
            full_name=test_name,
            organization_id=org.id,
            role="admin",  # Backward compatibility
            is_active=True
        )
        db.add(user)
        db.flush()
        
        # Create Owner role if it doesn't exist
        owner_role = db.query(Role).filter(Role.name == "Owner").first()
        if not owner_role:
            owner_role = Role(
                name="Owner",
                description="Full system access and organization management",
                permissions=["*"]  # All permissions
            )
            db.add(owner_role)
            db.flush()
        
        # Assign Owner role to user
        user_role = UserRole(
            user_id=user.id,
            role_id=owner_role.id,
            tenant_id=org.id,
            assigned_by=user.id  # Self-assigned
        )
        db.add(user_role)
        
        db.commit()
        
        print("✓ Test user created successfully!")
        print(f"\n=== TEST USER CREDENTIALS ===")
        print(f"Email:    {test_email}")
        print(f"Password: {test_password}")
        print(f"Name:     {test_name}")
        print(f"Organization: {test_org_name}")
        print(f"Role:     Owner (Full Access)")
        print(f"User ID:  {user.id}")
        print(f"Org ID:   {org.id}")
        print(f"\n=== LOGIN INSTRUCTIONS ===")
        print(f"1. Go to http://localhost:3000 (or your Vercel URL)")
        print(f"2. Click 'Sign in'")
        print(f"3. Enter email: {test_email}")
        print(f"4. Enter password: {test_password}")
        print(f"5. Click 'Sign in'")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating test user: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
