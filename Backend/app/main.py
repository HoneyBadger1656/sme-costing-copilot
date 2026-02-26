from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
import json

from app.core.database import engine, Base
from app.api import auth, clients, evaluations, data_upload

app = FastAPI(
    title="SME Costing Copilot API",
    version="1.0.0",
    description="AI-powered costing and working capital decisions for Indian SMEs",
    json_encoders={UUID: str}
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/")
def root():
    return {"message": "SME Costing Copilot API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
