# backend/app/services/financial_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.models import Order, Ledger, Client
from datetime import datetime, timedelta
from typing import Dict, List

class FinancialService:
    
    @staticmethod
    def get_profitability_summary(
        db: Session,
        client_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """Calculate order-wise and period profitability"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get orders in period
        orders = db.query(Order).filter(
            Order.client_id == client_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status != "draft"
        ).all()
        
        total_revenue = sum(o.total_selling_price for o in orders)
        total_cost = sum(o.total_cost for o in orders)
        gross_profit = total_revenue - total_cost
        
        avg_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Group by customer
        customer_profitability = {}
        for order in orders:
            if order.customer_name not in customer_profitability:
                customer_profitability[order.customer_name] = {
                    "revenue": 0,
                    "cost": 0,
                    "margin": 0,
                    "order_count": 0
                }
            
            customer_profitability[order.customer_name]["revenue"] += order.total_selling_price
            customer_profitability[order.customer_name]["cost"] += order.total_cost
            customer_profitability[order.customer_name]["order_count"] += 1
        
        # Calculate margins
        for customer in customer_profitability:
            data = customer_profitability[customer]
            data["margin"] = data["revenue"] - data["cost"]
            data["margin_percent"] = (data["margin"] / data["revenue"] * 100) if data["revenue"] > 0 else 0
        
        # Sort by margin
        top_customers = sorted(
            customer_profitability.items(),
            key=lambda x: x[1]["margin"],
            reverse=True
        )[:10]
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "gross_profit": round(gross_profit, 2),
                "margin_percentage": round(avg_margin, 2),
                "order_count": len(orders)
            },
            "top_customers": [
                {
                    "name": name,
                    "revenue": round(data["revenue"], 2),
                    "margin": round(data["margin"], 2),
                    "margin_percent": round(data["margin_percent"], 2),
                    "order_count": data["order_count"]
                }
                for name, data in top_customers
            ]
        }
    
    @staticmethod
    def get_receivables_summary(db: Session, client_id: int) -> Dict:
        """Get outstanding receivables analysis"""
        
        # Outstanding ledger entries
        outstanding = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding"
        ).all()
        
        total_outstanding = sum(l.amount for l in outstanding)
        
        # Age analysis
        now = datetime.utcnow()
        age_buckets = {
            "0-30": 0,
            "31-60": 0,
            "61-90": 0,
            "90+": 0
        }
        
        overdue_items = []
        
        for ledger in outstanding:
            days_old = (now - ledger.transaction_date).days
            
            if days_old <= 30:
                age_buckets["0-30"] += ledger.amount
            elif days_old <= 60:
                age_buckets["31-60"] += ledger.amount
            elif days_old <= 90:
                age_buckets["61-90"] += ledger.amount
            else:
                age_buckets["90+"] += ledger.amount
            
            # Overdue check
            if ledger.due_date and now > ledger.due_date:
                overdue_items.append({
                    "party_name": ledger.party_name,
                    "amount": round(ledger.amount, 2),
                    "due_date": ledger.due_date.isoformat(),
                    "days_overdue": (now - ledger.due_date).days
                })
        
        # Sort by days overdue
        overdue_items.sort(key=lambda x: x["days_overdue"], reverse=True)
        
        return {
            "total_outstanding": round(total_outstanding, 2),
            "age_analysis": {k: round(v, 2) for k, v in age_buckets.items()},
            "overdue_count": len(overdue_items),
            "overdue_amount": round(sum(i["amount"] for i in overdue_items), 2),
            "top_overdue": overdue_items[:10]
        }
    
    @staticmethod
    def get_payables_summary(db: Session, client_id: int) -> Dict:
        """Get outstanding payables analysis"""
        
        outstanding = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "payable",
            Ledger.status == "outstanding"
        ).all()
        
        total_outstanding = sum(l.amount for l in outstanding)
        
        # Age analysis
        now = datetime.utcnow()
        age_buckets = {
            "0-30": 0,
            "31-60": 0,
            "61-90": 0,
            "90+": 0
        }
        
        due_soon = []
        
        for ledger in outstanding:
            days_old = (now - ledger.transaction_date).days
            
            if days_old <= 30:
                age_buckets["0-30"] += ledger.amount
            elif days_old <= 60:
                age_buckets["31-60"] += ledger.amount
            elif days_old <= 90:
                age_buckets["61-90"] += ledger.amount
            else:
                age_buckets["90+"] += ledger.amount
            
            # Due in next 7 days
            if ledger.due_date:
                days_until_due = (ledger.due_date - now).days
                if 0 <= days_until_due <= 7:
                    due_soon.append({
                        "party_name": ledger.party_name,
                        "amount": round(ledger.amount, 2),
                        "due_date": ledger.due_date.isoformat(),
                        "days_until_due": days_until_due
                    })
        
        due_soon.sort(key=lambda x: x["days_until_due"])
        
        return {
            "total_outstanding": round(total_outstanding, 2),
            "age_analysis": {k: round(v, 2) for k, v in age_buckets.items()},
            "due_in_7_days": round(sum(i["amount"] for i in due_soon), 2),
            "upcoming_payments": due_soon
        }
    
    @staticmethod
    def get_cash_flow_forecast(db: Session, client_id: int, days: int = 30) -> Dict:
        """Simple cash flow forecast based on receivables and payables"""
        
        now = datetime.utcnow()
        forecast_end = now + timedelta(days=days)
        
        # Expected cash inflows (receivables due in period)
        inflows = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding",
            Ledger.due_date >= now,
            Ledger.due_date <= forecast_end
        ).all()
        
        # Expected cash outflows (payables due in period)
        outflows = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "payable",
            Ledger.status == "outstanding",
            Ledger.due_date >= now,
            Ledger.due_date <= forecast_end
        ).all()
        
        total_inflow = sum(l.amount for l in inflows)
        total_outflow = sum(l.amount for l in outflows)
        net_cash_flow = total_inflow - total_outflow
        
        return {
            "forecast_period_days": days,
            "expected_inflows": round(total_inflow, 2),
            "expected_outflows": round(total_outflow, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "cash_position": "positive" if net_cash_flow > 0 else "negative",
            "recommendation": FinancialService._cash_flow_recommendation(net_cash_flow, total_outflow)
        }
    
    @staticmethod
    def _cash_flow_recommendation(net_flow: float, outflows: float) -> str:
        """Generate cash flow recommendation"""
        if net_flow < 0:
            return f"⚠ Negative cash flow of ₹{abs(net_flow):,.0f} expected. Arrange credit line or accelerate collections to cover ₹{outflows:,.0f} in payments."
        elif net_flow < outflows * 0.2:
            return f"⚠ Cash flow is tight (₹{net_flow:,.0f} surplus). Monitor closely and delay non-essential payments if needed."
        else:
            return f"✓ Healthy cash surplus of ₹{net_flow:,.0f} expected. Good liquidity position."

    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
        """Calculate current ratio"""
        if current_liabilities == 0:
            raise ValueError("Current liabilities cannot be zero")
        return round(current_assets / current_liabilities, 2)
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
        """Calculate quick ratio (acid test ratio)"""
        if current_liabilities == 0:
            raise ValueError("Current liabilities cannot be zero")
        quick_assets = current_assets - inventory
        return round(quick_assets / current_liabilities, 2)
    
    @staticmethod
    def calculate_debt_equity_ratio(total_debt: float, total_equity: float) -> float:
        """Calculate debt to equity ratio"""
        if total_equity == 0:
            raise ValueError("Total equity cannot be zero")
        return round(total_debt / total_equity, 2)
    
    @staticmethod
    def calculate_gross_margin(revenue: float, cogs: float) -> float:
        """Calculate gross margin percentage"""
        if revenue == 0:
            return 0.0
        gross_profit = revenue - cogs
        return round((gross_profit / revenue) * 100, 2)
    
    @staticmethod
    def calculate_net_margin(revenue: float, net_income: float) -> float:
        """Calculate net margin percentage"""
        if revenue == 0:
            return 0.0
        return round((net_income / revenue) * 100, 2)
    
    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> float:
        """Calculate return on assets percentage"""
        if total_assets == 0:
            raise ValueError("Total assets cannot be zero")
        return round((net_income / total_assets) * 100, 2)
    
    @staticmethod
    def calculate_roe(net_income: float, total_equity: float) -> float:
        """Calculate return on equity percentage"""
        if total_equity == 0:
            raise ValueError("Total equity cannot be zero")
        return round((net_income / total_equity) * 100, 2)
    
    @staticmethod
    def calculate_working_capital(current_assets: float, current_liabilities: float) -> float:
        """Calculate working capital"""
        return round(current_assets - current_liabilities, 2)
    
    @staticmethod
    def calculate_cash_conversion_cycle(
        days_inventory_outstanding: int,
        days_sales_outstanding: int,
        days_payables_outstanding: int
    ) -> int:
        """Calculate cash conversion cycle in days"""
        return days_inventory_outstanding + days_sales_outstanding - days_payables_outstanding
