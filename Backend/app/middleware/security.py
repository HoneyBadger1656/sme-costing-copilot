# Security middleware for FastAPI
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import time
import logging
import os

# Rate limiting storage (simple in-memory for demo)
rate_limit_storage = {}

security = HTTPBearer()

def add_security_middleware(app: FastAPI):
    """Add comprehensive security middleware to FastAPI app"""
    
    # Trusted Host middleware for production
    if not os.getenv("DEBUG", "false").lower() == "true":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                "localhost",
                "127.0.0.1",
                "sme-costing-copilot-production.up.railway.app",
                "*.railway.app"
            ]
        )
    
    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        cutoff_time = current_time - 60
        if client_ip in rate_limit_storage:
            rate_limit_storage[client_ip] = [
                timestamp for timestamp in rate_limit_storage[client_ip]
                if timestamp > cutoff_time
            ]
        else:
            rate_limit_storage[client_ip] = []
        
        # Check rate limit (100 requests per minute)
        if len(rate_limit_storage[client_ip]) > 100:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Add current request
        rate_limit_storage[client_ip].append(current_time)
        
        response = await call_next(request)
        return response
    
    # Security headers middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS in production
        if not os.getenv("DEBUG", "false").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    # Request logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logging.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"IP: {request.client.host}"
        )
        
        return response
