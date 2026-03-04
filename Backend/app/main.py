from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pathlib import Path
from uuid import UUID
import json
import os
import logging
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.api import auth, clients, evaluations, data_upload, scenarios, financials, assistant, integrations, costing, products, financial_data, roles, audit
from app.middleware.security import add_security_middleware
from app.exceptions import AppException
from app.logging_config import setup_logging, get_logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure structured logging
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    Base.metadata.create_all(bind=engine)
    logger.info("database_initialized", message="Database tables created successfully")
    yield
    # Shutdown
    logger.info("application_shutdown", message="Application shutting down")

app = FastAPI(
    title="SME Costing Copilot API",
    version="1.0.0",
    description="AI-powered costing and working capital decisions for Indian SMEs",
    json_encoders={UUID: str},
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware
add_security_middleware(app)

# CORS middleware - restrict to specific origins
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    # Production: strict CORS
    allowed_origins = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "").split(",") 
        if origin.strip()
    ]
    if not allowed_origins:
        logger.warning("cors_not_configured", message="CORS_ORIGINS not set in production")
        allowed_origins = ["https://sme-costing-copilot-frontend.vercel.app"]
else:
    # Development: allow localhost
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

logger.info("cors_configured", origins=allowed_origins, environment=ENVIRONMENT)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Global exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    logger.error(
        "application_error",
        error=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": exc.__class__.__name__}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "type": "ValidationError"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.exception(
        "unexpected_error",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "type": "InternalError"}
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(data_upload.router, prefix="/api/data", tags=["Data Upload"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])
app.include_router(financials.router, prefix="/api/financials", tags=["Financials"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["AI Assistant"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(costing.router, prefix="/api/costing", tags=["Costing"])
app.include_router(financial_data.router, prefix="/api/financial-data", tags=["Financial Data"])
app.include_router(roles.router, prefix="/api/roles", tags=["Roles"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])

# Serve static files (frontend) - check multiple possible locations
frontend_paths = [
    Path(__file__).parent.parent.parent / "frontend" / "out",
    Path(__file__).parent.parent.parent / "frontend" / "build", 
    Path(__file__).parent.parent.parent / "frontend" / "static",
    Path("/app/frontend/out"),
    Path("/app/frontend/build"),
    Path("/app/frontend/static")
]

for frontend_path in frontend_paths:
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        logger.info(f"[FRONTEND] Serving static files from: {frontend_path}")
        break

@app.get("/")
@limiter.limit("10/minute")
def root(request: Request):
    # Redirect to frontend if available, otherwise show API info
    for frontend_path in frontend_paths:
        if (frontend_path / "index.html").exists():
            return FileResponse(frontend_path / "index.html")
    return {"message": "SME Costing Copilot API", "status": "running", "version": "1.0.0"}

@app.get("/health")
@limiter.limit("30/minute")
def health_check(request: Request):
    return {"status": "healthy", "version": "1.0.0"}

# Serve frontend for all other routes (SPA) - exclude API paths
@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str):
    # Don't interfere with API routes
    if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi") or path.startswith("health"):
        return {"message": "API endpoint not found", "path": path}
    
    # Try to serve static file first
    for frontend_path in frontend_paths:
        static_file = frontend_path / path
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)
    
    # Fallback to index.html for SPA routing
    for frontend_path in frontend_paths:
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    
    # If no frontend, return API message
    return {"message": "SME Costing Copilot API - Frontend not built", "path": path}
