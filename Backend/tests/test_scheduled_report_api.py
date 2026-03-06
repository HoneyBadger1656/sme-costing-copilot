# backend/tests/test_scheduled_report_api.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from app.main import app
from app.core.database import Base, get_db
from app.models.models import User, Organization, Role, UserRole


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_scheduled_reports.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def accountant_role(test_db):
    """Create Accountant role"""
    role = Role(
        name="Accountant",
        description="Access to financial data and reports",
        permissions={"financial": True, "reports": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role


@pytest.fixture(scope="function")
def accountant_auth_headers(test_db, client, accountant_role):
    """Create an accountant user and return auth headers"""
    # Create organization
    org = Organization(
        name="Test Organization",
        email="test@example.com",
        subscription_status="trial"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    
    # Create user
    user = User(
        email="accountant@example.com",
        hashed_password=generate_password_hash("AccountantPass123"),
        full_name="Test Accountant",
        organization_id=org.id,
        role="accountant",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign role
    user_role = UserRole(
        user_id=user.id,
        role_id=accountant_role.id,
        tenant_id=org.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "AccountantPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestScheduledReportEndpoints:
    """Test scheduled report API endpoints"""
    
    def test_create_schedule(self, client, accountant_auth_headers):
        """Test creating a scheduled report"""
        response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {
                    "period_type": "monthly",
                    "period_start": "2024-01-01",
                    "period_end": "2024-12-31"
                },
                "frequency": "daily",
                "recipients": ["user@example.com", "manager@example.com"]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["template_id"] == "financial_statement"
        assert data["format"] == "pdf"
        assert data["frequency"] == "daily"
        assert len(data["recipients"]) == 2
        assert data["is_active"] is True
        assert "id" in data
        assert "next_run_at" in data
    
    def test_create_schedule_with_invalid_frequency(self, client, accountant_auth_headers):
        """Test creating schedule with invalid frequency"""
        response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {},
                "frequency": "invalid_frequency",
                "recipients": ["user@example.com"]
            }
        )
        
        assert response.status_code == 400
        assert "Invalid frequency" in response.json()["detail"]
    
    def test_create_schedule_with_invalid_email(self, client, accountant_auth_headers):
        """Test creating schedule with invalid email"""
        response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {},
                "frequency": "daily",
                "recipients": ["invalid-email"]
            }
        )
        
        assert response.status_code == 400
        assert "Invalid email address" in response.json()["detail"]
    
    def test_list_schedules(self, client, accountant_auth_headers):
        """Test listing scheduled reports"""
        # Create a schedule first
        create_response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "excel",
                "parameters": {},
                "frequency": "weekly",
                "recipients": ["user@example.com"]
            }
        )
        assert create_response.status_code == 201
        
        # List schedules
        response = client.get(
            "/api/reports/schedules",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["template_id"] == "costing_analysis"
        assert data[0]["format"] == "excel"
    
    def test_get_schedule_by_id(self, client, accountant_auth_headers):
        """Test getting a specific schedule by ID"""
        # Create a schedule first
        create_response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "margin_analysis",
                "format": "csv",
                "parameters": {},
                "frequency": "monthly",
                "recipients": ["user@example.com"]
            }
        )
        assert create_response.status_code == 201
        schedule_id = create_response.json()["id"]
        
        # Get schedule by ID
        response = client.get(
            f"/api/reports/schedules/{schedule_id}",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule_id
        assert data["template_id"] == "margin_analysis"
        assert data["format"] == "csv"
        assert data["frequency"] == "monthly"
    
    def test_get_nonexistent_schedule(self, client, accountant_auth_headers):
        """Test getting a schedule that doesn't exist"""
        response = client.get(
            "/api/reports/schedules/99999",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_schedule(self, client, accountant_auth_headers):
        """Test deleting a scheduled report"""
        # Create a schedule first
        create_response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "receivables_report",
                "format": "pdf",
                "parameters": {},
                "frequency": "daily",
                "recipients": ["user@example.com"]
            }
        )
        assert create_response.status_code == 201
        schedule_id = create_response.json()["id"]
        
        # Delete the schedule
        response = client.delete(
            f"/api/reports/schedules/{schedule_id}",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted (should not appear in active schedules)
        list_response = client.get(
            "/api/reports/schedules",
            headers=accountant_auth_headers
        )
        schedules = list_response.json()
        schedule_ids = [s["id"] for s in schedules]
        assert schedule_id not in schedule_ids
    
    def test_delete_nonexistent_schedule(self, client, accountant_auth_headers):
        """Test deleting a schedule that doesn't exist"""
        response = client.delete(
            "/api/reports/schedules/99999",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_schedule_requires_authentication(self, client):
        """Test that scheduled report endpoints require authentication"""
        # Try to create without auth
        response = client.post(
            "/api/reports/schedules",
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {},
                "frequency": "daily",
                "recipients": ["user@example.com"]
            }
        )
        assert response.status_code == 401
        
        # Try to list without auth
        response = client.get("/api/reports/schedules")
        assert response.status_code == 401
        
        # Try to delete without auth
        response = client.delete("/api/reports/schedules/1")
        assert response.status_code == 401
