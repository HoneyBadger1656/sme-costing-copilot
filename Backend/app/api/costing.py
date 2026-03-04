# backend/app/api/costing.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import Product, Order, OrderItem, BOMItem, User
from app.services.costing_service import CostingService
from app.services.costing_formulas import get_all_formulas, calculate_formula
from app.utils.rbac import require_role

router = APIRouter(tags=["costing"])

# ── Request / Response models ─────────────────────────────────────────

class ProductCostingRequest(BaseModel):
    raw_material_cost: float
    labour_cost_per_unit: float
    overhead_percentage: float = 10
    target_margin_percentage: float = 20
    tax_rate: float = 18

class ProductCostingResponse(BaseModel):
    direct_cost: float
    overhead: float
    total_cost: float
    selling_price_before_tax: float
    tax_amount: float
    final_selling_price: float
    margin_amount: float
    margin_percentage: float

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: float

class EvaluateOrderRequest(BaseModel):
    customer_name: str
    product_id: int
    selling_price: float
    cost_price: float
    quantity: float
    credit_days: int

class EvaluateOrderResponse(BaseModel):
    total_cost: float
    total_revenue: float
    gross_margin: float
    margin_percentage: float
    working_capital_blocked: float
    profitability_score: float
    risk_level: str
    recommendations: str
    should_accept: bool

class FormulaCalculateRequest(BaseModel):
    inputs: Dict[str, Any]

class BOMItemCreate(BaseModel):
    component_name: str
    quantity: float
    unit: str = "pcs"
    unit_cost: float
    notes: Optional[str] = None

class BOMItemResponse(BaseModel):
    id: int
    product_id: int
    component_name: str
    quantity: float
    unit: str
    unit_cost: float
    total_cost: float
    notes: Optional[str] = None


# ── Existing endpoints ────────────────────────────────────────────────

@router.post("/calculate-product-cost", response_model=ProductCostingResponse)
def calculate_product_cost(
    request: ProductCostingRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner"))
):
    """Quick cost calculation without saving to database (Accountant+ access)"""
    temp_product = Product(
        raw_material_cost=request.raw_material_cost,
        labour_cost_per_unit=request.labour_cost_per_unit,
        overhead_percentage=request.overhead_percentage,
        target_margin_percentage=request.target_margin_percentage,
        tax_rate=request.tax_rate
    )
    
    result = CostingService.calculate_product_unit_cost(temp_product)
    
    if result["final_selling_price"] > 0:
        result["margin_percentage"] = round(
            (result["margin_amount"] / result["final_selling_price"]) * 100, 2
        )
    else:
        result["margin_percentage"] = 0
    
    return result


@router.post("/evaluate-order", response_model=EvaluateOrderResponse)
def evaluate_order_quick(
    request: EvaluateOrderRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Quick order evaluation without creating order in DB (Accountant+ access)"""
    total_cost = request.cost_price * request.quantity
    total_revenue = request.selling_price * request.quantity
    gross_margin = total_revenue - total_cost
    
    if total_revenue > 0:
        margin_percentage = round((gross_margin / total_revenue) * 100, 2)
    else:
        margin_percentage = 0
    
    working_capital_blocked = round(total_cost * (request.credit_days / 365), 2)
    
    score = 100
    
    if margin_percentage < 10:
        score -= 40
        risk = "high"
        recommendations = f"Low margin of {margin_percentage}%. Consider increasing price or reducing costs."
        should_accept = False
    elif margin_percentage < 15:
        score -= 20
        risk = "medium"
        recommendations = f"Acceptable margin of {margin_percentage}%, but below 15% target."
        should_accept = True
    else:
        risk = "low"
        recommendations = f"Good margin of {margin_percentage}%. Order is profitable."
        should_accept = True
    
    if working_capital_blocked > total_revenue * 0.3:
        score -= 20
        recommendations += f" High working capital impact: ₹{working_capital_blocked:,.2f} blocked."
    
    return {
        "total_cost": round(total_cost, 2),
        "total_revenue": round(total_revenue, 2),
        "gross_margin": round(gross_margin, 2),
        "margin_percentage": margin_percentage,
        "working_capital_blocked": working_capital_blocked,
        "profitability_score": max(0, score),
        "risk_level": risk,
        "recommendations": recommendations,
        "should_accept": should_accept
    }


@router.post("/orders/{order_id}/recalculate")
def recalculate_order(
    order_id: int,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Recalculate an existing order's costs and evaluation (Accountant+ access)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    evaluation = CostingService.evaluate_order(db, order)
    
    return {
        "message": "Order recalculated successfully",
        "order_id": order.id,
        "total_cost": order.total_cost,
        "total_revenue": order.total_selling_price,
        "margin_percentage": order.margin_percentage,
        "evaluation": evaluation
    }


# ── Formula library endpoints ─────────────────────────────────────────

@router.get("/formulas")
def list_formulas():
    """Return all 82 costing formulas grouped by 13 categories."""
    return get_all_formulas()


@router.post("/formulas/{formula_id}/calculate")
def run_formula(
    formula_id: str,
    request: FormulaCalculateRequest,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
):
    """Calculate a specific formula given input values (Accountant+ access)"""
    try:
        result = calculate_formula(formula_id, request.inputs)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── BOM (Bill of Materials) endpoints ─────────────────────────────────

@router.get("/products/{product_id}/bom")
def list_bom_items(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all BOM components for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    items = db.query(BOMItem).filter(BOMItem.product_id == product_id).all()
    return [
        {
            "id": item.id,
            "product_id": item.product_id,
            "component_name": item.component_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_cost": item.unit_cost,
            "total_cost": round(item.quantity * item.unit_cost, 2),
            "notes": item.notes,
        }
        for item in items
    ]


@router.post("/products/{product_id}/bom")
def add_bom_item(
    product_id: int,
    request: BOMItemCreate,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Add a BOM component to a product (Accountant+ access)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    item = BOMItem(
        product_id=product_id,
        component_name=request.component_name,
        quantity=request.quantity,
        unit=request.unit,
        unit_cost=request.unit_cost,
        notes=request.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return {
        "id": item.id,
        "product_id": item.product_id,
        "component_name": item.component_name,
        "quantity": item.quantity,
        "unit": item.unit,
        "unit_cost": item.unit_cost,
        "total_cost": round(item.quantity * item.unit_cost, 2),
        "notes": item.notes,
    }


@router.delete("/bom/{bom_id}")
def delete_bom_item(
    bom_id: int,
    current_user: User = Depends(require_role("Accountant", "Admin", "Owner")),
    db: Session = Depends(get_db)
):
    """Delete a BOM component (Accountant+ access)"""
    item = db.query(BOMItem).filter(BOMItem.id == bom_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "BOM item deleted", "id": bom_id}
