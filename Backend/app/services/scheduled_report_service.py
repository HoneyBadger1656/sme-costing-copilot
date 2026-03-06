# backend/app/services/scheduled_report_service.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

from app.models.models import ReportSchedule
from app.services.report_service import ReportService
from app.utils.validation import validate_email_list, ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class ScheduledReportService:
    """Service for managing scheduled report operations"""
    
    # Valid frequency values
    VALID_FREQUENCIES = ["daily", "weekly", "monthly"]
    
    def __init__(self, db: Session):
        self.db = db
        self.report_service = ReportService(db)
    
    def create_schedule(
        self,
        template_id: str,
        format: str,
        parameters: Dict[str, Any],
        frequency: str,
        recipients: List[str],
        user_id: int,
        tenant_id: int,
        cron_expression: Optional[str] = None
    ) -> ReportSchedule:
        """
        Create a new scheduled report.
        
        Args:
            template_id: Report template ID
            format: Output format (pdf, excel, csv)
            parameters: Report-specific parameters
            frequency: Schedule frequency (daily, weekly, monthly)
            recipients: List of email addresses
            user_id: User ID creating the schedule
            tenant_id: Tenant ID
            cron_expression: Optional cron expression for custom schedules
        
        Returns:
            Created ReportSchedule instance
        
        Raises:
            ValueError: If validation fails
        """
        # Validate frequency
        if frequency not in self.VALID_FREQUENCIES:
            raise ValueError(
                f"Invalid frequency '{frequency}'. Must be one of: {', '.join(self.VALID_FREQUENCIES)}"
            )
        
        # Validate cron expression if provided
        if cron_expression:
            self._validate_cron_expression(cron_expression)
        
        # Validate recipients using secure email validation (Requirement 30.4)
        try:
            validated_recipients = validate_email_list(recipients, max_recipients=100)
        except ValidationError as e:
            logger.warning(
                "scheduled_report_email_validation_failed",
                error=str(e),
                tenant_id=tenant_id,
                user_id=user_id
            )
            raise ValueError(f"Invalid recipient email addresses: {e}")
        
        # Calculate next run time
        next_run_at = self._calculate_next_run(frequency, cron_expression)
        
        # Create schedule with validated recipients
        schedule = ReportSchedule(
            tenant_id=tenant_id,
            user_id=user_id,
            template_id=template_id,
            format=format,
            parameters=parameters or {},
            frequency=frequency,
            cron_expression=cron_expression,
            recipients=validated_recipients,
            next_run_at=next_run_at,
            is_active=True
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(
            "scheduled_report_created",
            schedule_id=schedule.id,
            template_id=template_id,
            frequency=frequency,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return schedule
    
    def get_schedules(
        self,
        tenant_id: int,
        user_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[ReportSchedule]:
        """
        Get scheduled reports for a tenant.
        
        Args:
            tenant_id: Tenant ID
            user_id: Optional user ID to filter by user
            include_inactive: Whether to include inactive schedules
        
        Returns:
            List of ReportSchedule instances
        """
        query = self.db.query(ReportSchedule).filter(
            ReportSchedule.tenant_id == tenant_id
        )
        
        if user_id is not None:
            query = query.filter(ReportSchedule.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(ReportSchedule.is_active == True)
        
        return query.order_by(ReportSchedule.next_run_at).all()
    
    def get_schedule_by_id(
        self,
        schedule_id: int,
        tenant_id: int
    ) -> Optional[ReportSchedule]:
        """
        Get a specific schedule by ID with tenant isolation.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID
        
        Returns:
            ReportSchedule instance or None
        """
        return self.db.query(ReportSchedule).filter(
            ReportSchedule.id == schedule_id,
            ReportSchedule.tenant_id == tenant_id
        ).first()
    
    def delete_schedule(
        self,
        schedule_id: int,
        tenant_id: int
    ) -> bool:
        """
        Delete (deactivate) a scheduled report.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID for tenant isolation
        
        Returns:
            True if deleted, False if not found
        """
        schedule = self.get_schedule_by_id(schedule_id, tenant_id)
        
        if not schedule:
            return False
        
        schedule.is_active = False
        self.db.commit()
        
        logger.info(
            "scheduled_report_deleted",
            schedule_id=schedule_id,
            tenant_id=tenant_id
        )
        
        return True
    
    def execute_scheduled_report(
        self,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Execute a scheduled report and update next_run_at.
        
        Args:
            schedule_id: Schedule ID
        
        Returns:
            Report generation result
        
        Raises:
            ValueError: If schedule not found or inactive
        """
        schedule = self.db.query(ReportSchedule).filter(
            ReportSchedule.id == schedule_id
        ).first()
        
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        if not schedule.is_active:
            raise ValueError(f"Schedule {schedule_id} is inactive")
        
        try:
            # Generate the report
            result = self.report_service.generate_report(
                template_id=schedule.template_id,
                format=schedule.format,
                parameters=schedule.parameters or {},
                tenant_id=schedule.tenant_id,
                user_id=schedule.user_id
            )
            
            # Update schedule
            schedule.last_run_at = datetime.utcnow()
            schedule.next_run_at = self._calculate_next_run(
                schedule.frequency,
                schedule.cron_expression
            )
            self.db.commit()
            
            logger.info(
                "scheduled_report_executed",
                schedule_id=schedule_id,
                template_id=schedule.template_id,
                next_run_at=schedule.next_run_at.isoformat()
            )
            
            return {
                "schedule_id": schedule_id,
                "status": "success",
                "report": result,
                "next_run_at": schedule.next_run_at.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "scheduled_report_execution_failed",
                schedule_id=schedule_id,
                error=str(e)
            )
            raise
    
    def _validate_cron_expression(self, cron_expression: str) -> None:
        """
        Validate cron expression format.
        
        Args:
            cron_expression: Cron expression string
        
        Raises:
            ValueError: If cron expression is invalid
        """
        # Basic cron validation: 5 or 6 fields separated by spaces
        # Format: minute hour day month day_of_week [year]
        parts = cron_expression.strip().split()
        
        if len(parts) not in [5, 6]:
            raise ValueError(
                "Cron expression must have 5 or 6 fields: "
                "minute hour day month day_of_week [year]"
            )
        
        # Validate each field contains valid characters
        valid_chars = re.compile(r'^[\d\*\-\,\/]+$')
        for i, part in enumerate(parts):
            if not valid_chars.match(part):
                raise ValueError(
                    f"Invalid characters in cron field {i+1}: {part}"
                )
    
    def _calculate_next_run(
        self,
        frequency: str,
        cron_expression: Optional[str] = None
    ) -> datetime:
        """
        Calculate next run time based on frequency.
        
        Args:
            frequency: Schedule frequency (daily, weekly, monthly)
            cron_expression: Optional cron expression (not fully implemented)
        
        Returns:
            Next run datetime
        """
        now = datetime.utcnow()
        
        if frequency == "daily":
            # Run at 9:00 AM UTC next day
            next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif frequency == "weekly":
            # Run at 9:00 AM UTC next Monday
            next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and next_run <= now:
                days_until_monday = 7
            next_run += timedelta(days=days_until_monday)
            return next_run
        
        elif frequency == "monthly":
            # Run at 9:00 AM UTC on the 1st of next month
            if now.month == 12:
                next_run = now.replace(
                    year=now.year + 1,
                    month=1,
                    day=1,
                    hour=9,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            else:
                next_run = now.replace(
                    month=now.month + 1,
                    day=1,
                    hour=9,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            return next_run
        
        else:
            # Default to daily if unknown
            return now + timedelta(days=1)
