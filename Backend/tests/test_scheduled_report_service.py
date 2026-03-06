# Backend/tests/test_scheduled_report_service.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.scheduled_report_service import ScheduledReportService
from app.models.models import ReportSchedule


class TestScheduledReportService:
    """Test scheduled report service functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a ScheduledReportService instance."""
        return ScheduledReportService(mock_db)
    
    def test_create_schedule_daily(self, service, mock_db):
        """Test creating a daily scheduled report."""
        template_id = "financial_statement"
        format = "pdf"
        parameters = {"period_start": "2024-01-01", "period_end": "2024-12-31"}
        frequency = "daily"
        recipients = ["user@example.com"]
        user_id = 1
        tenant_id = 1
        
        schedule = service.create_schedule(
            template_id=template_id,
            format=format,
            parameters=parameters,
            frequency=frequency,
            recipients=recipients,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Verify db.add was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_schedule_weekly(self, service, mock_db):
        """Test creating a weekly scheduled report."""
        schedule = service.create_schedule(
            template_id="costing_analysis",
            format="excel",
            parameters={},
            frequency="weekly",
            recipients=["user@example.com"],
            user_id=1,
            tenant_id=1
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_schedule_monthly(self, service, mock_db):
        """Test creating a monthly scheduled report."""
        schedule = service.create_schedule(
            template_id="margin_analysis",
            format="csv",
            parameters={},
            frequency="monthly",
            recipients=["user@example.com"],
            user_id=1,
            tenant_id=1
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_schedule_invalid_frequency(self, service, mock_db):
        """Test creating a schedule with invalid frequency."""
        with pytest.raises(ValueError, match="Invalid frequency"):
            service.create_schedule(
                template_id="financial_statement",
                format="pdf",
                parameters={},
                frequency="hourly",  # Invalid
                recipients=["user@example.com"],
                user_id=1,
                tenant_id=1
            )
    
    def test_create_schedule_invalid_email(self, service, mock_db):
        """Test creating a schedule with invalid email."""
        with pytest.raises(ValueError, match="Invalid email address"):
            service.create_schedule(
                template_id="financial_statement",
                format="pdf",
                parameters={},
                frequency="daily",
                recipients=["invalid-email"],  # Invalid email
                user_id=1,
                tenant_id=1
            )
    
    def test_create_schedule_empty_recipients(self, service, mock_db):
        """Test creating a schedule with empty recipients."""
        with pytest.raises(ValueError, match="Recipients must be a non-empty list"):
            service.create_schedule(
                template_id="financial_statement",
                format="pdf",
                parameters={},
                frequency="daily",
                recipients=[],  # Empty
                user_id=1,
                tenant_id=1
            )
    
    def test_validate_cron_expression_valid(self, service):
        """Test validating a valid cron expression."""
        # Should not raise
        service._validate_cron_expression("0 9 * * *")
        service._validate_cron_expression("0 0 1 * *")
        service._validate_cron_expression("*/15 * * * *")
    
    def test_validate_cron_expression_invalid(self, service):
        """Test validating an invalid cron expression."""
        with pytest.raises(ValueError, match="must have 5 or 6 fields"):
            service._validate_cron_expression("0 9 *")  # Too few fields
        
        with pytest.raises(ValueError, match="Invalid characters"):
            service._validate_cron_expression("0 9 * * * invalid")
    
    def test_is_valid_email(self, service):
        """Test email validation."""
        assert service._is_valid_email("user@example.com") is True
        assert service._is_valid_email("test.user+tag@domain.co.uk") is True
        assert service._is_valid_email("invalid-email") is False
        assert service._is_valid_email("@example.com") is False
        assert service._is_valid_email("user@") is False
    
    def test_get_schedules_all(self, service, mock_db):
        """Test getting all schedules for a tenant."""
        tenant_id = 1
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        schedules = service.get_schedules(tenant_id=tenant_id)
        
        assert schedules == []
        mock_db.query.assert_called_once_with(ReportSchedule)
    
    def test_get_schedules_by_user(self, service, mock_db):
        """Test getting schedules filtered by user."""
        tenant_id = 1
        user_id = 1
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        schedules = service.get_schedules(tenant_id=tenant_id, user_id=user_id)
        
        assert schedules == []
    
    def test_get_schedule_by_id(self, service, mock_db):
        """Test getting a specific schedule by ID."""
        schedule_id = 1
        tenant_id = 1
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        schedule = service.get_schedule_by_id(schedule_id=schedule_id, tenant_id=tenant_id)
        
        assert schedule is None
    
    def test_delete_schedule_success(self, service, mock_db):
        """Test deleting a schedule."""
        schedule_id = 1
        tenant_id = 1
        
        # Mock schedule
        mock_schedule = Mock(spec=ReportSchedule)
        mock_schedule.is_active = True
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_schedule
        
        result = service.delete_schedule(schedule_id=schedule_id, tenant_id=tenant_id)
        
        assert result is True
        assert mock_schedule.is_active is False
        mock_db.commit.assert_called_once()
    
    def test_delete_schedule_not_found(self, service, mock_db):
        """Test deleting a non-existent schedule."""
        schedule_id = 999
        tenant_id = 1
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = service.delete_schedule(schedule_id=schedule_id, tenant_id=tenant_id)
        
        assert result is False
    
    @patch('app.services.scheduled_report_service.ReportService')
    def test_execute_scheduled_report_success(self, mock_report_service_class, service, mock_db):
        """Test executing a scheduled report."""
        schedule_id = 1
        
        # Mock schedule
        mock_schedule = Mock(spec=ReportSchedule)
        mock_schedule.id = schedule_id
        mock_schedule.template_id = "financial_statement"
        mock_schedule.format = "pdf"
        mock_schedule.parameters = {}
        mock_schedule.tenant_id = 1
        mock_schedule.user_id = 1
        mock_schedule.frequency = "daily"
        mock_schedule.cron_expression = None
        mock_schedule.is_active = True
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_schedule
        
        # Mock report service
        mock_report_service = Mock()
        mock_report_service.generate_report.return_value = {
            "task_id": "test-task-id",
            "status": "completed"
        }
        service.report_service = mock_report_service
        
        result = service.execute_scheduled_report(schedule_id=schedule_id)
        
        assert result["status"] == "success"
        assert result["schedule_id"] == schedule_id
        assert "next_run_at" in result
        mock_report_service.generate_report.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_execute_scheduled_report_not_found(self, service, mock_db):
        """Test executing a non-existent schedule."""
        schedule_id = 999
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        with pytest.raises(ValueError, match="not found"):
            service.execute_scheduled_report(schedule_id=schedule_id)
    
    def test_execute_scheduled_report_inactive(self, service, mock_db):
        """Test executing an inactive schedule."""
        schedule_id = 1
        
        # Mock inactive schedule
        mock_schedule = Mock(spec=ReportSchedule)
        mock_schedule.id = schedule_id
        mock_schedule.is_active = False
        
        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_schedule
        
        with pytest.raises(ValueError, match="is inactive"):
            service.execute_scheduled_report(schedule_id=schedule_id)
    
    def test_calculate_next_run_daily(self, service):
        """Test calculating next run time for daily frequency."""
        next_run = service._calculate_next_run("daily")
        
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert next_run > datetime.utcnow()
    
    def test_calculate_next_run_weekly(self, service):
        """Test calculating next run time for weekly frequency."""
        next_run = service._calculate_next_run("weekly")
        
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert next_run.weekday() == 0  # Monday
        assert next_run > datetime.utcnow()
    
    def test_calculate_next_run_monthly(self, service):
        """Test calculating next run time for monthly frequency."""
        next_run = service._calculate_next_run("monthly")
        
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert next_run.day == 1  # First of month
        assert next_run > datetime.utcnow()
