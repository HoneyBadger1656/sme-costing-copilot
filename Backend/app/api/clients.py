# File: backend/app/api/clients.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.models.models import Client, User, Organization
from app.api.auth import get_current_user
from app.utils.tenant import TenantFilter
from app.utils.pagination import paginate, create_paginated_response
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

class ClientCreate(BaseModel):
    business_name: str
    email: str
    phone: Optional[str] = None
    industry: str = "manufacturing"
    annual_revenue: Optional[float] = 0.0
    current_debtors: Optional[float] = 0.0
    average_credit_days: Optional[int] = 30

class ClientUpdate(BaseModel):
    business_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    current_debtors: Optional[float] = None
    average_credit_days: Optional[int] = None

class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    business_name: str
    email: str
    phone: Optional[str]
    industry: str
    annual_revenue: float
    current_debtors: float
    average_credit_days: int
    organization_id: str

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify organization access
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User not associated with organization")
    
    # Create client
    client = Client(
        business_name=client_data.business_name,
        email=client_data.email,
        phone=client_data.phone,
        industry=client_data.industry,
        annual_revenue=client_data.annual_revenue or 0.0,
        current_debtors=client_data.current_debtors or 0.0,
        average_credit_days=client_data.average_credit_days or 30,
        user_id=current_user.id,
        organization_id=current_user.organization_id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/")
async def list_clients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all clients with pagination and tenant isolation
    
    Returns paginated response with metadata
    """
    try:
        # Use tenant filter for automatic organization isolation
        tenant = TenantFilter(db, current_user)
        query = tenant.query(Client)
        
        # Apply pagination
        items, total = paginate(query, skip=skip, limit=limit)
        
        logger.info("clients_listed", 
                   organization_id=current_user.organization_id,
                   total=total,
                   returned=len(items))
        
        # Return paginated response
        return create_paginated_response(items, total, skip, limit)
        
    except Exception as e:
        logger.exception("list_clients_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list clients")

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single client with tenant isolation"""
    try:
        tenant = TenantFilter(db, current_user)
        client = tenant.get_by_id(Client, client_id)
        
        if not client:
            logger.warning("client_not_found", 
                          client_id=client_id,
                          organization_id=current_user.organization_id)
            raise HTTPException(status_code=404, detail="Client not found")
        
        return client
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_client_failed", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve client")

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a client with tenant isolation"""
    try:
        tenant = TenantFilter(db, current_user)
        client = tenant.get_by_id(Client, client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        update_dict = client_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(client, field, value)
        
        db.commit()
        db.refresh(client)
        
        logger.info("client_updated", 
                   client_id=client_id,
                   organization_id=current_user.organization_id)
        
        return client
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("update_client_failed", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update client")

@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a client with tenant isolation"""
    try:
        tenant = TenantFilter(db, current_user)
        client = tenant.get_by_id(Client, client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        db.delete(client)
        db.commit()
        
        logger.info("client_deleted", 
                   client_id=client_id,
                   organization_id=current_user.organization_id)
        
        return {"message": "Client deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("delete_client_failed", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete client")
