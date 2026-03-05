# Backend/tests/test_audit_trail_api.py

"""Integration tests for audit trail API endpoints"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import User, Organization, Role, UserRole, AuditLog


@pytest.fixture
def owner_role(test_db):
    """Create Owner role"""
    role = Role(
        name="Owner",
        description="Full system access including billing",
        permissions={"all": True, "billing": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def admin_role(test_db):
    """Create Admin role"""
    role = Role(
        name="Admin",
        description="All access except billing",
        permissions={"all": True, "billing": False}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def viewer_role(test_db):
    """Create Viewer role"""
    role = Role(
        name="Viewer",
        description="Read-only access",
        permissions={"read_only": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture
def owner_user(test_db, test_organization, owner_role):
    """Create a user with Owner role"""
    from werkzeug.security import generate_password_hash
    
    user = User(
        email="owner@example.com",
        hashed_password=generate_password_hash("OwnerPass123"),
        full_name="Owner User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Owner role
    user_role = UserRole(
        user_id=user.id,
        role_id=owner_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user


@pytest.fixture
def admin_user(test_db, test_organization, admin_role):
    """Create a user with Admin role"""
    from werkzeug.security import generate_password_hash
    
    user = User(
        email="admin@example.com",
        hashed_password=generate_password_hash("AdminPass123"),
        full_name="Admin User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Admin role
    user_role = UserRole(
        user_id=user.id,
        role_id=admin_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user


@pytest.fixture
def viewer_user(test_db, test_organization, viewer_role):
    """Create a user with Viewer role"""
    from werkzeug.security import generate_password_hash
    
    user = User(
        email="viewer@example.com",
        hashed_password=generate_password_hash("ViewerPass123"),
        full_name="Viewer User",
        organization_id=test_organization.id,
        role="viewer",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Viewer role
    user_role = UserRole(
        user_id=user.id,
        role_id=viewer_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user


@pytest.fixture
def owner_auth_headers(client, owner_user):
    """Get authentication headers for owner user"""
    response = client.post(
        "/api/auth/login",
        data={"username": owner_user.email, "password": "OwnerPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post(
        "/api/auth/login",
        data={"username": admin_user.email, "password": "AdminPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers(client, viewer_user):
    """Get authentication headers for viewer user"""
    response = client.post(
        "/api/auth/login",
        data={"username": viewer_user.email, "password": "ViewerPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_audit_logs(test_db, test_organization, owner_user, admin_user):
    """Create sample audit logs for testing"""
    logs = []
    
    # Create audit logs with different actions and tables
    base_time = datetime.utcnow() - timedelta(days=5)
    
    # Product CREATE logs
    for i in range(3):
        log = AuditLog(
            tenant_id=test_organization.id,
            user_id=owner_user.id,
            action="CREATE",
            table_name="products",
            record_id=i + 1,
            new_values={"name": f"Product {i+1}", "price": 100.0 * (i+1)},
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            created_at=base_time + timedelta(hours=i)
        )
        test_db.add(log)
        logs.append(log)
    
    # Product UPDATE logs
    for i in range(2):
        log = AuditLog(
            tenant_id=test_organization.id,
            user_id=admin_user.id,
            action="UPDATE",
            table_name="products",
            record_id=i + 1,
            old_values={"name": f"Product {i+1}", "price": 100.0 * (i+1)},
            new_values={"name": f"Updated Product {i+1}", "price": 150.0 * (i+1)},
            ip_address="192.168.1.2",
            user_agent="Test Browser",
            created_at=base_time + timedelta(hours=i+3)
        )
        test_db.add(log)
        logs.append(log)
    
    # Client CREATE logs
    for i in range(2):
        log = AuditLog(
            tenant_id=test_organization.id,
            user_id=owner_user.id,
            action="CREATE",
            table_name="clients",
            record_id=i + 1,
            new_values={"name": f"Client {i+1}", "email": f"client{i+1}@example.com"},
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            created_at=base_time + timedelta(hours=i+5)
        )
        test_db.add(log)
        logs.append(log)
    
    # Product DELETE log
    log = AuditLog(
        tenant_id=test_organization.id,
        user_id=admin_user.id,
        action="DELETE",
        table_name="products",
        record_id=3,
        old_values={"name": "Product 3", "price": 300.0},
        ip_address="192.168.1.2",
        user_agent="Test Browser",
        created_at=base_time + timedelta(hours=7)
    )
    test_db.add(log)
    logs.append(log)
    
    test_db.commit()
    return logs


class TestAuditLogQueryingAPI:
    """Test audit log querying with various filters"""
    
    def test_get_audit_logs_as_owner(self, client, owner_auth_headers, sample_audit_logs):
        """Test Owner can retrieve audit logs"""
        response = client.get(
            "/api/audit-logs",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        
        assert data["total"] == len(sample_audit_logs)
        assert len(data["logs"]) == len(sample_audit_logs)
        assert data["page"] == 1
        assert data["per_page"] == 50
    
    def test_get_audit_logs_as_admin(self, client, admin_auth_headers, sample_audit_logs):
        """Test Admin can retrieve audit logs"""
        response = client.get(
            "/api/audit-logs",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == len(sample_audit_logs)
        assert len(data["logs"]) > 0
    
    def test_get_audit_logs_as_viewer_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer cannot access audit logs (403 Forbidden)"""
        response = client.get(
            "/api/audit-logs",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_filter_by_table_name(self, client, owner_auth_headers, sample_audit_logs):
        """Test filtering audit logs by table name"""
        response = client.get(
            "/api/audit-logs?table_name=products",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return product logs (3 CREATE + 2 UPDATE + 1 DELETE = 6)
        assert data["total"] == 6
        for log in data["logs"]:
            assert log["table_name"] == "products"
    
    def test_filter_by_action(self, client, owner_auth_headers, sample_audit_logs):
        """Test filtering audit logs by action type"""
        response = client.get(
            "/api/audit-logs?action=CREATE",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 5 CREATE logs (3 products + 2 clients)
        assert data["total"] == 5
        for log in data["logs"]:
            assert log["action"] == "CREATE"
    
    def test_filter_by_user_id(self, client, owner_auth_headers, sample_audit_logs, owner_user):
        """Test filtering audit logs by user ID"""
        response = client.get(
            f"/api/audit-logs?user_id={owner_user.id}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return logs created by owner_user (3 products + 2 clients = 5)
        assert data["total"] == 5
        for log in data["logs"]:
            assert log["user_id"] == owner_user.id
            assert log["user_email"] == owner_user.email
    
    def test_filter_by_date_range(self, client, owner_auth_headers, sample_audit_logs):
        """Test filtering audit logs by date range"""
        # Get the first log's timestamp
        start_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        end_date = (datetime.utcnow() - timedelta(days=4, hours=20)).isoformat()
        
        response = client.get(
            f"/api/audit-logs?start_date={start_date}&end_date={end_date}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return logs within the date range
        assert data["total"] >= 0
        for log in data["logs"]:
            log_date = datetime.fromisoformat(log["created_at"].replace("Z", "+00:00"))
            assert log_date >= datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            assert log_date <= datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    
    def test_combined_filters(self, client, owner_auth_headers, sample_audit_logs, admin_user):
        """Test combining multiple filters"""
        response = client.get(
            f"/api/audit-logs?table_name=products&action=UPDATE&user_id={admin_user.id}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 2 UPDATE logs for products by admin_user
        assert data["total"] == 2
        for log in data["logs"]:
            assert log["table_name"] == "products"
            assert log["action"] == "UPDATE"
            assert log["user_id"] == admin_user.id


class TestAuditLogPagination:
    """Test pagination functionality"""
    
    def test_pagination_first_page(self, client, owner_auth_headers, sample_audit_logs):
        """Test retrieving first page of audit logs"""
        response = client.get(
            "/api/audit-logs?skip=0&limit=3",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["logs"]) == 3
        assert data["page"] == 1
        assert data["per_page"] == 3
        assert data["total"] == len(sample_audit_logs)
        assert data["pages"] == (len(sample_audit_logs) + 2) // 3
    
    def test_pagination_second_page(self, client, owner_auth_headers, sample_audit_logs):
        """Test retrieving second page of audit logs"""
        response = client.get(
            "/api/audit-logs?skip=3&limit=3",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["logs"]) == 3
        assert data["page"] == 2
        assert data["per_page"] == 3
    
    def test_pagination_limit_validation(self, client, owner_auth_headers, sample_audit_logs):
        """Test pagination limit validation (max 100)"""
        response = client.get(
            "/api/audit-logs?limit=150",
            headers=owner_auth_headers
        )
        
        # Should return 422 validation error for limit > 100
        assert response.status_code == 422
    
    def test_pagination_skip_validation(self, client, owner_auth_headers, sample_audit_logs):
        """Test pagination skip validation (must be >= 0)"""
        response = client.get(
            "/api/audit-logs?skip=-1",
            headers=owner_auth_headers
        )
        
        # Should return 422 validation error for negative skip
        assert response.status_code == 422


class TestAuditLogExport:
    """Test audit log export to CSV"""
    
    def test_export_csv_as_owner(self, client, owner_auth_headers, sample_audit_logs):
        """Test Owner can export audit logs to CSV"""
        response = client.get(
            "/api/audit-logs/export?format=csv",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "audit_logs_" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]
        
        # Verify CSV content
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        
        # Should have header + data rows
        assert len(lines) > 1
        
        # Verify header
        header = lines[0]
        assert "id" in header
        assert "created_at" in header
        assert "user_email" in header
        assert "action" in header
        assert "table_name" in header
        assert "record_id" in header
    
    def test_export_csv_as_admin(self, client, admin_auth_headers, sample_audit_logs):
        """Test Admin can export audit logs to CSV"""
        response = client.get(
            "/api/audit-logs/export?format=csv",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_csv_as_viewer_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer cannot export audit logs (403 Forbidden)"""
        response = client.get(
            "/api/audit-logs/export?format=csv",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_export_csv_with_filters(self, client, owner_auth_headers, sample_audit_logs):
        """Test exporting filtered audit logs to CSV"""
        response = client.get(
            "/api/audit-logs/export?format=csv&table_name=products&action=CREATE",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify filtered CSV content
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        
        # Should have header + 3 CREATE product logs
        assert len(lines) == 4  # 1 header + 3 data rows
        
        # Verify all rows contain products and CREATE
        for line in lines[1:]:  # Skip header
            assert "products" in line
            assert "CREATE" in line
    
    def test_export_unsupported_format(self, client, owner_auth_headers, sample_audit_logs):
        """Test exporting with unsupported format returns error"""
        response = client.get(
            "/api/audit-logs/export?format=json",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 400
        assert "Only CSV format is currently supported" in response.json()["detail"]


class TestAuditLogAuthorization:
    """Test authorization enforcement (Owner/Admin only)"""
    
    def test_unauthenticated_access_denied(self, client, sample_audit_logs):
        """Test unauthenticated users cannot access audit logs"""
        response = client.get("/api/audit-logs")
        
        assert response.status_code == 401
    
    def test_viewer_get_audit_logs_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer role cannot access GET /api/audit-logs"""
        response = client.get(
            "/api/audit-logs",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_viewer_export_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer role cannot access GET /api/audit-logs/export"""
        response = client.get(
            "/api/audit-logs/export",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_viewer_record_history_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer role cannot access record history"""
        response = client.get(
            "/api/audit-logs/record/products/1",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403


class TestAuditLogTenantIsolation:
    """Test tenant isolation - users can only see their tenant's audit logs"""
    
    def test_tenant_isolation(self, test_db, client, owner_role):
        """Test users can only see audit logs from their own tenant"""
        from werkzeug.security import generate_password_hash
        
        # Create second organization
        org2 = Organization(
            name="Second Organization",
            email="org2@example.com",
            subscription_status="trial"
        )
        test_db.add(org2)
        test_db.commit()
        test_db.refresh(org2)
        
        # Create user in second organization
        user2 = User(
            email="owner2@example.com",
            hashed_password=generate_password_hash("Owner2Pass123"),
            full_name="Owner 2",
            organization_id=org2.id,
            role="admin",
            is_active=True
        )
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user2)
        
        # Assign Owner role to user2
        user_role2 = UserRole(
            user_id=user2.id,
            role_id=owner_role.id,
            tenant_id=org2.id
        )
        test_db.add(user_role2)
        test_db.commit()
        
        # Create audit logs for org2
        log_org2 = AuditLog(
            tenant_id=org2.id,
            user_id=user2.id,
            action="CREATE",
            table_name="products",
            record_id=999,
            new_values={"name": "Org2 Product"},
            ip_address="10.0.0.1",
            user_agent="Test Browser"
        )
        test_db.add(log_org2)
        test_db.commit()
        
        # Login as user2
        response = client.post(
            "/api/auth/login",
            data={"username": user2.email, "password": "Owner2Pass123"}
        )
        token2 = response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Get audit logs for user2
        response = client.get(
            "/api/audit-logs",
            headers=headers2
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only see logs from org2
        assert data["total"] == 1
        assert data["logs"][0]["tenant_id"] == org2.id
        assert data["logs"][0]["record_id"] == 999


class TestAuditLogRecordHistory:
    """Test record history endpoint"""
    
    def test_get_record_history(self, client, owner_auth_headers, sample_audit_logs):
        """Test retrieving audit history for a specific record"""
        response = client.get(
            "/api/audit-logs/record/products/1",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "table_name" in data
        assert "record_id" in data
        assert "history" in data
        assert "count" in data
        
        assert data["table_name"] == "products"
        assert data["record_id"] == 1
        
        # Should have CREATE and UPDATE logs for product 1
        assert data["count"] >= 2
        
        # Verify logs are ordered by created_at desc (newest first)
        if len(data["history"]) > 1:
            for i in range(len(data["history"]) - 1):
                current_time = datetime.fromisoformat(data["history"][i]["created_at"].replace("Z", "+00:00"))
                next_time = datetime.fromisoformat(data["history"][i+1]["created_at"].replace("Z", "+00:00"))
                assert current_time >= next_time
    
    def test_get_record_history_as_admin(self, client, admin_auth_headers, sample_audit_logs):
        """Test Admin can retrieve record history"""
        response = client.get(
            "/api/audit-logs/record/products/1",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 0
    
    def test_get_record_history_as_viewer_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer cannot retrieve record history"""
        response = client.get(
            "/api/audit-logs/record/products/1",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403


class TestAuditLogStatistics:
    """Test audit log statistics endpoint"""
    
    def test_get_audit_statistics(self, client, owner_auth_headers, sample_audit_logs):
        """Test retrieving audit statistics"""
        response = client.get(
            "/api/audit-logs/statistics",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_logs" in data
        assert "create_count" in data
        assert "update_count" in data
        assert "delete_count" in data
        assert "top_users" in data
        assert "period" in data
        
        # Verify counts
        assert data["total_logs"] == len(sample_audit_logs)
        assert data["create_count"] == 5  # 3 products + 2 clients
        assert data["update_count"] == 2  # 2 product updates
        assert data["delete_count"] == 1  # 1 product delete
        
        # Verify top users
        assert len(data["top_users"]) > 0
        for user_stat in data["top_users"]:
            assert "user_id" in user_stat
            assert "email" in user_stat
            assert "action_count" in user_stat
    
    def test_get_audit_statistics_with_date_range(self, client, owner_auth_headers, sample_audit_logs):
        """Test retrieving audit statistics with date range filter"""
        start_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(
            f"/api/audit-logs/statistics?start_date={start_date}&end_date={end_date}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period"]["start_date"] is not None
        assert data["period"]["end_date"] is not None
    
    def test_get_audit_statistics_as_admin(self, client, admin_auth_headers, sample_audit_logs):
        """Test Admin can retrieve audit statistics"""
        response = client.get(
            "/api/audit-logs/statistics",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
    
    def test_get_audit_statistics_as_viewer_denied(self, client, viewer_auth_headers, sample_audit_logs):
        """Test Viewer cannot retrieve audit statistics"""
        response = client.get(
            "/api/audit-logs/statistics",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403


class TestAuditLogDataIntegrity:
    """Test audit log data integrity and content"""
    
    def test_audit_log_contains_user_email(self, client, owner_auth_headers, sample_audit_logs, owner_user):
        """Test audit logs include user email for easy identification"""
        response = client.get(
            f"/api/audit-logs?user_id={owner_user.id}",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for log in data["logs"]:
            if log["user_id"] == owner_user.id:
                assert log["user_email"] == owner_user.email
    
    def test_audit_log_contains_ip_and_user_agent(self, client, owner_auth_headers, sample_audit_logs):
        """Test audit logs include IP address and user agent"""
        response = client.get(
            "/api/audit-logs",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for log in data["logs"]:
            assert "ip_address" in log
            assert "user_agent" in log
    
    def test_audit_log_timestamps_are_iso_format(self, client, owner_auth_headers, sample_audit_logs):
        """Test audit log timestamps are in ISO 8601 format"""
        response = client.get(
            "/api/audit-logs",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for log in data["logs"]:
            # Should be able to parse as ISO datetime
            created_at = log["created_at"]
            assert created_at is not None
            # Verify it's a valid ISO format
            datetime.fromisoformat(created_at.replace("Z", "+00:00"))
