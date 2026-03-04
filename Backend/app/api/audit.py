# backend/app/api/audit.py

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import io

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User
from app.services.audit_service import AuditService
from app.utils.rbac import require_role
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["audit"])


class AuditLogFilters(BaseModel):
    """Filters for audit log queries"""
    table_name: Optional[str] = None
    action: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("/audit-logs")
@require_role(["Admin", "Owner"])
def get_audit_logs(
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    action: Optional[str] = Query(None, description="Filter by action (CREATE, UPDATE, DELETE)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO 8601)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with filtering and pagination (Owner/Admin only).
    
    Returns paginated audit logs for the current user's organization.
    """
    try:
        # Get tenant ID from current user
        tenant_id = current_user.organization_id
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        # Get audit logs
        result = AuditService.get_audit_logs(
            db=db,
            tenant_id=tenant_id,
            table_name=table_name,
            action=action,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        logger.info(
            "audit_logs_retrieved",
            tenant_id=tenant_id,
            user_id=current_user.id,
            count=len(result["logs"])
        )
        
        return result
        
    except Exception as e:
        logger.error("get_audit_logs_error", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get("/audit-logs/record/{table_name}/{record_id}")
@require_role(["Admin", "Owner"])
def get_record_history(
    table_name: str,
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete audit history for a specific record (Owner/Admin only).
    
    Returns all audit log entries for the specified record.
    """
    try:
        tenant_id = current_user.organization_id
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        history = AuditService.get_record_history(
            db=db,
            tenant_id=tenant_id,
            table_name=table_name,
            record_id=record_id
        )
        
        logger.info(
            "record_history_retrieved",
            tenant_id=tenant_id,
            table_name=table_name,
            record_id=record_id,
            count=len(history)
        )
        
        return {
            "table_name": table_name,
            "record_id": record_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(
            "get_record_history_error",
            error=str(e),
            table_name=table_name,
            record_id=record_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve record history")


@router.get("/audit-logs/export")
@require_role(["Admin", "Owner"])
def export_audit_logs(
    format: str = Query("csv", description="Export format (csv)"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    action: Optional[str] = Query(None, description="Filter by action"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export audit logs to CSV format (Owner/Admin only).
    
    Returns a downloadable CSV file with filtered audit logs.
    """
    try:
        tenant_id = current_user.organization_id
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        if format.lower() != "csv":
            raise HTTPException(status_code=400, detail="Only CSV format is currently supported")
        
        # Export audit logs
        csv_content = AuditService.export_audit_logs(
            db=db,
            tenant_id=tenant_id,
            format=format,
            table_name=table_name,
            action=action,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(
            "audit_logs_exported",
            tenant_id=tenant_id,
            user_id=current_user.id,
            format=format
        )
        
        # Create streaming response
        output = io.BytesIO(csv_content.encode('utf-8'))
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.csv"
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("export_audit_logs_error", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to export audit logs")


@router.get("/audit-logs/statistics")
@require_role(["Admin", "Owner"])
def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit log statistics (Owner/Admin only).
    
    Returns statistics about audit logs including action counts and top users.
    """
    try:
        tenant_id = current_user.organization_id
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        statistics = AuditService.get_audit_statistics(
            db=db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(
            "audit_statistics_retrieved",
            tenant_id=tenant_id,
            user_id=current_user.id
        )
        
        return statistics
        
    except Exception as e:
        logger.error("get_audit_statistics_error", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve audit statistics")
