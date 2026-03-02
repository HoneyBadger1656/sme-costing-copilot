# backend/app/api/scenarios.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import Scenario, User
from app.services.scenario_service import ScenarioService

router = APIRouter(tags=["scenarios"])

class CreateScenarioRequest(BaseModel):
    name: str
    description: str = None
    changes: Dict  # {"raw_material_cost_change": -10, "credit_days_change": 15}

class ScenarioResponse(BaseModel):
    id: int
    name: str
    description: str = None
    changes: Dict
    impact_summary: Dict
    created_at: str

@router.post("", response_model=ScenarioResponse)
def create_scenario(
    request: CreateScenarioRequest,
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new what-if scenario"""
    scenario = ScenarioService.create_scenario(
        db=db,
        client_id=client_id,
        name=request.name,
        changes=request.changes,
        description=request.description
    )
    
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "changes": scenario.changes,
        "impact_summary": scenario.impact_summary,
        "created_at": scenario.created_at.isoformat()
    }

@router.get("", response_model=List[ScenarioResponse])
def list_scenarios(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all scenarios for a client"""
    scenarios = db.query(Scenario).filter(
        Scenario.client_id == client_id
    ).order_by(Scenario.created_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "changes": s.changes,
            "impact_summary": s.impact_summary,
            "created_at": s.created_at.isoformat()
        }
        for s in scenarios
    ]

@router.post("/compare")
def compare_scenarios(
    scenario_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple scenarios side by side"""
    comparison = ScenarioService.compare_scenarios(db, scenario_ids)
    return comparison

@router.delete("/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scenario"""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    db.delete(scenario)
    db.commit()
    
    return {"message": "Scenario deleted successfully"}
