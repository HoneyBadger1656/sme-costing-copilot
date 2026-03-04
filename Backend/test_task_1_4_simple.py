"""
Simple test for Task 1.4: Populate predefined roles and assign to existing users

This script directly tests the SQL logic without running full migrations.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime, JSON, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Create test database
TEST_DB_PATH = Path(__file__).parent / "test_task_1_4_simple.db"
DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

Base = declarative_base()

# Define minimal models for testing
class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    subscription_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    organization_id = Column(String(255))
    role = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    permissions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserRole(Base):
    __tablename__ = 'user_roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
    tenant_id = Column(String(255), nullable=False)
    assigned_by = Column(Integer)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    notification_type = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    delivery_method = Column(String(50), default='email')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

def setup_database():
    """Create database and test data"""
    print("Setting up test database...")
    
    # Remove existing database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test organizations
        org1 = Organization(id="org1", name="Test Org 1", email="org1@example.com", subscription_status="active")
        org2 = Organization(id="org2", name="Test Org 2", email="org2@example.com", subscription_status="trial")
        session.add_all([org1, org2])
        session.commit()
        
        # Create test users (2 in org1, 1 in org2)
        user1 = User(email="user1@org1.com", hashed_password="hash1", full_name="User 1", 
                     organization_id="org1", role="admin", is_active=True)
        user2 = User(email="user2@org1.com", hashed_password="hash2", full_name="User 2",
                     organization_id="org1", role="user", is_active=True)
        user3 = User(email="user3@org2.com", hashed_password="hash3", full_name="User 3",
                     organization_id="org2", role="admin", is_active=True)
        session.add_all([user1, user2, user3])
        session.commit()
        
        print(f"  ✓ Created 2 organizations and 3 users")
        return engine, session
        
    except Exception as e:
        print(f"  ✗ Setup failed: {e}")
        session.close()
        raise

def execute_task_1_4_logic(session):
    """Execute the Task 1.4 SQL logic"""
    print("\nExecuting Task 1.4 logic...")
    
    try:
        # 1. Populate predefined roles
        print("  1. Populating predefined roles...")
        session.execute(text("""
            INSERT INTO roles (name, description, permissions) VALUES
            ('Owner', 'Full system access including billing operations', 
             '{"all": true, "billing": true, "user_management": true, "integrations": true, "reports": true, "audit_logs": true}'),
            ('Admin', 'All access except billing operations',
             '{"all": true, "billing": false, "user_management": true, "integrations": true, "reports": true, "audit_logs": true}'),
            ('Accountant', 'Access to financial data and reports',
             '{"financial_data": true, "reports": true, "costing": true, "orders": true, "billing": false, "user_management": false}'),
            ('Viewer', 'Read-only access to all data',
             '{"read_only": true, "write": false, "delete": false, "billing": false, "user_management": false}')
        """))
        session.commit()
        print("     ✓ Created 4 predefined roles")
        
        # 2. Assign Owner role to first user in each organization
        print("  2. Assigning Owner role to first user in each organization...")
        session.execute(text("""
            INSERT INTO user_roles (user_id, role_id, tenant_id, assigned_at)
            SELECT 
                u.id, 
                r.id, 
                u.organization_id,
                CURRENT_TIMESTAMP
            FROM users u
            CROSS JOIN roles r
            WHERE r.name = 'Owner'
            AND u.organization_id IS NOT NULL
            AND u.id IN (
                SELECT MIN(id)
                FROM users
                WHERE organization_id IS NOT NULL
                GROUP BY organization_id
            )
        """))
        session.commit()
        print("     ✓ Assigned Owner roles")
        
        # 3. Create default notification preferences for existing users
        print("  3. Creating default notification preferences...")
        notification_types = [
            'order_evaluation_complete',
            'scenario_analysis_ready',
            'sync_status',
            'low_margin_alert',
            'overdue_receivables'
        ]
        
        for notification_type in notification_types:
            session.execute(text(f"""
                INSERT INTO notification_preferences (user_id, notification_type, enabled, delivery_method)
                SELECT 
                    id,
                    '{notification_type}',
                    true,
                    'email'
                FROM users
                WHERE id NOT IN (
                    SELECT user_id 
                    FROM notification_preferences 
                    WHERE notification_type = '{notification_type}'
                )
            """))
        session.commit()
        print(f"     ✓ Created notification preferences for {len(notification_types)} types")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_results(session):
    """Verify Task 1.4 implementation"""
    print("\n" + "=" * 70)
    print("Verifying Task 1.4 Results")
    print("=" * 70)
    
    all_passed = True
    
    # Check 1: Verify roles
    print("\n1. Verifying predefined roles...")
    result = session.execute(text("SELECT name FROM roles ORDER BY name"))
    roles = [row[0] for row in result.fetchall()]
    expected_roles = ['Accountant', 'Admin', 'Owner', 'Viewer']
    
    if roles == expected_roles:
        print(f"   ✓ All 4 roles exist: {', '.join(roles)}")
    else:
        print(f"   ✗ Expected: {expected_roles}, Got: {roles}")
        all_passed = False
    
    # Check 2: Verify Owner assignments
    print("\n2. Verifying Owner role assignments...")
    result = session.execute(text("""
        SELECT ur.user_id, ur.tenant_id, u.email
        FROM user_roles ur
        JOIN users u ON ur.user_id = u.id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'Owner'
        ORDER BY ur.tenant_id
    """))
    assignments = result.fetchall()
    
    # Should have 2 assignments (first user in each org)
    if len(assignments) == 2:
        print(f"   ✓ Found {len(assignments)} Owner assignments:")
        for user_id, tenant_id, email in assignments:
            print(f"     - User {user_id} ({email}) in tenant {tenant_id}")
    else:
        print(f"   ✗ Expected 2 assignments, found {len(assignments)}")
        all_passed = False
    
    # Check 3: Verify notification types
    print("\n3. Verifying notification preference types...")
    result = session.execute(text("""
        SELECT DISTINCT notification_type 
        FROM notification_preferences 
        ORDER BY notification_type
    """))
    types = [row[0] for row in result.fetchall()]
    expected_types = [
        'low_margin_alert',
        'order_evaluation_complete',
        'overdue_receivables',
        'scenario_analysis_ready',
        'sync_status'
    ]
    
    if types == expected_types:
        print(f"   ✓ All 5 notification types exist")
    else:
        print(f"   ✗ Expected: {expected_types}, Got: {types}")
        all_passed = False
    
    # Check 4: Verify each user has all preferences
    print("\n4. Verifying each user has all notification preferences...")
    result = session.execute(text("""
        SELECT u.id, u.email, COUNT(np.id) as pref_count
        FROM users u
        LEFT JOIN notification_preferences np ON u.id = np.user_id
        GROUP BY u.id, u.email
        ORDER BY u.id
    """))
    
    all_complete = True
    for user_id, email, count in result.fetchall():
        if count == 5:
            print(f"   ✓ User {user_id} ({email}): {count}/5 preferences")
        else:
            print(f"   ✗ User {user_id} ({email}): {count}/5 preferences")
            all_complete = False
            all_passed = False
    
    # Check 5: Verify preferences are enabled
    print("\n5. Verifying preferences are enabled by default...")
    result = session.execute(text("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_count
        FROM notification_preferences
    """))
    total, enabled_count = result.fetchone()
    
    if total == enabled_count:
        print(f"   ✓ All {total} preferences are enabled")
    else:
        print(f"   ✗ Only {enabled_count}/{total} preferences are enabled")
        all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ Task 1.4 verification PASSED")
    else:
        print("✗ Task 1.4 verification FAILED")
    print("=" * 70)
    
    return all_passed

def cleanup():
    """Remove test database"""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
        print(f"\nCleaned up: {TEST_DB_PATH}")

if __name__ == "__main__":
    engine = None
    session = None
    try:
        # Setup
        engine, session = setup_database()
        
        # Execute Task 1.4 logic
        if not execute_task_1_4_logic(session):
            session.close()
            engine.dispose()
            cleanup()
            sys.exit(1)
        
        # Verify
        success = verify_results(session)
        
        # Cleanup
        session.close()
        engine.dispose()
        cleanup()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        if session:
            session.close()
        if engine:
            engine.dispose()
        cleanup()
        sys.exit(1)
