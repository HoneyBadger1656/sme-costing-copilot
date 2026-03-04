#!/usr/bin/env python3
"""Integration tests for endpoint authorization"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.models.models import User, Organization, Role, UserRole
from app.api.auth import get_password_hash
import uuid

client = TestClient(app)

@pytest.fixture
def test_db():
    """Create test database session"""
    from app.core.database import engine, Base
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()

@pytest.fixture
def test_org(test_db):
    """Create test organization"""
    org = Organization(
        name="Test Organization",
        email="test@org.com",
        subscription_status="trial"
    )
    test_db.add(org)
    test_db.flush()
    return org

@pytest.fixture
def test_roles(test_db):
    """Create test roles"""
    roles = {
        "Owner": Role(name="Owner", description="Full access", permissions=["*"]),
        "Admin": Role(name="Admin", description="Admin access", permissions=["user_management", "billing", "reports", "costing", "financial", "scenarios"]),
        "Accountant": Role(name="Accountant", description="Financial access", permissions=["costing", "financial", "scenarios", "reports"]),
        "Viewer": Role(name="Viewer", description="Read-only access", permissions=["reports"])
    }
    
    for role in roles.values():
        test_db.add(role)
    test_db.flush()
    return roles

@pytest.fixture
def test_users(test_db, test_org, test_roles):
    """Create test users with different roles"""
    users = {}
    
    # Create users
    for role_name in ["Owner", "Admin", "Accountant", "Viewer"]:
        user = User(
            email=f"{role_name.lower()}@test.com",
            hashed_password=get_password_hash("password123"),
            full_name=f"Test {role_name}",
            organization_id=test_org.id,
            role=role_name.lower()
        )
        test_db.add(user)
        test_db.flush()
        
        # Assign RBAC role
        user_role = UserRole(
            user_id=user.id,
            role_id=test_roles[role_name].id,
            tenant_id=test_org.id,
            assigned_by=user.id
        )
        test_db.add(user_role)
        users[role_name.lower()] = user
    
    test_db.commit()
    return users

def get_auth_headers(email: str, password: str = "password123"):
    """Get authentication headers for user"""
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

class TestEndpointAuthorization:
    """Test authorization on various endpoints"""
    
    def test_costing_endpoints_require_accountant_plus(self, test_users):
        """Test costing endpoints require Accountant+ access"""
        test_data = {
            "raw_material_cost": 25,
            "labour_cost_per_unit": 22,
            "overhead_percentage": 10,
            "target_margin_percentage": 20,
            "tax_rate": 18
        }
        
        # Viewer should be denied
        headers = get_auth_headers("viewer@test.com")
        response = client.post("/api/costing/calculate-product-cost", json=test_data, headers=headers)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
        
        # Accountant should be allowed
        headers = get_auth_headers("accountant@test.com")
        response = client.post("/api/costing/calculate-product-cost", json=test_data, headers=headers)
        assert response.status_code == 200
        
        # Admin should be allowed
        headers = get_auth_headers("admin@test.com")
        response = client.post("/api/costing/calculate-product-cost", json=test_data, headers=headers)
        assert response.status_code == 200
        
        # Owner should be allowed
        headers = get_auth_headers("owner@test.com")
        response = client.post("/api/costing/calculate-product-cost", json=test_data, headers=headers)
        assert response.status_code == 200
    
    def test_order_evaluation_requires_accountant_plus(self, test_users):
        """Test order evaluation requires Accountant+ access"""
        test_data = {
            "customer_name": "Test Customer",
            "product_id": 1,
            "selling_price": 100,
            "cost_price": 25,
            "quantity": 100,
            "credit_days": 30
        }
        
        # Viewer should be denied
        headers = get_auth_headers("viewer@test.com")
        response = client.post("/api/costing/evaluate-order", json=test_data, headers=headers)
        assert response.status_code == 403
        
        # Accountant should be allowed
        headers = get_auth_headers("accountant@test.com")
        response = client.post("/api/costing/evaluate-order", json=test_data, headers=headers)
        assert response.status_code == 200
    
    def test_audit_logs_require_admin_plus(self, test_users):
        """Test audit logs require Admin+ access"""
        # Viewer should be denied
        headers = get_auth_headers("viewer@test.com")
        response = client.get("/api/audit-logs", headers=headers)
        assert response.status_code == 403
        
        # Accountant should be denied
        headers = get_auth_headers("accountant@test.com")
        response = client.get("/api/audit-logs", headers=headers)
        assert response.status_code == 403
        
        # Admin should be allowed
        headers = get_auth_headers("admin@test.com")
        response = client.get("/api/audit-logs", headers=headers)
        assert response.status_code == 200
        
        # Owner should be allowed
        headers = get_auth_headers("owner@test.com")
        response = client.get("/api/audit-logs", headers=headers)
        assert response.status_code == 200
    
    def test_role_management_requires_admin_plus(self, test_users):
        """Test role management requires Admin+ access"""
        # Viewer should be denied
        headers = get_auth_headers("viewer@test.com")
        response = client.get("/api/roles/", headers=headers)
        assert response.status_code == 403
        
        # Accountant should be denied
        headers = get_auth_headers("accountant@test.com")
        response = client.get("/api/roles/", headers=headers)
        assert response.status_code == 403
        
        # Admin should be allowed
        headers = get_auth_headers("admin@test.com")
        response = client.get("/api/roles/", headers=headers)
        assert response.status_code == 200
        
        # Owner should be allowed
        headers = get_auth_headers("owner@test.com")
        response = client.get("/api/roles/", headers=headers)
        assert response.status_code == 200
    
    def test_viewer_has_read_only_access(self, test_users):
        """Test Viewer role has read-only access where permitted"""
        headers = get_auth_headers("viewer@test.com")
        
        # Should be able to read clients (if any exist)
        response = client.get("/api/clients/", headers=headers)
        assert response.status_code == 200
        
        # Should be able to read products (if any exist)
        response = client.get("/api/products/", headers=headers)
        assert response.status_code == 200
        
        # Should NOT be able to create clients
        test_data = {
            "business_name": "Test Business",
            "email": "test@business.com",
            "industry": "manufacturing"
        }
        response = client.post("/api/clients/", json=test_data, headers=headers)
        # This might be 403 or 422 depending on endpoint protection
        assert response.status_code in [403, 422]
    
    def test_unauthenticated_requests_denied(self):
        """Test unauthenticated requests are denied"""
        endpoints = [
            ("/api/clients/", "GET"),
            ("/api/products/", "GET"),
            ("/api/costing/calculate-product-cost", "POST"),
            ("/api/audit-logs", "GET"),
            ("/api/roles/", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]
    
    def test_financial_endpoints_require_accountant_plus(self, test_users):
        """Test financial endpoints require Accountant+ access"""
        # Viewer should be denied
        headers = get_auth_headers("viewer@test.com")
        response = client.get("/api/financials/formulas", headers=headers)
        assert response.status_code == 403
        
        # Accountant should be allowed
        headers = get_auth_headers("accountant@test.com")
        response = client.get("/api/financials/formulas", headers=headers)
        assert response.status_code == 200
    
    def test_scenario_endpoints_require_accountant_plus(self, test_users):
        """Test scenario endpoints require Accountant+ access"""
        # Viewer should be denied
        headers = get_auth_headers("viewer@test.com")
        response = client.get("/api/scenarios?client_id=1", headers=headers)
        assert response.status_code == 403
        
        # Accountant should be allowed
        headers = get_auth_headers("accountant@test.com")
        response = client.get("/api/scenarios?client_id=1", headers=headers)
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])