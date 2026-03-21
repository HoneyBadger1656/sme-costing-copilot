from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User, EInvoice
from app.api.auth import get_current_user
from app.services.einvoice_service import EInvoiceService
from app.utils.rbac import require_role

router = APIRouter()


class CancelIRNRequest(BaseModel):
    reason: str


@router.post("/generate/{order_id}")
def generate_irn(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return EInvoiceService.generate_irn(order_id, db)


@router.get("/{order_id}")
def get_einvoice(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    return EInvoiceService.get_einvoice(order_id, db)


@router.post("/cancel/{order_id}")
def cancel_irn(
    order_id: int,
    payload: CancelIRNRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return EInvoiceService.cancel_irn(order_id, payload.reason, db)
