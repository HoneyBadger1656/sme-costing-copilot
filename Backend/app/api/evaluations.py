from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import OrderEvaluation, Client, User
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
        Client.id == uuid.UUID(request.client_id),
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
    
    # Save to database
    evaluation = OrderEvaluation(
        client_id=client.id,
        evaluated_by=current_user.id,
        customer_name=request.customer_name,
        product_name=request.product_name,
        quantity=request.quantity,
        proposed_price=request.selling_price,
        proposed_credit_days=request.proposed_credit_days,
        contribution_margin=result['margin']['contribution_per_unit'],
        margin_percentage=result['margin']['margin_percentage'],
        working_capital_impact=result['working_capital']['wc_increase'],
        decision=result['decision'],
        reasons=str(result['reasons']),
        recommendation=result['recommendation']
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    return {
        "id": str(evaluation.id),
        "decision": result['decision'],
        "margin": result['margin'],
        "order_value": result['order_value'],
        "working_capital": result['working_capital'],
        "reasons": result['reasons'],
        "recommendation": result['recommendation'],
        "created_at": evaluation.created_at.isoformat()
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
    
    evaluations = db.query(OrderEvaluation).filter(
        OrderEvaluation.client_id == client.id
    ).order_by(OrderEvaluation.created_at.desc()).limit(50).all()
    
    return {
        "client_id": client_id,
        "client_name": client.business_name,
        "evaluations": [
            {
                "id": str(e.id),
                "customer_name": e.customer_name,
                "product_name": e.product_name,
                "decision": e.decision,
                "margin_percentage": float(e.margin_percentage),
                "order_value": float(e.proposed_price * e.quantity),
                "created_at": e.created_at.isoformat()
            }
            for e in evaluations
        ]
    }
