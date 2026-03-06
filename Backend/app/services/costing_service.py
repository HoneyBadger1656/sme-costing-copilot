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
        
        # Trigger notification for order evaluation completion
        try:
            from app.services.notification_trigger_service import NotificationTriggerService
            
            # Get order owner/creator
            if order.created_by:
                trigger_service = NotificationTriggerService(db)
                
                # Prepare order data for notification
                order_data = {
                    'user_name': 'User',  # TODO: Get actual user name
                    'order_name': f'Order #{order.id}',
                    'order_id': order.id,
                    'total_cost': order.total_cost,
                    'margin_percentage': order.margin_percentage,
                    'status': 'Completed',
                    'order_url': f'/orders/{order.id}',
                    'insights': evaluation.get('recommendations', [])[:3]  # Top 3 recommendations
                }
                
                trigger_service.trigger_order_evaluation_complete(
                    order_id=order.id,
                    user_id=order.created_by,
                    order_data=order_data
                )
        except Exception as e:
            # Don't fail the evaluation if notification fails
            logger = __import__('app.logging_config', fromlist=['get_logger']).get_logger(__name__)
            logger.warning(
                "notification_trigger_failed",
                error=str(e),
                order_id=order.id
            )
        
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

    @staticmethod
    def calculate_product_cost(product_data: Dict) -> Dict[str, float]:
        """Calculate product cost from raw data (for testing)"""
        if product_data.get("raw_material_cost", 0) < 0:
            raise ValueError("Raw material cost cannot be negative")
        if product_data.get("labour_cost_per_unit", 0) < 0:
            raise ValueError("Labour cost cannot be negative")
        
        direct_cost = product_data["raw_material_cost"] + product_data["labour_cost_per_unit"]
        overhead_cost = direct_cost * (product_data["overhead_percentage"] / 100)
        total_cost = direct_cost + overhead_cost
        
        return {
            "direct_cost": round(direct_cost, 2),
            "overhead_cost": round(overhead_cost, 2),
            "total_cost": round(total_cost, 2)
        }
    
    @staticmethod
    def calculate_selling_price(cost: float, margin_percentage: float, tax_rate: float) -> Dict[str, float]:
        """Calculate selling price with margin and tax"""
        price_before_tax = cost / (1 - margin_percentage / 100)
        margin_amount = price_before_tax - cost
        tax_amount = price_before_tax * (tax_rate / 100)
        final_price = price_before_tax + tax_amount
        
        return {
            "price_before_tax": round(price_before_tax, 2),
            "margin_amount": round(margin_amount, 2),
            "tax_amount": round(tax_amount, 2),
            "final_price": round(final_price, 2)
        }
    
    @staticmethod
    def calculate_order_totals(order_items: List[Dict]) -> Dict[str, float]:
        """Calculate order totals from items"""
        total_quantity = sum(item["quantity"] for item in order_items)
        total_cost = 0
        total_selling_price = 0
        
        for item in order_items:
            product = item["product"]
            quantity = item["quantity"]
            
            cost_breakdown = CostingService.calculate_product_unit_cost(product)
            total_cost += cost_breakdown["total_cost"] * quantity
            total_selling_price += cost_breakdown["final_selling_price"] * quantity
        
        gross_margin = total_selling_price - total_cost
        
        return {
            "total_quantity": total_quantity,
            "total_cost": round(total_cost, 2),
            "total_selling_price": round(total_selling_price, 2),
            "gross_margin": round(gross_margin, 2)
        }
    
    @staticmethod
    def calculate_working_capital_impact(order_value: float, credit_days: int) -> Dict[str, float]:
        """Calculate working capital impact of credit terms"""
        blocked_capital = order_value
        daily_cost = order_value / 365
        # Assume 12% annual interest rate
        interest_rate = 0.12
        interest_cost = (order_value * interest_rate * credit_days) / 365
        
        return {
            "blocked_capital": round(blocked_capital, 2),
            "credit_days": credit_days,
            "daily_cost": round(daily_cost, 2),
            "interest_cost": round(interest_cost, 2)
        }
