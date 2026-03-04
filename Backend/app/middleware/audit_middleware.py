# backend/app/middleware/audit_middleware.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session
from typing import Callable
import json

from app.core.database import get_db
from app.utils.audit import log_audit_event, get_model_dict
from app.logging_config import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log audit trails for CUD operations.
    
    This middleware intercepts POST, PUT, PATCH, and DELETE requests
    and logs them to the audit_logs table after successful completion.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.audit_enabled_paths = [
            "/api/clients",
            "/api/products",
            "/api/orders",
            "/api/roles",
            "/api/users",
            "/api/scenarios",
            "/api/financials",
            "/api/costing"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log audit trail if applicable.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in the chain
        
        Returns:
            Response from the endpoint
        """
        # Only audit CUD operations (POST, PUT, PATCH, DELETE)
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)
        
        # Check if path should be audited
        should_audit = any(
            request.url.path.startswith(path) 
            for path in self.audit_enabled_paths
        )
        
        if not should_audit:
            return await call_next(request)
        
        # Store request body for audit logging
        # Note: This is a simplified approach. In production, you might want
        # to capture the actual database changes using SQLAlchemy events
        try:
            body = await request.body()
            request_data = json.loads(body) if body else {}
        except:
            request_data = {}
        
        # Process the request
        response = await call_next(request)
        
        # Only log successful operations (2xx status codes)
        if 200 <= response.status_code < 300:
            # Extract information from request
            path_parts = request.url.path.split("/")
            
            # Determine table name from path
            table_name = self._extract_table_name(path_parts)
            
            # Determine action from method
            action = self._map_method_to_action(request.method)
            
            # Extract record ID from path or response
            record_id = self._extract_record_id(path_parts, request.method)
            
            # Get tenant_id and user_id from request state (set by auth middleware)
            tenant_id = getattr(request.state, "tenant_id", None)
            user_id = getattr(request.state, "user_id", None)
            
            # Log audit event asynchronously (don't block response)
            if table_name and record_id and tenant_id:
                try:
                    # Get database session
                    db = next(get_db())
                    
                    # Determine old and new values based on action
                    old_values = None
                    new_values = request_data if action in ["CREATE", "UPDATE"] else None
                    
                    if action == "DELETE":
                        old_values = request_data
                    
                    # Log the audit event
                    log_audit_event(
                        db=db,
                        action=action,
                        table_name=table_name,
                        record_id=record_id,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        old_values=old_values,
                        new_values=new_values,
                        request=request
                    )
                    
                    db.close()
                    
                except Exception as e:
                    # Log error but don't fail the request
                    logger.error(
                        "audit_middleware_error",
                        error=str(e),
                        path=request.url.path,
                        method=request.method
                    )
        
        return response
    
    def _extract_table_name(self, path_parts: list) -> str:
        """
        Extract table name from URL path.
        
        Args:
            path_parts: List of path segments
        
        Returns:
            Table name or empty string
        """
        # Map API paths to table names
        path_to_table = {
            "clients": "clients",
            "products": "products",
            "orders": "orders",
            "roles": "roles",
            "users": "users",
            "scenarios": "scenarios",
            "bom": "bom_items"
        }
        
        for part in path_parts:
            if part in path_to_table:
                return path_to_table[part]
        
        return ""
    
    def _map_method_to_action(self, method: str) -> str:
        """
        Map HTTP method to audit action.
        
        Args:
            method: HTTP method (POST, PUT, PATCH, DELETE)
        
        Returns:
            Audit action (CREATE, UPDATE, DELETE)
        """
        method_to_action = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE"
        }
        
        return method_to_action.get(method, "UNKNOWN")
    
    def _extract_record_id(self, path_parts: list, method: str) -> int:
        """
        Extract record ID from URL path.
        
        Args:
            path_parts: List of path segments
            method: HTTP method
        
        Returns:
            Record ID or 0 if not found
        """
        # For POST (CREATE), we might not have the ID in the path
        # For PUT/PATCH/DELETE, the ID is usually in the path
        
        # Look for numeric path segments
        for part in path_parts:
            if part.isdigit():
                return int(part)
        
        return 0


def add_audit_middleware(app):
    """
    Add audit middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(AuditMiddleware)
    logger.info("audit_middleware_added", message="Audit trail middleware enabled")
