# backend/app/api/financials.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User
from app.services.financial_service import FinancialService

router = APIRouter(prefix="/api/financials", tags=["financials"])

@router.get("/profitability")
def get_profitability(
    client_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profitability summary"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    summary = FinancialService.get_profitability_summary(
        db, client_id, start_date, end_date
    )
    
    return summary

@router.get("/receivables")
def get_receivables(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get receivables analysis"""
    summary = FinancialService.get_receivables_summary(db, client_id)
    return summary

@router.get("/payables")
def get_payables(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payables analysis"""
    summary = FinancialService.get_payables_summary(db, client_id)
    return summary

@router.get("/cash-flow-forecast")
def get_cash_flow_forecast(
    client_id: int,
    days: int = Query(30, description="Forecast period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cash flow forecast"""
    forecast = FinancialService.get_cash_flow_forecast(db, client_id, days)
    return forecast
