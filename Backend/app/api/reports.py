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
from app.utils.rbac import require_role
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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


@router.post("/generate", response_model=ReportGenerateResponse)
@limiter.limit("10/minute")
def generate_report(
    request: Request,
    report_request: ReportGenerateRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Generate a report.
    
    Requires Accountant, Admin, or Owner role.
    Rate limited to 10 requests per minute.
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
