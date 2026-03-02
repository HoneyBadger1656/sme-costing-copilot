from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.models import Client, User
from app.services.costing_engine import CostingEngine
from app.api.auth import get_current_user

router = APIRouter()

# Schemas
class OrderEvaluationRequest(BaseModel):
    client_id: str
    customer_name: str
    product_name: str
    selling_price: float
    cost_price: float
    quantity: float
    proposed_credit_days: int
    current_debtors: Optional[float] = 0
    annual_sales: Optional[float] = 0

class ScenarioRequest(BaseModel):
    client_id: str
    base_scenario: dict
    alternative_scenarios: List[dict]

class OrderEvaluationResponse(BaseModel):
    id: str
    decision: str
    margin: dict
    order_value: float
    working_capital: dict
    reasons: List[str]
    recommendation: str
    created_at: str

# Endpoints
@router.post("/evaluate", response_model=OrderEvaluationResponse)
def evaluate_order(
    request: OrderEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get client
    client = db.query(Client).filter(
        Client.id == request.client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Initialize engine
    engine = CostingEngine({
        "industry": client.industry or "manufacturing",
        "annual_revenue": float(client.annual_revenue or 0)
    })
    
    # Evaluate order
    result = engine.evaluate_order_decision(
        product_name=request.product_name,
        selling_price=request.selling_price,
        cost_price=request.cost_price,
        quantity=request.quantity,
        customer_name=request.customer_name,
        proposed_credit_days=request.proposed_credit_days,
        current_debtors=request.current_debtors,
        annual_sales=request.annual_sales
    )
    
    # Return evaluation result (no DB save needed for quick evaluation)
    return {
        "id": "quick-eval",
        "decision": result['decision'],
        "margin": result['margin'],
        "order_value": result['order_value'],
        "working_capital": result['working_capital'],
        "reasons": result['reasons'],
        "recommendation": result['recommendation'],
        "created_at": datetime.utcnow().isoformat()
    }

@router.post("/compare-scenarios")
def compare_scenarios(
    request: ScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get client
    client = db.query(Client).filter(
        Client.id == request.client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Initialize engine
    engine = CostingEngine({
        "industry": client.industry or "manufacturing",
        "annual_revenue": float(client.annual_revenue or 0)
    })
    
    # Compare scenarios
    comparison = engine.compare_scenarios(
        base_scenario=request.base_scenario,
        alternative_scenarios=request.alternative_scenarios
    )
    
    return comparison

@router.get("/history/{client_id}")
def get_evaluation_history(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify client belongs to user's organization
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Query evaluations through Orders that belong to this client
    from app.models.models import Order, OrderEvaluation
    evaluations = (
        db.query(OrderEvaluation)
        .join(Order, Order.id == OrderEvaluation.order_id)
        .filter(Order.client_id == client.id)
        .order_by(OrderEvaluation.created_at.desc())
        .limit(50)
        .all()
    )
    
    return {
        "client_id": client_id,
        "client_name": client.business_name,
        "evaluations": [
            {
                "id": e.id,
                "profitability_score": e.profitability_score,
                "risk_level": e.risk_level,
                "should_accept": e.should_accept,
                "recommendations": e.recommendations,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in evaluations
        ]
    }
