# backend/app/api/integrations.py

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from datetime import datetime

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Client
from app.services.integration_service import TallyIntegration, ZohoIntegration, ExcelCSVImport

router = APIRouter(tags=["integrations"])

# Tally endpoints
class TallyConfigRequest(BaseModel):
    tally_url: str
    tally_port: int = 9000
    company_name: str

@router.post("/tally/test-connection")
def test_tally_connection(
    request: TallyConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Test connection to Tally"""
    result = TallyIntegration.test_connection(request.tally_url, request.tally_port)
    return result

@router.post("/tally/sync-ledgers")
def sync_tally_ledgers(
    request: TallyConfigRequest,
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync ledgers from Tally to database"""
    
    # Fetch ledgers from Tally
    ledgers = TallyIntegration.fetch_ledgers(
        request.tally_url,
        request.tally_port,
        request.company_name
    )
    
    if not ledgers:
        return {"success": False, "message": "No ledgers found or connection failed"}
    
    # Sync to database
    result = TallyIntegration.sync_ledgers_to_db(db, client_id, ledgers)
    
    # Update client config
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        client.tally_config = {
            "url": request.tally_url,
            "port": request.tally_port,
            "company_name": request.company_name
        }
        db.commit()
    
    return result

# Zoho endpoints
@router.get("/zoho/auth-url")
def get_zoho_auth_url(current_user: User = Depends(get_current_user)):
    """Get Zoho OAuth authorization URL"""
    # These should come from environment variables
    import os
    client_id = os.getenv("ZOHO_CLIENT_ID")
    redirect_uri = os.getenv("ZOHO_REDIRECT_URI", "http://localhost:3000/integrations/zoho/callback")
    
    auth_url = ZohoIntegration.get_auth_url(client_id, redirect_uri)
    return {"auth_url": auth_url}

class ZohoTokenRequest(BaseModel):
    code: str
    client_id: int

@router.post("/zoho/exchange-token")
def exchange_zoho_token(
    request: ZohoTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange authorization code for tokens"""
    import os
    
    result = ZohoIntegration.exchange_code_for_tokens(
        request.code,
        os.getenv("ZOHO_CLIENT_ID"),
        os.getenv("ZOHO_CLIENT_SECRET"),
        os.getenv("ZOHO_REDIRECT_URI")
    )
    
    if "error" not in result:
        # Save tokens to client
        client = db.query(Client).filter(Client.id == request.client_id).first()
        if client:
            client.zoho_tokens = {
                "access_token": result.get("access_token"),
                "refresh_token": result.get("refresh_token"),
                "expires_at": datetime.utcnow().timestamp() + result.get("expires_in", 3600)
            }
            db.commit()
    
    return result

@router.post("/zoho/sync-invoices")
def sync_zoho_invoices(
    client_id: int,
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync invoices from Zoho Books"""
    
    # Get client tokens
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client or not client.zoho_tokens:
        return {"success": False, "message": "Zoho not connected"}
    
    access_token = client.zoho_tokens.get("access_token")
    
    # Fetch invoices
    invoices = ZohoIntegration.fetch_invoices(access_token, organization_id)
    
    if not invoices:
        return {"success": False, "message": "No invoices found"}
    
    # Sync to database
    result = ZohoIntegration.sync_invoices_to_db(db, client_id, invoices)
    return result

# Excel/CSV import endpoints
@router.post("/import/orders")
async def import_orders(
    file: UploadFile = File(...),
    client_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import orders from Excel or CSV file"""
    
    content = await file.read()
    result = ExcelCSVImport.import_orders_from_file(
        db, client_id, content, file.filename
    )
    return result

@router.post("/import/products")
async def import_products(
    file: UploadFile = File(...),
    client_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import products from Excel or CSV file"""
    
    content = await file.read()
    result = ExcelCSVImport.import_products_from_file(
        db, client_id, content, file.filename
    )
    return result
