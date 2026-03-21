from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.core.database import get_db
from app.models.models import User, GSTConfiguration, HSNSACMaster, GSTReturn, GSTReconciliation
from app.api.auth import get_current_user
from app.services.gst_service import GSTService
from app.utils.rbac import require_role
from pydantic import BaseModel

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class GSTConfigCreate(BaseModel):
    client_id: int
    gstin: str
    legal_name: str
    trade_name: Optional[str] = None
    state_code: str
    filing_frequency: str = "monthly"  # monthly, quarterly
    turnover_threshold: float = 50000000  # ₹5 crore default

class HSNCreate(BaseModel):
    hsn_sac_code: str
    description: str
    gst_rate: float
    type: str = "HSN"  # HSN or SAC
    category: Optional[str] = None

class GSTR1GenerateRequest(BaseModel):
    client_id: int
    period: str  # YYYY-MM

class GSTR3BGenerateRequest(BaseModel):
    client_id: int
    period: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/config")
def create_or_update_gst_config(
    payload: GSTConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    is_valid, error_segment = GSTService.validate_gstin(payload.gstin)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid GSTIN: error in {error_segment}")

    existing = db.query(GSTConfiguration).filter(
        GSTConfiguration.client_id == payload.client_id
    ).first()

    if existing:
        for field, val in payload.dict().items():
            setattr(existing, field, val)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        config = GSTConfiguration(
            organization_id=current_user.organization_id,
            **payload.dict(),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config


@router.get("/config/{client_id}")
def get_gst_config(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    config = db.query(GSTConfiguration).filter(
        GSTConfiguration.client_id == client_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="GST configuration not found")
    return config


@router.get("/hsn")
def list_hsn(
    q: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    query = db.query(HSNSACMaster)
    if q:
        query = query.filter(
            HSNSACMaster.hsn_sac_code.ilike(f"%{q}%") |
            HSNSACMaster.description.ilike(f"%{q}%")
        )
    return query.limit(100).all()


@router.post("/hsn")
def create_hsn(
    payload: HSNCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["admin", "owner"])
    hsn = HSNSACMaster(**payload.dict())
    db.add(hsn)
    db.commit()
    db.refresh(hsn)
    return hsn


@router.post("/gstr1/generate")
def generate_gstr1(
    payload: GSTR1GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    result = GSTService.generate_gstr1(payload.client_id, payload.period, db)
    return result


@router.get("/gstr1/{client_id}/{period}")
def get_gstr1(
    client_id: int,
    period: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    ret = db.query(GSTReturn).filter(
        GSTReturn.client_id == client_id,
        GSTReturn.period == period,
        GSTReturn.return_type == "GSTR-1",
    ).first()
    if not ret:
        raise HTTPException(status_code=404, detail="GSTR-1 not found for this period")
    return ret


@router.post("/gstr1/{return_id}/submit")
def submit_gstr1(
    return_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    ret = db.query(GSTReturn).filter(GSTReturn.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="GST return not found")
    if ret.status not in ("draft",):
        raise HTTPException(status_code=400, detail=f"Cannot submit return in status '{ret.status}'")
    result = GSTService.submit_for_review(return_id, db)
    return result


@router.post("/gstr3b/generate")
def generate_gstr3b(
    payload: GSTR3BGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    result = GSTService.generate_gstr3b(payload.client_id, payload.period, db)
    return result


@router.post("/reconciliation/upload")
async def upload_reconciliation(
    client_id: int,
    period: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    content = await file.read()
    try:
        gstr2_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    result = GSTService.reconcile_itc(client_id, period, gstr2_data, db)
    return result


@router.get("/reconciliation/{client_id}/{period}")
def get_reconciliation(
    client_id: int,
    period: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    rec = db.query(GSTReconciliation).filter(
        GSTReconciliation.client_id == client_id,
        GSTReconciliation.period == period,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    return rec


@router.get("/compliance-calendar/{client_id}")
def get_compliance_calendar(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    return GSTService.get_compliance_calendar(client_id, db)
