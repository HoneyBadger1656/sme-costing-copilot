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


class TestScheduledReportExecution:
    """Test scheduled report execution and Celery integration"""
    
    def test_execute_scheduled_report(self, test_db, accountant_auth_headers, client):
        """Test executing a scheduled report"""
        from app.services.scheduled_report_service import ScheduledReportService
        from app.models.models import ReportSchedule
        from datetime import datetime, timedelta
        
        # Create a schedule directly in the database
        org = test_db.query(Organization).first()
        user = test_db.query(User).filter(User.email == "accountant@example.com").first()
        
        # Use complete parameters for financial_statement template
        schedule = ReportSchedule(
            tenant_id=org.id,
            user_id=user.id,
            template_id="financial_statement",
            format="pdf",
            parameters={
                "period_type": "monthly",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31"
            },
            frequency="daily",
            recipients=["test@example.com"],
            next_run_at=datetime.utcnow() - timedelta(hours=1),  # Past due
            is_active=True
        )
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)
        
        # Execute the scheduled report
        scheduled_report_service = ScheduledReportService(test_db)
        result = scheduled_report_service.execute_scheduled_report(schedule.id)
        
        # Verify execution result
        assert result["status"] == "success"
        assert result["schedule_id"] == schedule.id
        assert "report" in result
        assert "next_run_at" in result
        
        # Verify schedule was updated
        test_db.refresh(schedule)
        assert schedule.last_run_at is not None
        assert schedule.next_run_at > datetime.utcnow()
    
    def test_execute_inactive_schedule_fails(self, test_db, accountant_auth_headers, client):
        """Test that executing an inactive schedule fails"""
        from app.services.scheduled_report_service import ScheduledReportService
        from app.models.models import ReportSchedule
        from datetime import datetime
        
        # Get org and user from the fixture setup
        org = test_db.query(Organization).first()
        user = test_db.query(User).filter(User.email == "accountant@example.com").first()
        
        schedule = ReportSchedule(
            tenant_id=org.id,
            user_id=user.id,
            template_id="financial_statement",
            format="pdf",
            parameters={
                "period_start": "2024-01-01",
                "period_end": "2024-12-31"
            },
            frequency="daily",
            recipients=["test@example.com"],
            next_run_at=datetime.utcnow(),
            is_active=False  # Inactive
        )
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)
        
        # Try to execute inactive schedule
        scheduled_report_service = ScheduledReportService(test_db)
        
        with pytest.raises(ValueError, match="is inactive"):
            scheduled_report_service.execute_scheduled_report(schedule.id)
    
    def test_execute_nonexistent_schedule_fails(self, test_db, accountant_auth_headers, client):
        """Test that executing a nonexistent schedule fails"""
        from app.services.scheduled_report_service import ScheduledReportService
        
        scheduled_report_service = ScheduledReportService(test_db)
        
        with pytest.raises(ValueError, match="not found"):
            scheduled_report_service.execute_scheduled_report(99999)
    
    def test_celery_beat_task_execution(self, test_db, accountant_auth_headers, client, monkeypatch):
        """Test Celery beat periodic task for executing due schedules"""
        from app.tasks import execute_due_scheduled_reports_task
        from app.models.models import ReportSchedule
        from datetime import datetime, timedelta
        
        # Get org and user from the fixture setup
        org = test_db.query(Organization).first()
        user = test_db.query(User).filter(User.email == "accountant@example.com").first()
        
        # Schedule 1: Due for execution
        schedule1 = ReportSchedule(
            tenant_id=org.id,
            user_id=user.id,
            template_id="financial_statement",
            format="pdf",
            parameters={
                "period_type": "monthly",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31"
            },
            frequency="daily",
            recipients=["test1@example.com"],
            next_run_at=datetime.utcnow() - timedelta(hours=1),  # Past due
            is_active=True
        )
        
        # Schedule 2: Not yet due
        schedule2 = ReportSchedule(
            tenant_id=org.id,
            user_id=user.id,
            template_id="costing_analysis",
            format="excel",
            parameters={},
            frequency="weekly",
            recipients=["test2@example.com"],
            next_run_at=datetime.utcnow() + timedelta(days=1),  # Future
            is_active=True
        )
        
        # Schedule 3: Inactive
        schedule3 = ReportSchedule(
            tenant_id=org.id,
            user_id=user.id,
            template_id="margin_analysis",
            format="csv",
            parameters={},
            frequency="monthly",
            recipients=["test3@example.com"],
            next_run_at=datetime.utcnow() - timedelta(hours=2),  # Past due but inactive
            is_active=False
        )
        
        test_db.add_all([schedule1, schedule2, schedule3])
        test_db.commit()
        
        # Store schedule IDs before they're detached
        schedule1_id = schedule1.id
        schedule2_id = schedule2.id
        schedule3_id = schedule3.id
        
        # Mock the email sending task
        email_task_called = []
        
        def mock_delay(**kwargs):
            email_task_called.append(kwargs)
        
        # Patch the email task
        from app import tasks
        
        class MockEmailTask:
            delay = staticmethod(mock_delay)
        
        monkeypatch.setattr(tasks, "send_scheduled_report_email_task", MockEmailTask())
        
        # Mock SessionLocal to use test_db
        def mock_session_local():
            return test_db
        
        monkeypatch.setattr("app.tasks.SessionLocal", mock_session_local)
        
        # Execute the periodic task - it returns a dict directly
        result = execute_due_scheduled_reports_task()
        
        # Verify results
        assert result["success"] is True
        assert result["executed"] == 1  # Only schedule1 should be executed
        assert result["failed"] == 0
        
        # Re-query schedules from database to get fresh instances
        schedule1_updated = test_db.query(ReportSchedule).filter(ReportSchedule.id == schedule1_id).first()
        schedule2_updated = test_db.query(ReportSchedule).filter(ReportSchedule.id == schedule2_id).first()
        schedule3_updated = test_db.query(ReportSchedule).filter(ReportSchedule.id == schedule3_id).first()
        
        # Verify schedule1 was updated
        assert schedule1_updated.last_run_at is not None
        assert schedule1_updated.next_run_at > datetime.utcnow()
        
        # Verify schedule2 was not executed (not due yet)
        assert schedule2_updated.last_run_at is None
        
        # Verify schedule3 was not executed (inactive)
        assert schedule3_updated.last_run_at is None
        
        # Verify email task was called
        assert len(email_task_called) == 1
        assert email_task_called[0]["schedule_id"] == schedule1_id
        assert email_task_called[0]["recipients"] == ["test1@example.com"]
    
    def test_schedule_execution_updates_next_run_time(self, test_db, accountant_auth_headers, client):
        """Test that schedule execution correctly updates next_run_at"""
        from app.services.scheduled_report_service import ScheduledReportService
        from app.models.models import ReportSchedule
        from datetime import datetime, timedelta
        
        # Get org and user from the fixture setup
        org = test_db.query(Organization).first()
        user = test_db.query(User).filter(User.email == "accountant@example.com").first()
        
        # Test daily frequency - set next_run_at to a past time that's after 9:00 AM
        # so the next run will be tomorrow at 9:00 AM (approximately 24 hours later)
        now = datetime.utcnow()
        # Set to yesterday at 10:00 AM
        past_run_time = now.replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(days=1)
        
        schedule_daily = ReportSchedule(
            tenant_id=org.id,
            user_id=user.id,
            template_id="financial_statement",
            format="pdf",
            parameters={
                "period_type": "monthly",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31"
            },
            frequency="daily",
            recipients=["test@example.com"],
            next_run_at=past_run_time,
            is_active=True
        )
        test_db.add(schedule_daily)
        test_db.commit()
        test_db.refresh(schedule_daily)
        
        original_next_run = schedule_daily.next_run_at
        
        # Execute the schedule
        scheduled_report_service = ScheduledReportService(test_db)
        result = scheduled_report_service.execute_scheduled_report(schedule_daily.id)
        
        # Verify next_run_at was updated
        # The new next_run_at should be at 9:00 AM on the next day
        test_db.refresh(schedule_daily)
        
        # Verify that next_run_at is in the future
        assert schedule_daily.next_run_at > datetime.utcnow()
        
        # Verify that next_run_at is set to 9:00 AM
        assert schedule_daily.next_run_at.hour == 9
        assert schedule_daily.next_run_at.minute == 0
        
        # Verify that it's later than the original next_run_at
        assert schedule_daily.next_run_at > original_next_run


class TestScheduledReportAuthorization:
    """Test authorization enforcement for scheduled reports"""
    
    def test_viewer_role_cannot_create_schedule(self, test_db, client, accountant_auth_headers):
        """Test that Viewer role cannot create scheduled reports"""
        # Get org from the fixture setup
        org = test_db.query(Organization).first()
        
        # Create viewer role and user
        viewer_role = Role(
            name="Viewer",
            description="Read-only access",
            permissions={"read": True}
        )
        test_db.add(viewer_role)
        test_db.commit()
        test_db.refresh(viewer_role)
        
        viewer_user = User(
            email="viewer@example.com",
            hashed_password=generate_password_hash("ViewerPass123"),
            full_name="Test Viewer",
            organization_id=org.id,
            role="viewer",
            is_active=True
        )
        test_db.add(viewer_user)
        test_db.commit()
        test_db.refresh(viewer_user)
        
        # Assign viewer role
        user_role = UserRole(
            user_id=viewer_user.id,
            role_id=viewer_role.id,
            tenant_id=org.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Login as viewer
        response = client.post(
            "/api/auth/login",
            data={"username": viewer_user.email, "password": "ViewerPass123"}
        )
        token = response.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {token}"}
        
        # Try to create schedule
        response = client.post(
            "/api/reports/schedules",
            headers=viewer_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {},
                "frequency": "daily",
                "recipients": ["test@example.com"]
            }
        )
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_accountant_can_manage_schedules(self, client, accountant_auth_headers):
        """Test that Accountant role can create, list, and delete schedules"""
        # Create schedule
        create_response = client.post(
            "/api/reports/schedules",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {},
                "frequency": "daily",
                "recipients": ["test@example.com"]
            }
        )
        assert create_response.status_code == 201
        schedule_id = create_response.json()["id"]
        
        # List schedules
        list_response = client.get(
            "/api/reports/schedules",
            headers=accountant_auth_headers
        )
        assert list_response.status_code == 200
        
        # Get specific schedule
        get_response = client.get(
            f"/api/reports/schedules/{schedule_id}",
            headers=accountant_auth_headers
        )
        assert get_response.status_code == 200
        
        # Delete schedule
        delete_response = client.delete(
            f"/api/reports/schedules/{schedule_id}",
            headers=accountant_auth_headers
        )
        assert delete_response.status_code == 204
    
    def test_tenant_isolation_for_schedules(self, test_db, client, accountant_auth_headers):
        """Test that users can only access schedules from their own tenant"""
        # Create second organization and user
        org2 = Organization(
            name="Second Organization",
            email="org2@example.com",
            subscription_status="trial"
        )
        test_db.add(org2)
        test_db.commit()
        test_db.refresh(org2)
        
        # Get or create accountant role
        accountant_role = test_db.query(Role).filter(Role.name == "Accountant").first()
        if not accountant_role:
            accountant_role = Role(
                name="Accountant",
                description="Access to financial data and reports",
                permissions={"financial": True, "reports": True}
            )
            test_db.add(accountant_role)
            test_db.commit()
            test_db.refresh(accountant_role)
        
        user2 = User(
            email="accountant2@example.com",
            hashed_password=generate_password_hash("Accountant2Pass123"),
            full_name="Second Accountant",
            organization_id=org2.id,
            role="accountant",
            is_active=True
        )
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user2)
        
        # Assign role
        user_role = UserRole(
            user_id=user2.id,
            role_id=accountant_role.id,
            tenant_id=org2.id
        )
        test_db.add(user_role)
        test_db.commit()
        
        # Login as second user
        response = client.post(
            "/api/auth/login",
            data={"username": user2.email, "password": "Accountant2Pass123"}
        )
        token = response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {token}"}
        
        # Create schedule for first user
        from app.models.models import ReportSchedule
        from datetime import datetime
        
        org1 = test_db.query(Organization).filter(Organization.name == "Test Organization").first()
        user1 = test_db.query(User).filter(User.email == "accountant@example.com").first()
        
        schedule1 = ReportSchedule(
            tenant_id=org1.id,
            user_id=user1.id,
            template_id="financial_statement",
            format="pdf",
            parameters={},
            frequency="daily",
            recipients=["test@example.com"],
            next_run_at=datetime.utcnow(),
            is_active=True
        )
        test_db.add(schedule1)
        test_db.commit()
        test_db.refresh(schedule1)
        
        # User2 should not be able to access schedule1
        response = client.get(
            f"/api/reports/schedules/{schedule1.id}",
            headers=user2_headers
        )
        assert response.status_code == 404
        
        # User2 should not be able to delete schedule1
        response = client.delete(
            f"/api/reports/schedules/{schedule1.id}",
            headers=user2_headers
        )
        assert response.status_code == 404
        
        # Verify schedule1 still exists
        test_db.refresh(schedule1)
        assert schedule1.is_active is True
