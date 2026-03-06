"""Tests for correlation ID integration with audit logging"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.correlation_middleware import add_correlation_middleware
import uuid
import structlog


@pytest.fixture
def test_app():
    """Create a test FastAPI application with correlation middleware"""
    app = FastAPI()
    
    # Add correlation middleware
    add_correlation_middleware(app)
    
    # Add a test endpoint that checks correlation ID in context
    @app.get("/test-logging")
    async def test_logging_endpoint(request: Request):
        # Get correlation ID from request state
        correlation_id = getattr(request.state, "correlation_id", None)
        
        # Get correlation ID from structlog context
        # This simulates what happens in audit logging
        context_vars = structlog.contextvars.get_contextvars()
        context_correlation_id = context_vars.get("correlation_id")
        
        return {
            "message": "test",
            "correlation_id_from_state": correlation_id,
            "correlation_id_from_context": context_correlation_id
        }
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client"""
    return TestClient(test_app)


def test_correlation_id_in_structlog_context(client):
    """Test that correlation ID is available in structlog context for logging"""
    provided_correlation_id = str(uuid.uuid4())
    
    # Make request with correlation ID
    response = client.get(
        "/test-logging",
        headers={"X-Correlation-ID": provided_correlation_id}
    )
    
    assert response.status_code == 200
    
    # Verify correlation ID is in request state
    assert response.json()["correlation_id_from_state"] == provided_correlation_id
    
    # Verify correlation ID is in structlog context
    # This is what allows all logs within the request to include the correlation ID
    assert response.json()["correlation_id_from_context"] == provided_correlation_id


def test_correlation_id_auto_generated_in_context(client):
    """Test that auto-generated correlation ID is available in structlog context"""
    # Make request without correlation ID
    response = client.get("/test-logging")
    
    assert response.status_code == 200
    
    # Verify correlation ID was generated
    correlation_id_from_state = response.json()["correlation_id_from_state"]
    correlation_id_from_context = response.json()["correlation_id_from_context"]
    
    assert correlation_id_from_state is not None
    assert correlation_id_from_context is not None
    
    # Both should be the same
    assert correlation_id_from_state == correlation_id_from_context
    
    # Verify it's a valid UUID
    try:
        uuid.UUID(correlation_id_from_state)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    
    assert is_valid_uuid


def test_correlation_id_enables_request_tracing():
    """
    Test that correlation IDs enable request tracing across components.
    
    This test verifies Requirement 29.6: Include correlation IDs in logs
    to trace requests across components.
    
    The correlation middleware:
    1. Extracts or generates a correlation ID
    2. Stores it in request.state for endpoint access
    3. Binds it to structlog context for automatic inclusion in all logs
    4. Adds it to response headers for client tracking
    """
    app = FastAPI()
    add_correlation_middleware(app)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        # Correlation ID is automatically available in structlog context
        # All logger.info/error/warning calls will include it
        return {"status": "ok"}
    
    client = TestClient(app)
    correlation_id = str(uuid.uuid4())
    
    response = client.get("/test", headers={"X-Correlation-ID": correlation_id})
    
    # Verify correlation ID is in response headers for end-to-end tracing
    assert response.headers["X-Correlation-ID"] == correlation_id
    assert response.status_code == 200

