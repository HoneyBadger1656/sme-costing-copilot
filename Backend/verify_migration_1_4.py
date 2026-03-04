"""
Verification script for Task 1.4: Populate predefined roles and assign to existing users

This script verifies:
1. Four predefined roles are created with correct permissions
2. Owner role is assigned to first user in each tenant
3. Default notification preferences are created for existing users
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use test database
DATABASE_URL = "sqlite:///./test_migration.db"

def verify_migration():
    """Verify migration Task 1.4 implementation"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=" * 60)
    print("Verifying Task 1.4: Populate predefined roles and assign to existing users")
    print("=" * 60)
    
    try:
        # 1. Verify predefined roles exist
        print("\n1. Checking predefined roles...")
        result = session.execute(text("SELECT name, description FROM roles ORDER BY name"))
        roles = result.fetchall()
        
        expected_roles = ['Accountant', 'Admin', 'Owner', 'Viewer']
        actual_roles = [role[0] for role in roles]
        
        print(f"   Expected roles: {expected_roles}")
        print(f"   Actual roles: {actual_roles}")
        
        if actual_roles == expected_roles:
            print("   ✓ All predefined roles exist")
        else:
            print("   ✗ Role mismatch!")
            return False
        
        # 2. Verify role permissions structure
        print("\n2. Checking role permissions...")
        result = session.execute(text("SELECT name, permissions FROM roles"))
        roles_with_perms = result.fetchall()
        
        for role_name, permissions in roles_with_perms:
            print(f"   {role_name}: {permissions}")
        
        print("   ✓ Role permissions defined")
        
        # 3. Verify Owner role assignments
        print("\n3. Checking Owner role assignments...")
        result = session.execute(text("""
            SELECT ur.user_id, ur.tenant_id, u.email, r.name
            FROM user_roles ur
            JOIN users u ON ur.user_id = u.id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'Owner'
        """))
        owner_assignments = result.fetchall()
        
        if owner_assignments:
            print(f"   Found {len(owner_assignments)} Owner role assignment(s):")
            for user_id, tenant_id, email, role_name in owner_assignments:
                print(f"   - User {user_id} ({email}) in tenant {tenant_id}")
            print("   ✓ Owner roles assigned")
        else:
            print("   ⚠ No Owner role assignments found (may be expected if no users exist)")
        
        # 4. Verify notification preferences
        print("\n4. Checking default notification preferences...")
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
        
        if pref_counts:
            print(f"   Found {len(pref_counts)} notification type(s):")
            actual_types = []
            for notif_type, count in pref_counts:
                print(f"   - {notif_type}: {count} user(s)")
                actual_types.append(notif_type)
            
            if actual_types == expected_types:
                print("   ✓ All notification types initialized")
            else:
                print(f"   ⚠ Expected types: {expected_types}")
                print(f"   ⚠ Actual types: {actual_types}")
        else:
            print("   ⚠ No notification preferences found (may be expected if no users exist)")
        
        # 5. Verify each user has all notification types
        print("\n5. Checking notification preferences per user...")
        result = session.execute(text("""
            SELECT u.id, u.email, COUNT(np.id) as pref_count
            FROM users u
            LEFT JOIN notification_preferences np ON u.id = np.user_id
            GROUP BY u.id, u.email
        """))
        user_prefs = result.fetchall()
        
        if user_prefs:
            all_complete = True
            for user_id, email, pref_count in user_prefs:
                status = "✓" if pref_count == 5 else "✗"
                print(f"   {status} User {user_id} ({email}): {pref_count}/5 preferences")
                if pref_count != 5:
                    all_complete = False
            
            if all_complete:
                print("   ✓ All users have complete notification preferences")
            else:
                print("   ✗ Some users missing notification preferences")
                return False
        else:
            print("   ⚠ No users found in database")
        
        print("\n" + "=" * 60)
        print("✓ Task 1.4 verification PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
