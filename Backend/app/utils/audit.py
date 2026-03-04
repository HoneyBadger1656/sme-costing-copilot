# backend/app/utils/audit.py

from sqlalchemy.orm import Session
from fastapi import Request
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.models import AuditLog
from app.logging_config import get_logger

logger = get_logger(__name__)

# Sensitive fields that should be excluded from audit logs
SENSITIVE_FIELDS = {
    'password', 'hashed_password', 'access_token', 'refresh_token',
    'api_key', 'secret_key', 'private_key', 'token', 'zoho_tokens',
    'tally_config'
}


def sanitize_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive fields from data before logging.
    
    Args:
        data: Dictionary containing data to sanitize
    
    Returns:
        Sanitized dictionary with sensitive fields removed
    """
    if not data:
        return data
    
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_fields(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_sensitive_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


def log_audit_event(
    db: Session,
    action: str,
    table_name: str,
    record_id: int,
    tenant_id: str,
    user_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> Optional[AuditLog]:
    """
    Log an audit event for a database operation.
    
    Args:
        db: Database session
        action: Action type (CREATE, UPDATE, DELETE)
        table_name: Name of the table being modified
        record_id: ID of the record being modified
        tenant_id: Tenant/Organization ID
        user_id: ID of the user performing the action (optional)
        old_values: Previous state of the record (for UPDATE/DELETE)
        new_values: New state of the record (for CREATE/UPDATE)
        request: FastAPI request object (optional, for IP and user agent)
    
    Returns:
        Created AuditLog object or None if logging failed
    """
    try:
        # Sanitize sensitive data
        sanitized_old = sanitize_sensitive_fields(old_values) if old_values else None
        sanitized_new = sanitize_sensitive_fields(new_values) if new_values else None
        
        # Extract IP address and user agent from request
        ip_address = None
        user_agent = None
        if request:
            # Get real IP from X-Forwarded-For header or client host
            ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not ip_address:
                ip_address = request.client.host if request.client else None
            
            user_agent = request.headers.get("User-Agent")
            # Truncate user agent if too long
            if user_agent and len(user_agent) > 500:
                user_agent = user_agent[:497] + "..."
        
        # Create audit log entry
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action.upper(),
            table_name=table_name,
            record_id=record_id,
            old_values=sanitized_old,
            new_values=sanitized_new,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        db.add(audit_log)
        db.commit()
        
        logger.info(
            "audit_log_created",
            action=action,
            table_name=table_name,
            record_id=record_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return audit_log
        
    except Exception as e:
        # Log the error but don't block the operation
        logger.error(
            "audit_log_failed",
            error=str(e),
            action=action,
            table_name=table_name,
            record_id=record_id,
            tenant_id=tenant_id
        )
        
        # Rollback the audit log transaction but don't raise
        try:
            db.rollback()
        except:
            pass
        
        return None


def get_model_dict(model_instance) -> Dict[str, Any]:
    """
    Convert SQLAlchemy model instance to dictionary.
    
    Args:
        model_instance: SQLAlchemy model instance
    
    Returns:
        Dictionary representation of the model
    """
    if not model_instance:
        return {}
    
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        
        # Convert datetime to ISO format string
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        # Convert other non-serializable types
        elif hasattr(value, '__dict__'):
            result[column.name] = str(value)
        else:
            result[column.name] = value
    
    return result


def log_create(
    db: Session,
    table_name: str,
    record_id: int,
    tenant_id: str,
    new_values: Dict[str, Any],
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> Optional[AuditLog]:
    """
    Log a CREATE operation.
    
    Args:
        db: Database session
        table_name: Name of the table
        record_id: ID of the created record
        tenant_id: Tenant/Organization ID
        new_values: New record data
        user_id: ID of the user performing the action
        request: FastAPI request object
    
    Returns:
        Created AuditLog object or None
    """
    return log_audit_event(
        db=db,
        action="CREATE",
        table_name=table_name,
        record_id=record_id,
        tenant_id=tenant_id,
        user_id=user_id,
        old_values=None,
        new_values=new_values,
        request=request
    )


def log_update(
    db: Session,
    table_name: str,
    record_id: int,
    tenant_id: str,
    old_values: Dict[str, Any],
    new_values: Dict[str, Any],
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> Optional[AuditLog]:
    """
    Log an UPDATE operation.
    
    Args:
        db: Database session
        table_name: Name of the table
        record_id: ID of the updated record
        tenant_id: Tenant/Organization ID
        old_values: Previous record data
        new_values: New record data
        user_id: ID of the user performing the action
        request: FastAPI request object
    
    Returns:
        Created AuditLog object or None
    """
    return log_audit_event(
        db=db,
        action="UPDATE",
        table_name=table_name,
        record_id=record_id,
        tenant_id=tenant_id,
        user_id=user_id,
        old_values=old_values,
        new_values=new_values,
        request=request
    )


def log_delete(
    db: Session,
    table_name: str,
    record_id: int,
    tenant_id: str,
    old_values: Dict[str, Any],
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> Optional[AuditLog]:
    """
    Log a DELETE operation.
    
    Args:
        db: Database session
        table_name: Name of the table
        record_id: ID of the deleted record
        tenant_id: Tenant/Organization ID
        old_values: Previous record data
        user_id: ID of the user performing the action
        request: FastAPI request object
    
    Returns:
        Created AuditLog object or None
    """
    return log_audit_event(
        db=db,
        action="DELETE",
        table_name=table_name,
        record_id=record_id,
        tenant_id=tenant_id,
        user_id=user_id,
        old_values=old_values,
        new_values=None,
        request=request
    )
