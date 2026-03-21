from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User
from app.api.auth import get_current_user
from app.services.ewaybill_service import EWayBillService
from app.utils.rbac import require_role

router = APIRouter()


class GenerateEWBRequest(BaseModel):
    transporter_gstin: Optional[str] = None
    vehicle_number: Optional[str] = None
    transport_mode: str = "road"  # road, rail, air, ship
    distance_km: int = 0
    transporter_name: Optional[str] = None


class CancelEWBRequest(BaseModel):
    reason: str


class AddTransporterRequest(BaseModel):
    name: str
    gstin: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


@router.post("/generate/{order_id}")
def generate_ewb(
    order_id: int,
    payload: GenerateEWBRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return EWayBillService.generate_ewb(order_id, payload.dict(), db)


@router.get("/{order_id}")
def get_ewb(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    return EWayBillService.get_ewb(order_id, db)


@router.post("/cancel/{order_id}")
def cancel_ewb(
    order_id: int,
    payload: CancelEWBRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return EWayBillService.cancel_ewb(order_id, payload.reason, db)


@router.get("/transporters")
def list_transporters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    return EWayBillService.list_transporters(current_user.organization_id, db)


@router.post("/transporters")
def add_transporter(
    payload: AddTransporterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return EWayBillService.add_transporter(
        organization_id=current_user.organization_id,
        name=payload.name,
        gstin=payload.gstin,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        db=db,
    )
