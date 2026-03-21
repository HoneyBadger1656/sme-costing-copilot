from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User
from app.api.auth import get_current_user
from app.services.financial_service import FinancialService
from app.utils.rbac import require_role

router = APIRouter()


class CreditLimitRequest(BaseModel):
    amount: float


@router.get("/aging/{client_id}")
def get_aging_report(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return FinancialService.get_aging_report(client_id, db)


@router.get("/forecast/{client_id}")
def get_cash_flow_forecast(
    client_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return FinancialService.get_cash_flow_forecast(db, client_id, days)


@router.get("/cycle/{client_id}")
def get_working_capital_cycle(
    client_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return FinancialService.get_working_capital_cycle(client_id, days, db)


@router.get("/collection-efficiency")
def get_collection_efficiency(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["accountant", "admin", "owner"])
    return FinancialService.get_collection_efficiency(current_user.organization_id, db)


@router.post("/credit-limit/{client_id}")
def set_credit_limit(
    client_id: int,
    payload: CreditLimitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["admin", "owner"])
    return FinancialService.set_credit_limit(client_id, payload.amount, current_user.id, db)


@router.get("/credit-limit/{client_id}")
def get_credit_limit(
    client_id: int,
    order_amount: float = Query(0.0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    return FinancialService.check_credit_limit(client_id, order_amount, db)
