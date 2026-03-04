"""Verify Role and UserRole models match migration schema"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Role, UserRole, User, Organization

# Create test database
engine = create_engine("sqlite:///./test_rbac_models.db")
Base.metadata.create_all(bind=engine)

# Inspect the created tables
inspector = inspect(engine)

print("=" * 60)
print("ROLE TABLE VERIFICATION")
print("=" * 60)

# Check roles table
if 'roles' in inspector.get_table_names():
    print("✓ roles table exists")
    
    columns = inspector.get_columns('roles')
    column_names = [col['name'] for col in columns]
    
    expected_columns = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']
    for col in expected_columns:
        if col in column_names:
            print(f"  ✓ Column '{col}' exists")
        else:
            print(f"  ✗ Column '{col}' MISSING")
    
    # Check indexes
    indexes = inspector.get_indexes('roles')
    print(f"\n  Indexes: {len(indexes)} found")
    for idx in indexes:
        print(f"    - {idx['name']}: {idx['column_names']}")
    
    # Check unique constraints
    unique_constraints = inspector.get_unique_constraints('roles')
    print(f"\n  Unique constraints: {len(unique_constraints)} found")
    for uc in unique_constraints:
        print(f"    - {uc.get('name', 'unnamed')}: {uc['column_names']}")
else:
    print("✗ roles table DOES NOT EXIST")

print("\n" + "=" * 60)
print("USER_ROLES TABLE VERIFICATION")
print("=" * 60)

# Check user_roles table
if 'user_roles' in inspector.get_table_names():
    print("✓ user_roles table exists")
    
    columns = inspector.get_columns('user_roles')
    column_names = [col['name'] for col in columns]
    
    expected_columns = ['id', 'user_id', 'role_id', 'tenant_id', 'assigned_by', 
                       'assigned_at', 'created_at', 'updated_at']
    for col in expected_columns:
        if col in column_names:
            print(f"  ✓ Column '{col}' exists")
        else:
            print(f"  ✗ Column '{col}' MISSING")
    
    # Check foreign keys
    foreign_keys = inspector.get_foreign_keys('user_roles')
    print(f"\n  Foreign keys: {len(foreign_keys)} found")
    for fk in foreign_keys:
        print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Check indexes
    indexes = inspector.get_indexes('user_roles')
    print(f"\n  Indexes: {len(indexes)} found")
    for idx in indexes:
        print(f"    - {idx['name']}: {idx['column_names']}")
else:
    print("✗ user_roles table DOES NOT EXIST")

print("\n" + "=" * 60)
print("MODEL METHODS VERIFICATION")
print("=" * 60)

# Test model methods exist
print("✓ Role.has_permission() method exists" if hasattr(Role, 'has_permission') else "✗ Role.has_permission() MISSING")
print("✓ UserRole.get_user_roles() method exists" if hasattr(UserRole, 'get_user_roles') else "✗ UserRole.get_user_roles() MISSING")
print("✓ UserRole.has_permission() method exists" if hasattr(UserRole, 'has_permission') else "✗ UserRole.has_permission() MISSING")

print("\n" + "=" * 60)
print("FUNCTIONAL TEST")
print("=" * 60)

# Create a session and test basic functionality
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Create test organization
    org = Organization(
        name="Test Org",
        email="test@example.com"
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    print(f"✓ Created test organization: {org.id}")
    
    # Create test user
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        hashed_password="hashed",
        full_name="Test User",
        organization_id=org.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✓ Created test user: {user.id}")
    
    # Create test role or get existing one
    role = db.query(Role).filter(Role.name == "Owner").first()
    if not role:
        role = Role(
            name="Owner",
            description="Full access",
            permissions={"all": True, "billing": True}
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        print(f"✓ Created test role: {role.id}")
    else:
        print(f"✓ Using existing test role: {role.id}")
    
    # Test has_permission method
    assert role.has_permission("billing") == True
    assert role.has_permission("reports") == True
    print("✓ Role.has_permission() works correctly")
    
    # Create user role assignment
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        tenant_id=org.id,
        assigned_by=user.id
    )
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    print(f"✓ Created user role assignment: {user_role.id}")
    
    # Test get_user_roles method
    roles = UserRole.get_user_roles(db, user.id, org.id)
    assert len(roles) == 1
    assert roles[0].name == "Owner"
    print("✓ UserRole.get_user_roles() works correctly")
    
    # Test has_permission method
    assert user_role.has_permission(db, "billing") == True
    print("✓ UserRole.has_permission() works correctly")
    
    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS PASSED ✓")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error during functional test: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

# Clean up
import os
try:
    if os.path.exists("./test_rbac_models.db"):
        os.remove("./test_rbac_models.db")
        print("\n✓ Cleaned up test database")
except PermissionError:
    print("\n⚠ Could not remove test database (file in use), will be cleaned up later")
