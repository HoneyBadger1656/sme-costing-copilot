from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from uuid import UUID
import json
import os

from app.core.database import engine, Base
from app.api import auth, clients, evaluations, data_upload, scenarios, financials, assistant, integrations, costing

app = FastAPI(
    title="SME Costing Copilot API",
    version="1.0.0",
    description="AI-powered costing and working capital decisions for Indian SMEs",
    json_encoders={UUID: str}
)

# CORS middleware - restrict to specific origins in production
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    os.getenv("PUBLIC_URL", "http://localhost:8000")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(data_upload.router, prefix="/api/data", tags=["Data Upload"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])
app.include_router(financials.router, prefix="/api/financials", tags=["Financials"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["AI Assistant"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(costing.router, prefix="/api/costing", tags=["Costing"])

# Serve static files (frontend)
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "static"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
def root():
    return {"message": "SME Costing Copilot API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Serve frontend for all other routes (SPA)
@app.get("/{path:path}")
def serve_frontend(path: str):
    frontend_index = Path(__file__).parent.parent.parent / "frontend" / "static" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {"message": "Frontend not built. Please build the frontend first."}
