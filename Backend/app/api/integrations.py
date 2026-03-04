# backend/app/api/integrations.py

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from datetime import datetime

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Client
from app.services.integration_service import TallyIntegration, ZohoIntegration, ExcelCSVImport
from app.logging_config import get_logger
from app.utils.rbac import require_role

# Import Celery tasks
try:
    from app.tasks import sync_tally_ledgers_task, sync_zoho_invoices_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = get_logger(__name__)
router = APIRouter(tags=["integrations"])

# Tally endpoints
class TallyConfigRequest(BaseModel):
    tally_url: str
    tally_port: int = 9000
    company_name: str

@router.post("/tally/test-connection")
def test_tally_connection(
    request: TallyConfigRequest,
    current_user: User = Depends(require_role("Admin", "Owner"))
):
    """Test connection to Tally (Admin/Owner only)"""
    result = TallyIntegration.test_connection(request.tally_url, request.tally_port)
    return result

@router.post("/tally/sync-ledgers")
def sync_tally_ledgers(
    request: TallyConfigRequest,
    client_id: int,
    background: bool = True,
    current_user: User = Depends(require_role("Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Sync ledgers from Tally to database (Admin/Owner only)
    
    Args:
        background: If True, run as background task (requires Celery)
    """
    
    # Verify client access
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    tally_config = {
        "url": request.tally_url,
        "port": request.tally_port,
        "company_name": request.company_name
    }
    
    # Run as background task if Celery is available and requested
    if background and CELERY_AVAILABLE:
        task = sync_tally_ledgers_task.delay(client_id, tally_config)
        
        logger.info("tally_sync_queued", 
                   client_id=client_id,
                   task_id=task.id,
                   organization_id=current_user.organization_id)
        
        return {
            "task_id": task.id,
            "status": "processing",
            "message": "Tally sync started in background"
        }
    
    # Otherwise run synchronously (fallback)
    logger.warning("tally_sync_synchronous", 
                  client_id=client_id,
                  reason="celery_unavailable" if not CELERY_AVAILABLE else "background_disabled")
    
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
    client.tally_config = tally_config
    db.commit()
    
    return result

# Zoho endpoints
@router.get("/zoho/auth-url")
def get_zoho_auth_url(current_user: User = Depends(require_role("Admin", "Owner"))):
    """Get Zoho OAuth authorization URL (Admin/Owner only)"""
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
    current_user: User = Depends(require_role("Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Exchange authorization code for tokens (Admin/Owner only)"""
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
    background: bool = True,
    current_user: User = Depends(require_role("Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """
    Sync invoices from Zoho Books (Admin/Owner only)
    
    Args:
        background: If True, run as background task (requires Celery)
    """
    
    # Verify client access
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client or not client.zoho_tokens:
        return {"success": False, "message": "Zoho not connected"}
    
    # Run as background task if Celery is available and requested
    if background and CELERY_AVAILABLE:
        task = sync_zoho_invoices_task.delay(client_id, organization_id)
        
        logger.info("zoho_sync_queued",
                   client_id=client_id,
                   task_id=task.id,
                   organization_id=current_user.organization_id)
        
        return {
            "task_id": task.id,
            "status": "processing",
            "message": "Zoho sync started in background"
        }
    
    # Otherwise run synchronously (fallback)
    logger.warning("zoho_sync_synchronous",
                  client_id=client_id,
                  reason="celery_unavailable" if not CELERY_AVAILABLE else "background_disabled")
    
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
    current_user: User = Depends(require_role("Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Import orders from Excel or CSV file (Admin/Owner only)"""
    
    content = await file.read()
    result = ExcelCSVImport.import_orders_from_file(
        db, client_id, content, file.filename
    )
    return result

@router.post("/import/products")
async def import_products(
    file: UploadFile = File(...),
    client_id: int = 1,
    current_user: User = Depends(require_role("Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Import products from Excel or CSV file (Admin/Owner only)"""
    
    content = await file.read()
    result = ExcelCSVImport.import_products_from_file(
        db, client_id, content, file.filename
    )
    return result


@router.get("/tasks/{task_id}")
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a background task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status and result
    """
    if not CELERY_AVAILABLE:
        return {"error": "Background tasks not available"}
    
    from celery.result import AsyncResult
    from app.celery_app import celery_app
    
    task = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task.state,
        "ready": task.ready(),
        "successful": task.successful() if task.ready() else None
    }
    
    if task.ready():
        if task.successful():
            response["result"] = task.result
        else:
            response["error"] = str(task.info)
    
    return response
