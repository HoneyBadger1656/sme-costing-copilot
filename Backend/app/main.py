from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
from uuid import UUID
import json
import os
import logging

from app.core.database import engine, Base
from app.api import auth, clients, evaluations, data_upload, scenarios, financials, assistant, integrations, costing, products
from app.middleware.security import add_security_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SME Costing Copilot API",
    version="1.0.0",
    description="AI-powered costing and working capital decisions for Indian SMEs",
    json_encoders={UUID: str}
)

# Add security middleware
add_security_middleware(app)

# CORS middleware - restrict to specific origins in production
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    os.getenv("PUBLIC_URL", "http://localhost:8000"),
    "https://sme-costing-copilot-production.up.railway.app",
    "https://sme-costing-copilot-frontend.vercel.app",
    "https://sme-costing-copilot-frontend-3wy5n5q29.vercel.app",
    "https://*.vercel.app"  # Allow all Vercel preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

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
def root():
    # Redirect to frontend if available, otherwise show API info
    for frontend_path in frontend_paths:
        if (frontend_path / "index.html").exists():
            return FileResponse(frontend_path / "index.html")
    return {"message": "SME Costing Copilot API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
