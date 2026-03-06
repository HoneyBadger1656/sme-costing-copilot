# backend/app/middleware/correlation_middleware.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import uuid
import structlog

from app.logging_config import get_logger

logger = get_logger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to all requests for distributed tracing.
    
    This middleware:
    - Extracts correlation ID from X-Correlation-ID header if present
    - Generates a new correlation ID if not present
    - Adds correlation ID to request state
    - Adds correlation ID to response headers
    - Binds correlation ID to structlog context for all logs
    
    Requirement 29.6: Include correlation IDs in logs to trace requests across components
    """
    
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add correlation ID.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in the chain
        
        Returns:
            Response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            self.CORRELATION_ID_HEADER,
            str(uuid.uuid4())
        )
        
        # Store correlation ID in request state for access in endpoints
        request.state.correlation_id = correlation_id
        
        # Bind correlation ID to structlog context
        # This ensures all logs within this request include the correlation ID
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_method=request.method,
            request_path=request.url.path
        )
        
        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers[self.CORRELATION_ID_HEADER] = correlation_id
            
            # Log request completion
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                correlation_id=correlation_id
            )
            
            return response
            
        except Exception as e:
            # Log request failure
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
        
        finally:
            # Clear context variables after request
            structlog.contextvars.clear_contextvars()


def add_correlation_middleware(app):
    """
    Add correlation middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(CorrelationMiddleware)
    logger.info("correlation_middleware_added", message="Correlation ID middleware enabled")
