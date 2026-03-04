"""
Test script for Task 1.4: Populate predefined roles and assign to existing users

This script:
1. Creates a test database
2. Runs the migration
3. Verifies the implementation
"""

import os
import sys
import subprocess
from pathlib import Path

# Set test database URL
TEST_DB_PATH = Path(__file__).parent / "test_migration_1_4.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

def setup_test_database():
    """Create a fresh test database with base schema"""
    print("Setting up test database...")
    
    # Remove existing test database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
        print(f"  Removed existing test database: {TEST_DB_PATH}")
    
    # Create database with base schema (before Phase 3 migration)
    from sqlalchemy import create_engine, text
    from app.core.database import Base
    
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    
    # Import only the models that existed before Phase 3
    from app.models.models import User, Organization, Client, Product
    
    # Create base tables (simulating pre-Phase 3 state)
    Base.metadata.create_all(bind=engine)
    print("  Created base tables")
    
    # Add some test data
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test organizations
        org1 = Organization(
            id="org1",
            name="Test Org 1",
            email="org1@example.com",
            subscription_status="active"
        )
        org2 = Organization(
            id="org2",
            name="Test Org 2",
            email="org2@example.com",
            subscription_status="trial"
        )
        session.add_all([org1, org2])
        session.commit()
        print("  Created 2 test organizations")
        
        # Create test users (2 users in org1, 1 user in org2)
        from werkzeug.security import generate_password_hash
        
        user1 = User(
            email="user1@org1.com",
            hashed_password=generate_password_hash("password123"),
            full_name="User 1",
            organization_id="org1",
            role="admin",
            is_active=True
        )
        user2 = User(
            email="user2@org1.com",
            hashed_password=generate_password_hash("password123"),
            full_name="User 2",
            organization_id="org1",
            role="user",
            is_active=True
        )
        user3 = User(
            email="user3@org2.com",
            hashed_password=generate_password_hash("password123"),
            full_name="User 3",
            organization_id="org2",
            role="admin",
            is_active=True
        )
        session.add_all([user1, user2, user3])
        session.commit()
        print("  Created 3 test users")
        
        print("✓ Test database setup complete\n")
        return True
        
    except Exception as e:
        print(f"✗ Failed to setup test database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def run_migration():
    """Run the Phase 3 migration"""
    print("Running Phase 3 migration...")
    
    try:
        # Run alembic upgrade using Python module
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            env={**os.environ, "DATABASE_URL": f"sqlite:///{TEST_DB_PATH}"}
        )
        
        if result.returncode == 0:
            print("✓ Migration completed successfully\n")
            if result.stdout:
                print("Migration output:")
                print(result.stdout)
            return True
        else:
            print(f"✗ Migration failed with return code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Failed to run migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_task_1_4():
    """Verify Task 1.4 implementation"""
    print("=" * 70)
    print("Verifying Task 1.4: Populate predefined roles and assign to existing users")
    print("=" * 70)
    
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    all_checks_passed = True
    
    try:
        # Check 1: Verify predefined roles exist
        print("\n1. Checking predefined roles...")
        result = session.execute(text("SELECT name, description FROM roles ORDER BY name"))
        roles = result.fetchall()
        
        expected_roles = ['Accountant', 'Admin', 'Owner', 'Viewer']
        actual_roles = [role[0] for role in roles]
        
        if actual_roles == expected_roles:
            print(f"   ✓ All 4 predefined roles exist: {', '.join(actual_roles)}")
        else:
            print(f"   ✗ Expected: {expected_roles}")
            print(f"   ✗ Actual: {actual_roles}")
            all_checks_passed = False
        
        # Check 2: Verify Owner role assignments
        print("\n2. Checking Owner role assignments...")
        result = session.execute(text("""
            SELECT ur.user_id, ur.tenant_id, u.email, r.name
            FROM user_roles ur
            JOIN users u ON ur.user_id = u.id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'Owner'
            ORDER BY ur.tenant_id, ur.user_id
        """))
        owner_assignments = result.fetchall()
        
        # We expect 2 Owner assignments (first user in each org)
        if len(owner_assignments) == 2:
            print(f"   ✓ Found {len(owner_assignments)} Owner role assignments:")
            for user_id, tenant_id, email, role_name in owner_assignments:
                print(f"     - User {user_id} ({email}) in tenant {tenant_id}")
        else:
            print(f"   ✗ Expected 2 Owner assignments, found {len(owner_assignments)}")
            all_checks_passed = False
        
        # Check 3: Verify notification preferences
        print("\n3. Checking default notification preferences...")
        result = session.execute(text("""
            SELECT notification_type, COUNT(*) as count
            FROM notification_preferences
            GROUP BY notification_type
            ORDER BY notification_type
        """))
        pref_counts = result.fetchall()
        
        expected_types = [
            'low_margin_alert',
            'order_evaluation_complete',
            'overdue_receivables',
            'scenario_analysis_ready',
            'sync_status'
        ]
        
        actual_types = [row[0] for row in pref_counts]
        
        if actual_types == expected_types:
            print(f"   ✓ All 5 notification types initialized:")
            for notif_type, count in pref_counts:
                print(f"     - {notif_type}: {count} user(s)")
        else:
            print(f"   ✗ Expected types: {expected_types}")
            print(f"   ✗ Actual types: {actual_types}")
            all_checks_passed = False
        
        # Check 4: Verify each user has all notification types
        print("\n4. Checking notification preferences per user...")
        result = session.execute(text("""
            SELECT u.id, u.email, COUNT(np.id) as pref_count
            FROM users u
            LEFT JOIN notification_preferences np ON u.id = np.user_id
            GROUP BY u.id, u.email
            ORDER BY u.id
        """))
        user_prefs = result.fetchall()
        
        all_users_complete = True
        for user_id, email, pref_count in user_prefs:
            if pref_count == 5:
                print(f"   ✓ User {user_id} ({email}): {pref_count}/5 preferences")
            else:
                print(f"   ✗ User {user_id} ({email}): {pref_count}/5 preferences")
                all_users_complete = False
                all_checks_passed = False
        
        if all_users_complete:
            print("   ✓ All users have complete notification preferences")
        
        # Check 5: Verify preferences are enabled by default
        print("\n5. Checking notification preferences are enabled...")
        result = session.execute(text("""
            SELECT enabled, delivery_method, COUNT(*) as count
            FROM notification_preferences
            GROUP BY enabled, delivery_method
        """))
        pref_settings = result.fetchall()
        
        for enabled, delivery_method, count in pref_settings:
            if enabled and delivery_method == 'email':
                print(f"   ✓ {count} preferences enabled with email delivery")
            else:
                print(f"   ✗ Unexpected setting: enabled={enabled}, method={delivery_method}, count={count}")
                all_checks_passed = False
        
        print("\n" + "=" * 70)
        if all_checks_passed:
            print("✓ Task 1.4 verification PASSED - All checks successful!")
        else:
            print("✗ Task 1.4 verification FAILED - Some checks failed")
        print("=" * 70)
        
        return all_checks_passed
        
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def cleanup():
    """Clean up test database"""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
        print(f"\nCleaned up test database: {TEST_DB_PATH}")

if __name__ == "__main__":
    try:
        # Step 1: Setup test database
        if not setup_test_database():
            sys.exit(1)
        
        # Step 2: Run migration
        if not run_migration():
            sys.exit(1)
        
        # Step 3: Verify implementation
        success = verify_task_1_4()
        
        # Step 4: Cleanup
        cleanup()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
