from typing import Dict, List
import pandas as pd

class CostingEngine:
    
    # Industry-specific rules
    INDUSTRY_RULES = {
        "manufacturing": {
            "min_margin_pct": 20,
            "max_safe_credit_days": 45,
            "max_debtor_days": 60,
            "warning_debtor_days": 50
        },
        "trading": {
            "min_margin_pct": 15,
            "max_safe_credit_days": 30,
            "max_debtor_days": 45,
            "warning_debtor_days": 40
        },
        "services": {
            "min_margin_pct": 30,
            "max_safe_credit_days": 30,
            "max_debtor_days": 45,
            "warning_debtor_days": 40
        }
    }
    
    def __init__(self, client_data: Dict):
        self.client_data = client_data
        self.industry = client_data.get("industry", "manufacturing").lower()
        self.rules = self.INDUSTRY_RULES.get(
            self.industry, 
            self.INDUSTRY_RULES["manufacturing"]
        )
    
    def calculate_contribution_margin(
        self, 
        selling_price: float, 
        cost_price: float
    ) -> Dict:
        contribution = selling_price - cost_price
        margin_pct = (contribution / selling_price * 100) if selling_price > 0 else 0
        
        return {
            "contribution_per_unit": round(contribution, 2),
            "margin_percentage": round(margin_pct, 2)
        }
    
    def estimate_working_capital_impact(
        self,
        order_value: float,
        credit_days: int,
        current_debtors: float = 0,
        annual_sales: float = 0
    ) -> Dict:
        additional_receivables = order_value
        
        daily_sales = annual_sales / 365 if annual_sales > 0 else order_value / 30
        
        current_debtor_days = (current_debtors / daily_sales) if daily_sales > 0 else 0
        new_debtors = current_debtors + order_value
        new_debtor_days = (new_debtors / daily_sales) if daily_sales > 0 else credit_days
        
        return {
            "additional_receivables": round(additional_receivables, 2),
            "current_debtor_days": round(current_debtor_days, 0),
            "new_debtor_days": round(new_debtor_days, 0),
            "wc_increase": round(additional_receivables, 2)
        }
    
    def evaluate_order_decision(
        self,
        product_name: str,
        selling_price: float,
        cost_price: float,
        quantity: float,
        customer_name: str,
        proposed_credit_days: int,
        current_debtors: float = 0,
        annual_sales: float = 0
    ) -> Dict:
        
        # Calculate metrics
        margin = self.calculate_contribution_margin(selling_price, cost_price)
        order_value = selling_price * quantity
        
        wc_impact = self.estimate_working_capital_impact(
            order_value,
            proposed_credit_days,
            current_debtors,
            annual_sales
        )
        
        # Decision rules
        decision = "safe"
        reasons = []
        
        # Rule 1: Minimum margin threshold
        min_margin = self.rules["min_margin_pct"]
        if margin['margin_percentage'] < min_margin:
            decision = "risky"
            reasons.append(
                f"Margin {margin['margin_percentage']:.1f}% is below "
                f"minimum {min_margin}% for {self.industry}"
            )
        
        # Rule 2: Credit days vs margin
        max_credit = self.rules["max_safe_credit_days"]
        if proposed_credit_days > max_credit and margin['margin_percentage'] < 25:
            if decision != "risky":
                decision = "caution"
            reasons.append(
                f"Credit days {proposed_credit_days} exceed safe limit of {max_credit} days "
                f"for margin {margin['margin_percentage']:.1f}%"
            )
        
        # Rule 3: Working capital strain
        max_debtor_days = self.rules["max_debtor_days"]
        if wc_impact['new_debtor_days'] > max_debtor_days:
            if decision != "risky":
                decision = "caution"
            reasons.append(
                f"Total debtor days will reach {wc_impact['new_debtor_days']:.0f}, "
                f"exceeding safe limit of {max_debtor_days}"
            )
        
        # If no issues, add positive reasons
        if not reasons:
            reasons.append(f"Healthy margin of {margin['margin_percentage']:.1f}%")
            reasons.append(f"Credit days {proposed_credit_days} are manageable")
        
        recommendation = self._generate_recommendation(
            decision, margin, proposed_credit_days, order_value
        )
        
        return {
            "decision": decision,
            "margin": margin,
            "order_value": round(order_value, 2),
            "working_capital": wc_impact,
            "reasons": reasons,
            "recommendation": recommendation
        }
    
    def _generate_recommendation(
        self, 
        decision: str, 
        margin: Dict,
        credit_days: int,
        order_value: float
    ) -> str:
        if decision == "safe":
            return (
                f"✅ Safe to accept this ₹{order_value:,.0f} order. "
                f"Your {margin['margin_percentage']:.1f}% margin "
                f"supports {credit_days} days credit comfortably."
            )
        elif decision == "caution":
            return (
                f"⚠️ Proceed with caution. Consider either: "
                f"(1) Increase price by 5-10% OR "
                f"(2) Reduce credit days to {self.rules['max_safe_credit_days']} days."
            )
        else:
            return (
                f"❌ Not recommended at current terms. "
                f"Increase price to achieve at least {self.rules['min_margin_pct']}% margin, "
                f"or request 30-50% advance payment."
            )
    
    def compare_scenarios(
        self,
        base_scenario: Dict,
        alternative_scenarios: List[Dict]
    ) -> Dict:
        """
        Compare multiple pricing/credit scenarios side by side
        """
        results = []
        
        # Evaluate base scenario
        base_result = self.evaluate_order_decision(**base_scenario)
        base_result['scenario_name'] = "Current Proposal"
        results.append(base_result)
        
        # Evaluate alternatives
        for idx, scenario in enumerate(alternative_scenarios):
            alt_result = self.evaluate_order_decision(**scenario)
            alt_result['scenario_name'] = scenario.get('name', f"Option {idx+1}")
            results.append(alt_result)
        
        # Find best scenario
        safe_scenarios = [r for r in results if r['decision'] == 'safe']
        best_scenario = max(
            safe_scenarios if safe_scenarios else results,
            key=lambda x: x['margin']['margin_percentage']
        )
        
        return {
            "scenarios": results,
            "best_scenario": best_scenario['scenario_name'],
            "comparison_summary": self._generate_comparison_summary(results)
        }
    
    def _generate_comparison_summary(self, results: List[Dict]) -> str:
        safe_count = len([r for r in results if r['decision'] == 'safe'])
        
        if safe_count == 0:
            return "None of the scenarios are recommended. Consider higher pricing or shorter credit terms."
        elif safe_count == len(results):
            best = max(results, key=lambda x: x['margin']['margin_percentage'])
            return f"All scenarios are acceptable. {best['scenario_name']} offers the best margin at {best['margin']['margin_percentage']:.1f}%."
        else:
            safe_scenarios = [r for r in results if r['decision'] == 'safe']
            best = max(safe_scenarios, key=lambda x: x['margin']['margin_percentage'])
            return f"{safe_count} out of {len(results)} scenarios are safe. Recommend: {best['scenario_name']}."
