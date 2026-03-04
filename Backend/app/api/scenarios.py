# backend/app/api/scenarios.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel
import re

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import Scenario, User
from app.services.scenario_service import ScenarioService
from app.utils.rbac import require_role

router = APIRouter(tags=["scenarios"])

class CreateScenarioRequest(BaseModel):
    name: str
    description: str = None
    changes: Dict  # {"raw_material_cost_change": -10, "credit_days_change": 15}

class QuickScenarioRequest(BaseModel):
    text: str  # Natural language input like "What if raw material costs go up by 15%?"

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
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Create a new what-if scenario (Accountant+ access)"""
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
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Compare multiple scenarios side by side (Accountant+ access)"""
    comparison = ScenarioService.compare_scenarios(db, scenario_ids)
    return comparison

@router.delete("/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Delete a scenario (Accountant+ access)"""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    db.delete(scenario)
    db.commit()
    
    return {"message": "Scenario deleted successfully"}

@router.post("/parse-quick-scenario")
def parse_quick_scenario(
    request: QuickScenarioRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner"))
):
    """Parse natural language scenario input into structured changes (Accountant+ access)"""
    text = request.text.lower()
    changes = {}
    name = request.text[:50] + "..." if len(request.text) > 50 else request.text
    
    # Parse raw material cost changes
    rm_patterns = [
        r"raw material.*?(?:up|increase|rise).*?(\d+)%",
        r"raw material.*?(?:down|decrease|reduce).*?(\d+)%",
        r"rm.*?(?:up|increase|rise).*?(\d+)%",
        r"rm.*?(?:down|decrease|reduce).*?(\d+)%",
        r"material cost.*?(?:up|increase|rise).*?₹?(\d+)",
        r"material cost.*?(?:down|decrease|reduce).*?₹?(\d+)"
    ]
    
    for pattern in rm_patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            if "up" in pattern or "increase" in pattern or "rise" in pattern:
                if "%" in pattern:
                    changes["raw_material_cost_change"] = value  # Assume base cost of ₹100 for % calculation
                else:
                    changes["raw_material_cost_change"] = value
            else:
                if "%" in pattern:
                    changes["raw_material_cost_change"] = -value
                else:
                    changes["raw_material_cost_change"] = -value
            break
    
    # Parse labour cost changes
    labour_patterns = [
        r"labour.*?(?:up|increase|rise).*?₹?(\d+)",
        r"labour.*?(?:down|decrease|reduce).*?₹?(\d+)",
        r"labor.*?(?:up|increase|rise).*?₹?(\d+)",
        r"labor.*?(?:down|decrease|reduce).*?₹?(\d+)"
    ]
    
    for pattern in labour_patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            if "up" in pattern or "increase" in pattern or "rise" in pattern:
                changes["labour_cost_change"] = value
            else:
                changes["labour_cost_change"] = -value
            break
    
    # Parse selling price changes
    price_patterns = [
        r"price.*?(?:up|increase|rise).*?₹?(\d+)",
        r"price.*?(?:down|decrease|reduce).*?₹?(\d+)",
        r"selling price.*?(?:up|increase|rise).*?₹?(\d+)",
        r"selling price.*?(?:down|decrease|reduce).*?₹?(\d+)"
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            if "up" in pattern or "increase" in pattern or "rise" in pattern:
                changes["selling_price_change"] = value
            else:
                changes["selling_price_change"] = -value
            break
    
    # Parse volume changes
    volume_patterns = [
        r"volume.*?(?:up|increase|rise).*?(\d+)%",
        r"volume.*?(?:down|decrease|reduce).*?(\d+)%",
        r"orders.*?(?:up|increase|rise).*?(\d+)%",
        r"orders.*?(?:down|decrease|reduce).*?(\d+)%"
    ]
    
    for pattern in volume_patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            if "up" in pattern or "increase" in pattern or "rise" in pattern:
                changes["volume_change_percent"] = value
            else:
                changes["volume_change_percent"] = -value
            break
    
    # Parse credit days changes
    credit_patterns = [
        r"credit.*?(\d+).*?days",
        r"payment.*?(\d+).*?days",
        r"(\d+).*?days.*?credit"
    ]
    
    for pattern in credit_patterns:
        match = re.search(pattern, text)
        if match:
            value = int(match.group(1))
            if "extend" in text or "increase" in text or "more" in text:
                changes["credit_days_change"] = value
            elif "reduce" in text or "decrease" in text or "less" in text:
                changes["credit_days_change"] = -value
            else:
                changes["credit_days_change"] = value  # Default to increase
            break
    
    # Parse overhead changes
    overhead_patterns = [
        r"overhead.*?(?:up|increase|rise).*?(\d+)%",
        r"overhead.*?(?:down|decrease|reduce).*?(\d+)%"
    ]
    
    for pattern in overhead_patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            if "up" in pattern or "increase" in pattern or "rise" in pattern:
                changes["overhead_percent_change"] = value
            else:
                changes["overhead_percent_change"] = -value
            break
    
    return {
        "name": name,
        "changes": changes,
        "description": f"Auto-generated from: {request.text}"
    }
