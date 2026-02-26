#!/usr/bin/env python
"""Test registration API"""
import sys
sys.path.insert(0, './Backend')

from app.core.database import engine, Base, get_db
from app.models.models import Organization, User
from app.api.auth import register, get_password_hash
from pydantic import BaseModel

# Test data
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    organization_name: str

user_data = UserCreate(
    email="test@example.com",
    password="password123",
    name="Test User",
    organization_name="Test Org"
)

# Get database session
db = next(get_db())

try:
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        print("✗ User already exists")
    else:
        print("✓ User doesn't exist, creating...")
        
    # Create organization
    org = Organization(
        name=user_data.organization_name,
        email=user_data.email,
        subscription_status="trial"
    )
    db.add(org)
    db.flush()
    print(f"✓ Organization created: {org.id}")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    print(f"✓ Password hashed")
    
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.name,
        organization_id=org.id,
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✓ User created: {user.id}")
    print("✓ Registration successful!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
