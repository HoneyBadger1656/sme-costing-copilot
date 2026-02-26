# backend/app/services/costing_service.py

from sqlalchemy.orm import Session
from app.models.models import Order, OrderItem, Product, OrderEvaluation
from datetime import datetime, timedelta
from typing import Dict, List

class CostingService:
    
    @staticmethod
    def calculate_product_unit_cost(product: Product) -> Dict[str, float]:
        """Calculate detailed unit cost breakdown"""
        # Direct costs
        direct_cost = product.raw_material_cost + product.labour_cost_per_unit
        
        # Overhead
        overhead = direct_cost * (product.overhead_percentage / 100)
        
        # Total cost
        total_cost = direct_cost + overhead
        
        # Selling price (reverse-calculate from margin)
        if product.target_margin_percentage > 0:
            selling_price_before_tax = total_cost / (1 - product.target_margin_percentage / 100)
        else:
            selling_price_before_tax = total_cost  # No margin
        
        # Tax
        tax_amount = selling_price_before_tax * (product.tax_rate / 100)
        final_price = selling_price_before_tax + tax_amount
        
        return {
            "direct_cost": round(direct_cost, 2),
            "overhead": round(overhead, 2),
            "total_cost": round(total_cost, 2),
            "selling_price_before_tax": round(selling_price_before_tax, 2),
            "tax_amount": round(tax_amount, 2),
            "final_selling_price": round(final_price, 2),
            "margin_amount": round(final_price - total_cost - tax_amount, 2)
        }
    
    @staticmethod
    def evaluate_order(db: Session, order: Order) -> OrderEvaluation:
        """
        Evaluate order profitability and generate recommendations
        This is called after order items are created
        """
        # Recalculate totals
        total_cost = 0
        total_revenue = 0
        
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            
            if product:
                # Calculate costs at order time (locked prices)
                cost_breakdown = CostingService.calculate_product_unit_cost(product)
                
                item.unit_cost = cost_breakdown["total_cost"]
                item.unit_selling_price = cost_breakdown["final_selling_price"]
                item.total_cost = item.unit_cost * item.quantity
                item.total_selling_price = item.unit_selling_price * item.quantity
                item.margin = item.total_selling_price - item.total_cost
                
                total_cost += item.total_cost
                total_revenue += item.total_selling_price
        
        # Update order totals
        order.total_cost = round(total_cost, 2)
        order.total_selling_price = round(total_revenue, 2)
        order.gross_margin = round(total_revenue - total_cost, 2)
        
        if total_revenue > 0:
            order.margin_percentage = round((order.gross_margin / total_revenue) * 100, 2)
        else:
            order.margin_percentage = 0
        
        # Working capital impact
        order.working_capital_blocked = round(
            total_cost * (order.credit_days / 365), 2
        )
        
        # Calculate due date
        order.due_date = order.order_date + timedelta(days=order.credit_days)
        
        # Generate AI evaluation
        evaluation = CostingService._generate_evaluation(order)
        
        # Create or update evaluation record
        existing = db.query(OrderEvaluation).filter(
            OrderEvaluation.order_id == order.id
        ).first()
        
        if existing:
            existing.profitability_score = evaluation["score"]
            existing.risk_level = evaluation["risk"]
            existing.recommendations = evaluation["recommendations"]
            existing.margin_analysis = evaluation["margin_analysis"]
            existing.working_capital_impact = evaluation["wc_impact"]
            existing.should_accept = evaluation["should_accept"]
            existing.suggested_changes = evaluation["suggested_changes"]
        else:
            new_eval = OrderEvaluation(
                order_id=order.id,
                profitability_score=evaluation["score"],
                risk_level=evaluation["risk"],
                recommendations=evaluation["recommendations"],
                margin_analysis=evaluation["margin_analysis"],
                working_capital_impact=evaluation["wc_impact"],
                should_accept=evaluation["should_accept"],
                suggested_changes=evaluation["suggested_changes"]
            )
            db.add(new_eval)
        
        db.commit()
        db.refresh(order)
        
        return evaluation
    
    @staticmethod
    def _generate_evaluation(order: Order) -> Dict:
        """Generate evaluation recommendations based on business rules"""
        score = 100
        suggestions = []
        
        # Margin analysis
        if order.margin_percentage < 10:
            score -= 40
            risk = "high"
            margin_analysis = f"Margin of {order.margin_percentage}% is below recommended 10% minimum. Order may not be profitable after accounting for all costs."
            suggestions.append({
                "field": "margin",
                "current": f"{order.margin_percentage}%",
                "suggested": "15-20%",
                "reason": "Increase selling price or reduce costs to improve profitability"
            })
        elif order.margin_percentage < 15:
            score -= 20
            risk = "medium"
            margin_analysis = f"Margin of {order.margin_percentage}% is acceptable but below industry average of 15-20%."
        else:
            risk = "low"
            margin_analysis = f"Healthy margin of {order.margin_percentage}%. Order is profitable."
        
        # Working capital analysis
        if order.working_capital_blocked > order.total_selling_price * 0.3:
            score -= 20
            suggestions.append({
                "field": "credit_days",
                "current": f"{order.credit_days} days",
                "suggested": f"{max(15, order.credit_days - 15)} days",
                "reason": "High working capital blocked. Consider shorter credit terms or advance payment."
            })
            wc_impact = f"₹{order.working_capital_blocked:,.2f} will be blocked for {order.credit_days} days. This is {round(order.working_capital_blocked/order.total_selling_price*100, 1)}% of order value."
        else:
            wc_impact = f"Working capital impact is manageable at ₹{order.working_capital_blocked:,.2f} for {order.credit_days} days."
        
        # Overall recommendation
        should_accept = score >= 60
        
        if should_accept:
            recommendations = f"✓ ACCEPT this order. Profitability score: {score}/100. "
            if suggestions:
                recommendations += "Consider the suggested improvements for better margins."
        else:
            recommendations = f"⚠ REVIEW CAREFULLY. Profitability score: {score}/100. "
            recommendations += "This order has significant risks. " + " ".join([s["reason"] for s in suggestions[:2]])
        
        return {
            "score": score,
            "risk": risk,
            "recommendations": recommendations,
            "margin_analysis": margin_analysis,
            "wc_impact": wc_impact,
            "should_accept": should_accept,
            "suggested_changes": suggestions
        }
