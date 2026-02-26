# backend/app/services/scenario_service.py

from sqlalchemy.orm import Session
from app.models.models import Scenario, Client, Product, Order
from typing import Dict, List
from datetime import datetime

class ScenarioService:
    
    @staticmethod
    def create_scenario(
        db: Session,
        client_id: int,
        name: str,
        changes: Dict,
        description: str = None
    ) -> Scenario:
        """
        Create a what-if scenario
        
        changes format: {
            "raw_material_cost_change": -10,  # ₹10 reduction
            "credit_days_change": +15,         # 15 more days
            "volume_change_percent": +20,      # 20% more volume
            "margin_change_percent": -2        # 2% margin reduction
        }
        """
        # Capture current state as baseline
        base_data = ScenarioService._capture_baseline(db, client_id)
        
        # Calculate impact
        impact = ScenarioService._calculate_impact(base_data, changes)
        
        scenario = Scenario(
            client_id=client_id,
            name=name,
            description=description,
            base_data=base_data,
            changes=changes,
            impact_summary=impact
        )
        
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        
        return scenario
    
    @staticmethod
    def _capture_baseline(db: Session, client_id: int) -> Dict:
        """Capture current financial state as baseline"""
        client = db.query(Client).filter(Client.id == client_id).first()
        
        # Get recent orders (last 30 days for example)
        from datetime import timedelta
        recent_orders = db.query(Order).filter(
            Order.client_id == client_id,
            Order.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        total_revenue = sum(o.total_selling_price for o in recent_orders)
        total_cost = sum(o.total_cost for o in recent_orders)
        total_margin = total_revenue - total_cost
        avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
        
        total_wc_blocked = sum(o.working_capital_blocked for o in recent_orders)
        avg_credit_days = sum(o.credit_days for o in recent_orders) / len(recent_orders) if recent_orders else 30
        
        # Get average product costs
        products = db.query(Product).filter(Product.client_id == client_id).all()
        avg_rm_cost = sum(p.raw_material_cost for p in products) / len(products) if products else 0
        avg_labour_cost = sum(p.labour_cost_per_unit for p in products) / len(products) if products else 0
        
        return {
            "snapshot_date": datetime.utcnow().isoformat(),
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_margin": round(total_margin, 2),
            "margin_percentage": round(avg_margin_pct, 2),
            "working_capital_blocked": round(total_wc_blocked, 2),
            "average_credit_days": round(avg_credit_days, 1),
            "average_rm_cost": round(avg_rm_cost, 2),
            "average_labour_cost": round(avg_labour_cost, 2),
            "order_count": len(recent_orders)
        }
    
    @staticmethod
    def _calculate_impact(base_data: Dict, changes: Dict) -> Dict:
        """Calculate financial impact of proposed changes"""
        impact = {
            "revenue_change": 0,
            "revenue_change_percent": 0,
            "cost_change": 0,
            "cost_change_percent": 0,
            "margin_change": 0,
            "margin_change_percent": 0,
            "wc_change": 0,
            "wc_change_percent": 0,
            "cash_flow_impact": "",
            "profitability_impact": "",
            "recommendation": ""
        }
        
        new_revenue = base_data["total_revenue"]
        new_cost = base_data["total_cost"]
        new_wc = base_data["working_capital_blocked"]
        
        # Apply raw material cost change
        if "raw_material_cost_change" in changes:
            rm_change = changes["raw_material_cost_change"]
            # Assume RM is 60% of total cost
            cost_impact = rm_change * (base_data["total_cost"] * 0.6 / base_data["average_rm_cost"]) if base_data["average_rm_cost"] > 0 else 0
            new_cost += cost_impact
            
            impact["cost_change"] += cost_impact
        
        # Apply credit days change
        if "credit_days_change" in changes:
            days_change = changes["credit_days_change"]
            new_credit_days = base_data["average_credit_days"] + days_change
            
            # Recalculate WC blocked
            new_wc = new_cost * (new_credit_days / 365)
            wc_change = new_wc - base_data["working_capital_blocked"]
            
            impact["wc_change"] = wc_change
            impact["wc_change_percent"] = (wc_change / base_data["working_capital_blocked"] * 100) if base_data["working_capital_blocked"] > 0 else 0
        
        # Apply volume change
        if "volume_change_percent" in changes:
            volume_pct = changes["volume_change_percent"]
            new_revenue = new_revenue * (1 + volume_pct / 100)
            new_cost = new_cost * (1 + volume_pct / 100)
            new_wc = new_wc * (1 + volume_pct / 100)
        
        # Apply margin change (price adjustment)
        if "margin_change_percent" in changes:
            margin_change = changes["margin_change_percent"]
            # Adjust revenue to achieve new margin
            current_margin_pct = ((new_revenue - new_cost) / new_revenue * 100) if new_revenue > 0 else 0
            target_margin_pct = current_margin_pct + margin_change
            
            if target_margin_pct > 0:
                new_revenue = new_cost / (1 - target_margin_pct / 100)
        
        # Calculate changes
        impact["revenue_change"] = round(new_revenue - base_data["total_revenue"], 2)
        impact["revenue_change_percent"] = round(impact["revenue_change"] / base_data["total_revenue"] * 100, 2) if base_data["total_revenue"] > 0 else 0
        
        impact["cost_change"] = round(new_cost - base_data["total_cost"], 2)
        impact["cost_change_percent"] = round(impact["cost_change"] / base_data["total_cost"] * 100, 2) if base_data["total_cost"] > 0 else 0
        
        new_margin = new_revenue - new_cost
        impact["margin_change"] = round(new_margin - base_data["total_margin"], 2)
        impact["margin_change_percent"] = round(impact["margin_change"] / base_data["total_margin"] * 100, 2) if base_data["total_margin"] > 0 else 0
        
        # Generate insights
        impact["cash_flow_impact"] = ScenarioService._generate_cash_flow_insight(impact, changes)
        impact["profitability_impact"] = ScenarioService._generate_profitability_insight(impact, changes)
        impact["recommendation"] = ScenarioService._generate_recommendation(impact, changes)
        
        return impact
    
    @staticmethod
    def _generate_cash_flow_insight(impact: Dict, changes: Dict) -> str:
        """Generate plain-language cash flow insight"""
        wc_change = impact["wc_change"]
        
        if abs(wc_change) < 1000:
            return "Minimal impact on working capital and cash flow."
        
        if wc_change > 0:
            return f"Working capital will increase by ₹{abs(wc_change):,.0f}. This means ₹{abs(wc_change):,.0f} more cash will be tied up in operations. Ensure adequate cash reserves or credit line."
        else:
            return f"Working capital will decrease by ₹{abs(wc_change):,.0f}. This frees up ₹{abs(wc_change):,.0f} cash that can be used elsewhere or kept as buffer."
    
    @staticmethod
    def _generate_profitability_insight(impact: Dict, changes: Dict) -> str:
        """Generate plain-language profitability insight"""
        margin_change = impact["margin_change"]
        margin_pct = impact["margin_change_percent"]
        
        if abs(margin_change) < 1000:
            return "Negligible impact on profitability."
        
        if margin_change > 0:
            return f"Profit will improve by ₹{margin_change:,.0f} ({margin_pct:+.1f}%). This change enhances business profitability."
        else:
            return f"Profit will reduce by ₹{abs(margin_change):,.0f} ({margin_pct:.1f}%). Consider if the trade-off is worth other benefits."
    
    @staticmethod
    def _generate_recommendation(impact: Dict, changes: Dict) -> str:
        """Generate actionable recommendation"""
        recommendations = []
        
        # Check if this is a good trade-off
        if impact["margin_change"] > 0 and impact["wc_change"] < 0:
            recommendations.append("✓ RECOMMENDED: This change improves both profitability and cash flow.")
        elif impact["margin_change"] > 0 and impact["wc_change"] > 0:
            recommendations.append("⚠ CONSIDER: Profitability improves but requires more working capital. Ensure cash availability.")
        elif impact["margin_change"] < 0 and impact["wc_change"] < 0:
            recommendations.append("⚠ TRADE-OFF: Lower profit but better cash flow. Acceptable if cash is tight.")
        else:
            recommendations.append("✗ NOT RECOMMENDED: Both profitability and cash flow worsen.")
        
        # Specific advice based on changes
        if "raw_material_cost_change" in changes:
            rm_change = changes["raw_material_cost_change"]
            if rm_change < 0:
                recommendations.append(f"Negotiate with suppliers or find alternatives to reduce RM cost by ₹{abs(rm_change)}.")
            else:
                recommendations.append(f"If RM cost increases by ₹{rm_change}, consider passing cost to customers via price increase.")
        
        if "credit_days_change" in changes:
            days_change = changes["credit_days_change"]
            if days_change > 0:
                recommendations.append(f"Extending credit by {days_change} days may help win orders but ties up more cash. Offer early-payment discounts to encourage faster payment.")
            else:
                recommendations.append(f"Reducing credit by {abs(days_change)} days improves cash flow. Communicate this change carefully to maintain customer relationships.")
        
        return " ".join(recommendations)
    
    @staticmethod
    def compare_scenarios(db: Session, scenario_ids: List[int]) -> Dict:
        """Compare multiple scenarios side by side"""
        scenarios = db.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        
        if not scenarios:
            return {"error": "No scenarios found"}
        
        comparison = {
            "scenarios": [],
            "best_for_profit": None,
            "best_for_cash": None,
            "balanced_choice": None
        }
        
        for scenario in scenarios:
            comparison["scenarios"].append({
                "id": scenario.id,
                "name": scenario.name,
                "margin_change": scenario.impact_summary.get("margin_change", 0),
                "wc_change": scenario.impact_summary.get("wc_change", 0),
                "revenue_change": scenario.impact_summary.get("revenue_change", 0),
                "recommendation": scenario.impact_summary.get("recommendation", "")
            })
        
        # Determine best scenarios
        sorted_by_margin = sorted(comparison["scenarios"], key=lambda x: x["margin_change"], reverse=True)
        sorted_by_wc = sorted(comparison["scenarios"], key=lambda x: x["wc_change"])  # Lower WC is better
        
        comparison["best_for_profit"] = sorted_by_margin[0]["name"]
        comparison["best_for_cash"] = sorted_by_wc[0]["name"]
        
        # Balanced = best profit with acceptable WC impact
        for s in sorted_by_margin:
            if s["wc_change"] <= 0 or (s["margin_change"] > 0 and s["wc_change"] < s["margin_change"] * 0.5):
                comparison["balanced_choice"] = s["name"]
                break
        
        return comparison
