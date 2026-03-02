from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.core.database import get_db
from app.models.models import Product, Client, User
from app.api.auth import get_current_user

router = APIRouter()

class ProductCreate(BaseModel):
    client_id: int
    name: str
    category: Optional[str] = None
    unit: str = "pcs"
    raw_material_cost: float = 0.0
    labour_cost_per_unit: float = 0.0
    overhead_percentage: float = 10.0
    target_margin_percentage: float = 20.0
    tax_rate: float = 18.0

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    client_id: int
    name: str
    category: Optional[str]
    unit: str
    raw_material_cost: float
    labour_cost_per_unit: float
    overhead_percentage: float
    target_margin_percentage: float
    tax_rate: float
    created_at: datetime
    is_active: bool

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify client exists and belongs to organization
    client = db.query(Client).filter(
        Client.id == product_data.client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found or access denied")
    
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/", response_model=List[ProductResponse])
def list_products(
    client_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Product).join(Client).filter(
        Client.organization_id == current_user.organization_id
    )
    
    if client_id:
        query = query.filter(Product.client_id == client_id)
        
    return query.all()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).join(Client).filter(
        Product.id == product_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).join(Client).filter(
        Product.id == product_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
