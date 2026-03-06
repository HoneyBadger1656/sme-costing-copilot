"""Tests for correlation ID middleware"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.correlation_middleware import CorrelationMiddleware, add_correlation_middleware
import uuid


@pytest.fixture
def test_app():
    """Create a test FastAPI application with correlation middleware"""
    app = FastAPI()
    
    # Add correlation middleware
    add_correlation_middleware(app)
    
    # Add a test endpoint
    @app.get("/test")
    async def test_endpoint(request: Request):
        # Return correlation ID from request state
        correlation_id = getattr(request.state, "correlation_id", None)
        return {
            "message": "test",
            "correlation_id": correlation_id
        }
    
    @app.post("/test-post")
    async def test_post_endpoint(request: Request):
        correlation_id = getattr(request.state, "correlation_id", None)
        return {
            "message": "created",
            "correlation_id": correlation_id
        }
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client"""
    return TestClient(test_app)


def test_correlation_id_generated_when_not_provided(client):
    """Test that correlation ID is generated when not provided in request"""
    response = client.get("/test")
    
    assert response.status_code == 200
    
    # Check response header contains correlation ID
    assert "X-Correlation-ID" in response.headers
    correlation_id = response.headers["X-Correlation-ID"]
    
    # Verify it's a valid UUID
    try:
        uuid.UUID(correlation_id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    
    assert is_valid_uuid, "Generated correlation ID should be a valid UUID"
    
    # Check response body contains the same correlation ID
    assert response.json()["correlation_id"] == correlation_id


def test_correlation_id_preserved_when_provided(client):
    """Test that correlation ID from request header is preserved"""
    provided_correlation_id = str(uuid.uuid4())
    
    response = client.get(
        "/test",
        headers={"X-Correlation-ID": provided_correlation_id}
    )
    
    assert response.status_code == 200
    
    # Check response header contains the same correlation ID
    assert response.headers["X-Correlation-ID"] == provided_correlation_id
    
    # Check response body contains the same correlation ID
    assert response.json()["correlation_id"] == provided_correlation_id


def test_correlation_id_works_with_post_requests(client):
    """Test that correlation ID works with POST requests"""
    provided_correlation_id = str(uuid.uuid4())
    
    response = client.post(
        "/test-post",
        json={"data": "test"},
        headers={"X-Correlation-ID": provided_correlation_id}
    )
    
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == provided_correlation_id
    assert response.json()["correlation_id"] == provided_correlation_id


def test_correlation_id_unique_per_request(client):
    """Test that each request gets a unique correlation ID when not provided"""
    response1 = client.get("/test")
    response2 = client.get("/test")
    
    correlation_id1 = response1.headers["X-Correlation-ID"]
    correlation_id2 = response2.headers["X-Correlation-ID"]
    
    # Correlation IDs should be different for different requests
    assert correlation_id1 != correlation_id2


def test_correlation_id_header_case_insensitive(client):
    """Test that correlation ID header is case-insensitive"""
    provided_correlation_id = str(uuid.uuid4())
    
    # Try with different case
    response = client.get(
        "/test",
        headers={"x-correlation-id": provided_correlation_id}
    )
    
    assert response.status_code == 200
    # FastAPI normalizes headers, so check if the ID is preserved
    assert response.json()["correlation_id"] == provided_correlation_id


def test_correlation_middleware_added_successfully():
    """Test that correlation middleware can be added to an app"""
    app = FastAPI()
    
    # Should not raise any exceptions
    add_correlation_middleware(app)
    
    # Verify middleware was added
    assert len(app.user_middleware) > 0
    
    # Check that the middleware is CorrelationMiddleware
    middleware_found = False
    for middleware in app.user_middleware:
        if middleware.cls == CorrelationMiddleware:
            middleware_found = True
            break
    
    assert middleware_found, "CorrelationMiddleware should be added to the app"
