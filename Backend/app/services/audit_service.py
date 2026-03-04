# backend/app/services/audit_service.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Dict, Any, Optional
import csv
import io

from app.models.models import AuditLog, User
from app.logging_config import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for querying and exporting audit logs."""
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        tenant_id: str,
        table_name: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get audit logs with filtering and pagination.
        
        Args:
            db: Database session
            tenant_id: Tenant/Organization ID
            table_name: Filter by table name (optional)
            action: Filter by action (CREATE, UPDATE, DELETE) (optional)
            user_id: Filter by user ID (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
        
        Returns:
            Dictionary with logs, total count, and pagination info
        """
        try:
            # Build query
            query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
            
            # Apply filters
            if table_name:
                query = query.filter(AuditLog.table_name == table_name)
            
            if action:
                query = query.filter(AuditLog.action == action.upper())
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
            
            # Format logs
            formatted_logs = []
            for log in logs:
                # Get user info
                user_email = None
                if log.user_id:
                    user = db.query(User).filter(User.id == log.user_id).first()
                    if user:
                        user_email = user.email
                
                formatted_logs.append({
                    "id": log.id,
                    "tenant_id": log.tenant_id,
                    "user_id": log.user_id,
                    "user_email": user_email,
                    "action": log.action,
                    "table_name": log.table_name,
                    "record_id": log.record_id,
                    "old_values": log.old_values,
                    "new_values": log.new_values,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            return {
                "logs": formatted_logs,
                "total": total,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "per_page": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 1
            }
            
        except Exception as e:
            logger.error("get_audit_logs_error", error=str(e), tenant_id=tenant_id)
            raise
    
    @staticmethod
    def get_record_history(
        db: Session,
        tenant_id: str,
        table_name: str,
        record_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit history for a specific record.
        
        Args:
            db: Database session
            tenant_id: Tenant/Organization ID
            table_name: Name of the table
            record_id: ID of the record
        
        Returns:
            List of audit log entries for the record
        """
        try:
            logs = AuditLog.get_record_history(db, table_name, record_id, tenant_id)
            
            formatted_logs = []
            for log in logs:
                # Get user info
                user_email = None
                if log.user_id:
                    user = db.query(User).filter(User.id == log.user_id).first()
                    if user:
                        user_email = user.email
                
                formatted_logs.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "user_email": user_email,
                    "action": log.action,
                    "old_values": log.old_values,
                    "new_values": log.new_values,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            return formatted_logs
            
        except Exception as e:
            logger.error(
                "get_record_history_error",
                error=str(e),
                tenant_id=tenant_id,
                table_name=table_name,
                record_id=record_id
            )
            raise
    
    @staticmethod
    def export_audit_logs(
        db: Session,
        tenant_id: str,
        format: str = "csv",
        table_name: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs to CSV format.
        
        Args:
            db: Database session
            tenant_id: Tenant/Organization ID
            format: Export format (currently only 'csv' supported)
            table_name: Filter by table name (optional)
            action: Filter by action (optional)
            user_id: Filter by user ID (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
        
        Returns:
            CSV string containing audit logs
        """
        try:
            # Get all matching logs (no pagination for export)
            result = AuditService.get_audit_logs(
                db=db,
                tenant_id=tenant_id,
                table_name=table_name,
                action=action,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                skip=0,
                limit=10000  # Max export limit
            )
            
            logs = result["logs"]
            
            # Create CSV
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id", "created_at", "user_email", "action", "table_name",
                    "record_id", "ip_address", "old_values", "new_values"
                ]
            )
            
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    "id": log["id"],
                    "created_at": log["created_at"],
                    "user_email": log["user_email"] or "System",
                    "action": log["action"],
                    "table_name": log["table_name"],
                    "record_id": log["record_id"],
                    "ip_address": log["ip_address"] or "N/A",
                    "old_values": str(log["old_values"]) if log["old_values"] else "",
                    "new_values": str(log["new_values"]) if log["new_values"] else ""
                })
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(
                "audit_logs_exported",
                tenant_id=tenant_id,
                format=format,
                count=len(logs)
            )
            
            return csv_content
            
        except Exception as e:
            logger.error("export_audit_logs_error", error=str(e), tenant_id=tenant_id)
            raise
    
    @staticmethod
    def get_audit_statistics(
        db: Session,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit log statistics for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant/Organization ID
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
        
        Returns:
            Dictionary with audit statistics
        """
        try:
            query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            total_logs = query.count()
            
            # Count by action
            create_count = query.filter(AuditLog.action == "CREATE").count()
            update_count = query.filter(AuditLog.action == "UPDATE").count()
            delete_count = query.filter(AuditLog.action == "DELETE").count()
            
            # Get most active users
            from sqlalchemy import func
            top_users = db.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label("count")
            ).filter(
                AuditLog.tenant_id == tenant_id
            ).group_by(
                AuditLog.user_id
            ).order_by(
                func.count(AuditLog.id).desc()
            ).limit(5).all()
            
            # Get user emails
            top_users_with_emails = []
            for user_id, count in top_users:
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
                    email = user.email if user else "Unknown"
                else:
                    email = "System"
                
                top_users_with_emails.append({
                    "user_id": user_id,
                    "email": email,
                    "action_count": count
                })
            
            return {
                "total_logs": total_logs,
                "create_count": create_count,
                "update_count": update_count,
                "delete_count": delete_count,
                "top_users": top_users_with_emails,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error("get_audit_statistics_error", error=str(e), tenant_id=tenant_id)
            raise
