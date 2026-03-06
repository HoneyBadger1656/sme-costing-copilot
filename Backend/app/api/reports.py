# backend/app/api/reports.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import date

from app.core.database import get_db
from app.models.models import User
from app.api.auth import get_current_user
from app.services.report_service import ReportService
from app.services.report_templates import get_all_templates, get_template
from app.services.scheduled_report_service import ScheduledReportService
from app.utils.rbac import require_role
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Rate limiting configuration from environment variables (Requirement 30.3)
RATE_LIMIT_REPORTS_PER_HOUR = int(os.getenv("RATE_LIMIT_REPORTS_PER_HOUR", "10"))


# Pydantic schemas
class ReportGenerateRequest(BaseModel):
    """Request schema for report generation"""
    template_id: str = Field(..., description="Report template ID")
    format: str = Field(..., description="Output format (pdf, excel, csv)")
    parameters: Dict[str, Any] = Field(..., description="Report parameters")


class ReportGenerateResponse(BaseModel):
    """Response schema for report generation"""
    task_id: str
    template_id: str
    format: str
    status: str
    message: str


class ReportStatusResponse(BaseModel):
    """Response schema for report status"""
    task_id: str
    status: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


class ReportTemplateResponse(BaseModel):
    """Response schema for report template"""
    id: str
    name: str
    description: str
    data_sources: List[str]
    supported_formats: List[str]
    parameters: Dict[str, Any]


class ScheduleCreateRequest(BaseModel):
    """Request schema for creating a scheduled report"""
    template_id: str = Field(..., description="Report template ID")
    format: str = Field(..., description="Output format (pdf, excel, csv)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    frequency: str = Field(..., description="Schedule frequency (daily, weekly, monthly)")
    recipients: List[str] = Field(..., description="List of recipient email addresses")
    cron_expression: Optional[str] = Field(None, description="Optional cron expression for custom schedules")


class ScheduleResponse(BaseModel):
    """Response schema for scheduled report"""
    id: int
    template_id: str
    format: str
    parameters: Dict[str, Any]
    frequency: str
    cron_expression: Optional[str]
    recipients: List[str]
    next_run_at: str
    last_run_at: Optional[str]
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/generate", response_model=ReportGenerateResponse)
@limiter.limit(f"{RATE_LIMIT_REPORTS_PER_HOUR}/hour")
def generate_report(
    request: Request,
    report_request: ReportGenerateRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Generate a report.
    
    Requires Accountant, Admin, or Owner role.
    Rate limited based on RATE_LIMIT_REPORTS_PER_HOUR environment variable (Requirement 30.3).
    """
    try:
        logger.info(
            "report_generation_requested",
            template_id=report_request.template_id,
            format=report_request.format,
            user_id=current_user.id,
            tenant_id=current_user.organization_id
        )
        
        # Generate report synchronously
        report_service = ReportService(db)
        result = report_service.generate_report(
            template_id=report_request.template_id,
            format=report_request.format,
            parameters=report_request.parameters,
            tenant_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        return ReportGenerateResponse(
            task_id=result["task_id"],
            template_id=report_request.template_id,
            format=report_request.format,
            status="completed",
            message="Report generated successfully"
        )
        
    except ValueError as e:
        logger.warning(
            "report_generation_validation_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(
            "report_generation_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report generation failed"
        )


@router.get("/status/{task_id}", response_model=ReportStatusResponse)
def get_report_status(
    task_id: str,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Get report generation status.
    
    Requires Accountant, Admin, or Owner role.
    """
    try:
        report_service = ReportService(db)
        status_info = report_service.get_report_status(task_id)
        
        if status_info["status"] == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get download URL if completed
        download_url = None
        if status_info["status"] == "completed":
            download_url = report_service.get_report_download_url(task_id)
        
        return ReportStatusResponse(
            task_id=task_id,
            status=status_info["status"],
            file_name=status_info.get("file_name"),
            file_size=status_info.get("file_size"),
            download_url=download_url,
            created_at=status_info.get("created_at"),
            expires_at=status_info.get("expires_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("report_status_error", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report status"
        )


@router.get("/download/{task_id}")
def download_report(
    task_id: str,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Download a generated report.
    
    Requires Accountant, Admin, or Owner role.
    """
    try:
        report_service = ReportService(db)
        
        # Check status
        status_info = report_service.get_report_status(task_id)
        
        if status_info["status"] == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        if status_info["status"] == "expired":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Report has expired"
            )
        
        # Get file path
        file_path = report_service.get_report_file_path(task_id)
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found"
            )
        
        logger.info(
            "report_downloaded",
            task_id=task_id,
            user_id=current_user.id,
            file_name=file_path.name
        )
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("report_download_error", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download report"
        )


@router.get("/templates", response_model=List[ReportTemplateResponse])
def list_report_templates(
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner"))
):
    """
    List all available report templates.
    
    Requires Accountant, Admin, or Owner role.
    """
    try:
        templates = get_all_templates()
        return templates
        
    except Exception as e:
        logger.exception("list_templates_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
def get_report_template(
    template_id: str,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner"))
):
    """
    Get details of a specific report template.
    
    Requires Accountant, Admin, or Owner role.
    """
    try:
        template = get_template(template_id)
        return template.to_dict()
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("get_template_error", error=str(e), template_id=template_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )



# Scheduled Report Endpoints

@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule_request: ScheduleCreateRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Create a new scheduled report.
    
    Requires Accountant, Admin, or Owner role.
    
    Args:
        schedule_request: Schedule creation request with template_id, format, parameters, frequency, recipients
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Created schedule details
    """
    try:
        logger.info(
            "scheduled_report_create_requested",
            template_id=schedule_request.template_id,
            frequency=schedule_request.frequency,
            user_id=current_user.id,
            tenant_id=current_user.organization_id
        )
        
        scheduled_report_service = ScheduledReportService(db)
        schedule = scheduled_report_service.create_schedule(
            template_id=schedule_request.template_id,
            format=schedule_request.format,
            parameters=schedule_request.parameters,
            frequency=schedule_request.frequency,
            recipients=schedule_request.recipients,
            user_id=current_user.id,
            tenant_id=current_user.organization_id,
            cron_expression=schedule_request.cron_expression
        )
        
        return ScheduleResponse(
            id=schedule.id,
            template_id=schedule.template_id,
            format=schedule.format,
            parameters=schedule.parameters or {},
            frequency=schedule.frequency,
            cron_expression=schedule.cron_expression,
            recipients=schedule.recipients,
            next_run_at=schedule.next_run_at.isoformat(),
            last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            is_active=schedule.is_active,
            created_at=schedule.created_at.isoformat()
        )
        
    except ValueError as e:
        logger.warning(
            "scheduled_report_validation_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(
            "scheduled_report_create_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scheduled report"
        )


@router.get("/schedules", response_model=List[ScheduleResponse])
def list_schedules(
    user_id: Optional[int] = None,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    List all scheduled reports for the current tenant.
    
    Requires Accountant, Admin, or Owner role.
    
    Args:
        user_id: Optional filter by user ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        List of scheduled reports
    """
    try:
        scheduled_report_service = ScheduledReportService(db)
        schedules = scheduled_report_service.get_schedules(
            tenant_id=current_user.organization_id,
            user_id=user_id
        )
        
        return [
            ScheduleResponse(
                id=schedule.id,
                template_id=schedule.template_id,
                format=schedule.format,
                parameters=schedule.parameters or {},
                frequency=schedule.frequency,
                cron_expression=schedule.cron_expression,
                recipients=schedule.recipients,
                next_run_at=schedule.next_run_at.isoformat(),
                last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
                is_active=schedule.is_active,
                created_at=schedule.created_at.isoformat()
            )
            for schedule in schedules
        ]
        
    except Exception as e:
        logger.exception(
            "list_schedules_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list scheduled reports"
        )


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Get a specific scheduled report by ID.
    
    Requires Accountant, Admin, or Owner role.
    
    Args:
        schedule_id: Schedule ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Schedule details
    """
    try:
        scheduled_report_service = ScheduledReportService(db)
        schedule = scheduled_report_service.get_schedule_by_id(
            schedule_id=schedule_id,
            tenant_id=current_user.organization_id
        )
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found"
            )
        
        return ScheduleResponse(
            id=schedule.id,
            template_id=schedule.template_id,
            format=schedule.format,
            parameters=schedule.parameters or {},
            frequency=schedule.frequency,
            cron_expression=schedule.cron_expression,
            recipients=schedule.recipients,
            next_run_at=schedule.next_run_at.isoformat(),
            last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            is_active=schedule.is_active,
            created_at=schedule.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "get_schedule_error",
            error=str(e),
            schedule_id=schedule_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduled report"
        )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Cancel (delete) a scheduled report.
    
    Requires Accountant, Admin, or Owner role.
    
    Args:
        schedule_id: Schedule ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        204 No Content on success
    """
    try:
        logger.info(
            "scheduled_report_delete_requested",
            schedule_id=schedule_id,
            user_id=current_user.id,
            tenant_id=current_user.organization_id
        )
        
        scheduled_report_service = ScheduledReportService(db)
        deleted = scheduled_report_service.delete_schedule(
            schedule_id=schedule_id,
            tenant_id=current_user.organization_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "scheduled_report_delete_error",
            error=str(e),
            schedule_id=schedule_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scheduled report"
        )
