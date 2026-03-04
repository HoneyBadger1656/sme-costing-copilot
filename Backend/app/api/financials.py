# backend/app/api/financials.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Dict, Any

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User
from app.services.financial_service import FinancialService
from app.services.financial_formulas import get_all_formulas, calculate_formula
from app.utils.rbac import require_role

router = APIRouter(tags=["financials"])

@router.get("/profitability")
@require_role(["Accountant", "Admin", "Owner"])
def get_profitability(
    client_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profitability summary (Accountant+ access)"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    summary = FinancialService.get_profitability_summary(
        db, client_id, start_date, end_date
    )
    
    return summary

@router.get("/receivables")
@require_role(["Accountant", "Admin", "Owner"])
def get_receivables(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get receivables analysis (Accountant+ access)"""
    summary = FinancialService.get_receivables_summary(db, client_id)
    return summary

@router.get("/payables")
@require_role(["Accountant", "Admin", "Owner"])
def get_payables(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payables analysis (Accountant+ access)"""
    summary = FinancialService.get_payables_summary(db, client_id)
    return summary

@router.get("/cash-flow-forecast")
@require_role(["Accountant", "Admin", "Owner"])
def get_cash_flow_forecast(
    client_id: int,
    days: int = Query(30, description="Forecast period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cash flow forecast (Accountant+ access)"""
    forecast = FinancialService.get_cash_flow_forecast(db, client_id, days)
    return forecast

# ── Financial formulas endpoints ─────────────────────────────────────

class FormulaCalculateRequest(BaseModel):
    inputs: Dict[str, Any]

@router.get("/formulas")
def list_financial_formulas():
    """Return all 101 financial formulas grouped by 18 categories."""
    return get_all_formulas()


@router.post("/formulas/{formula_id}/calculate")
@require_role(["Accountant", "Admin", "Owner"])
def calculate_financial_formula(
    formula_id: str,
    request: FormulaCalculateRequest,
    current_user: User = Depends(get_current_user),
):
    """Calculate a specific financial formula given input values (Accountant+ access)"""
    try:
        result = calculate_formula(formula_id, request.inputs)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
