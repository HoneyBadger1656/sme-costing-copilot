# backend/tests/test_scheduled_report_tasks.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import ReportSchedule


class TestCeleryBeatConfiguration:
    """Tests for Celery beat schedule configuration"""
    
    def test_celery_beat_schedule_configured(self):
        """Test that Celery beat schedule is properly configured"""
        from app.celery_app import celery_app
        
        # Verify beat_schedule exists
        assert hasattr(celery_app.conf, 'beat_schedule')
        assert celery_app.conf.beat_schedule is not None
        
        # Verify scheduled reports task is configured
        assert 'execute-due-scheduled-reports' in celery_app.conf.beat_schedule
        
        schedule_config = celery_app.conf.beat_schedule['execute-due-scheduled-reports']
        
        # Verify task name
        assert schedule_config['task'] == 'execute_due_scheduled_reports'
        
        # Verify schedule (every 60 seconds)
        assert schedule_config['schedule'] == 60.0
        
        # Verify expiry option
        assert 'options' in schedule_config
        assert schedule_config['options']['expires'] == 55
    
    def test_celery_app_configuration(self):
        """Test that Celery app has correct configuration"""
        from app.celery_app import celery_app
        
        # Verify basic configuration
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.task_track_started is True


class TestScheduledReportTasksLogic:
    """Tests for scheduled report task logic (without Celery execution)"""
    
    def test_due_schedules_query_logic(self, test_db: Session):
        """Test the logic for querying due schedules"""
        # Create schedules with different states
        due_schedule = ReportSchedule(
            tenant_id=1,
            user_id=1,
            template_id="financial_statement",
            format="pdf",
            parameters={},
            frequency="daily",
            recipients=["test@example.com"],
            next_run_at=datetime.utcnow() - timedelta(minutes=5),
            is_active=True
        )
        
        future_schedule = ReportSchedule(
            tenant_id=1,
            user_id=1,
            template_id="costing_analysis",
            format="excel",
            parameters={},
            frequency="weekly",
            recipients=["test2@example.com"],
            next_run_at=datetime.utcnow() + timedelta(hours=1),
            is_active=True
        )
        
        inactive_schedule = ReportSchedule(
            tenant_id=1,
            user_id=1,
            template_id="margin_analysis",
            format="csv",
            parameters={},
            frequency="monthly",
            recipients=["test3@example.com"],
            next_run_at=datetime.utcnow() - timedelta(minutes=10),
            is_active=False
        )
        
        test_db.add_all([due_schedule, future_schedule, inactive_schedule])
        test_db.commit()
        
        # Query for due schedules (same logic as in the task)
        now = datetime.utcnow()
        due_schedules = test_db.query(ReportSchedule).filter(
            ReportSchedule.is_active == True,
            ReportSchedule.next_run_at <= now
        ).all()
        
        # Should only return the due and active schedule
        assert len(due_schedules) == 1
        assert due_schedules[0].id == due_schedule.id
        assert due_schedules[0].template_id == "financial_statement"
    
    def test_scheduled_report_service_integration(self, test_db: Session):
        """Test that scheduled report service can execute a schedule"""
        from app.services.scheduled_report_service import ScheduledReportService
        
        # Create a due schedule
        schedule = ReportSchedule(
            tenant_id=1,
            user_id=1,
            template_id="financial_statement",
            format="pdf",
            parameters={},
            frequency="daily",
            recipients=["test@example.com"],
            next_run_at=datetime.utcnow() - timedelta(minutes=5),
            is_active=True
        )
        test_db.add(schedule)
        test_db.commit()
        
        # Mock the report service to avoid actual report generation
        service = ScheduledReportService(test_db)
        
        with patch.object(service.report_service, 'generate_report') as mock_generate:
            mock_generate.return_value = {
                "task_id": "test-123",
                "file_name": "report.pdf",
                "file_size": 1024
            }
            
            # Execute the schedule
            result = service.execute_scheduled_report(schedule.id)
            
            # Verify result
            assert result["status"] == "success"
            assert result["schedule_id"] == schedule.id
            assert "next_run_at" in result
            
            # Verify schedule was updated
            test_db.refresh(schedule)
            assert schedule.last_run_at is not None
            assert schedule.next_run_at > datetime.utcnow()
    
    def test_task_functions_exist(self):
        """Test that the Celery task functions are defined"""
        from app import tasks
        
        # Verify task functions exist
        assert hasattr(tasks, 'execute_due_scheduled_reports_task')
        assert hasattr(tasks, 'send_scheduled_report_email_task')
        
        # Verify they are Celery tasks
        assert hasattr(tasks.execute_due_scheduled_reports_task, 'delay')
        assert hasattr(tasks.send_scheduled_report_email_task, 'delay')

