# File: backend/app/api/clients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.models.models import Client, User, Organization
from app.api.auth import get_current_user

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

@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clients = db.query(Client).filter(
        Client.organization_id == current_user.organization_id
    ).offset(skip).limit(limit).all()
    return clients

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: str,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_dict = client_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    return client

@router.delete("/{client_id}")
def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}
