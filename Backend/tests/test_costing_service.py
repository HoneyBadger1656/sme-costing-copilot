"""Tests for costing service"""

import pytest
from app.services.costing_service import CostingService


class TestCostingService:
    """Test costing calculations"""
    
    def test_calculate_product_cost_basic(self):
        """Test basic product cost calculation"""
        service = CostingService()
        
        product_data = {
            "raw_material_cost": 100.0,
            "labour_cost_per_unit": 20.0,
            "overhead_percentage": 10.0
        }
        
        result = service.calculate_product_cost(product_data)
        
        # Direct cost = 100 + 20 = 120
        # Overhead = 120 * 0.10 = 12
        # Total cost = 120 + 12 = 132
        assert result["direct_cost"] == 120.0
        assert result["overhead_cost"] == 12.0
        assert result["total_cost"] == 132.0
    
    def test_calculate_selling_price(self):
        """Test selling price calculation with margin and tax"""
        service = CostingService()
        
        cost = 132.0
        margin_percentage = 20.0
        tax_rate = 18.0
        
        result = service.calculate_selling_price(cost, margin_percentage, tax_rate)
        
        # Price before tax = 132 / (1 - 0.20) = 165
        # Tax = 165 * 0.18 = 29.7
        # Final price = 165 + 29.7 = 194.7
        assert result["price_before_tax"] == 165.0
        assert result["tax_amount"] == 29.7
        assert result["final_price"] == 194.7
        assert result["margin_amount"] == 33.0
    
    def test_calculate_order_totals(self, test_product):
        """Test order totals calculation"""
        service = CostingService()
        
        order_items = [
            {"product": test_product, "quantity": 10},
            {"product": test_product, "quantity": 5}
        ]
        
        result = service.calculate_order_totals(order_items)
        
        assert result["total_quantity"] == 15
        assert result["total_cost"] > 0
        assert result["total_selling_price"] > result["total_cost"]
        assert result["gross_margin"] > 0
    
    def test_calculate_working_capital_impact(self):
        """Test working capital impact calculation"""
        service = CostingService()
        
        order_value = 100000.0
        credit_days = 45
        
        result = service.calculate_working_capital_impact(order_value, credit_days)
        
        assert result["blocked_capital"] == order_value
        assert result["credit_days"] == credit_days
        assert round(result["daily_cost"], 2) == round(order_value / 365, 2)
        assert result["interest_cost"] > 0
    
    def test_zero_overhead(self):
        """Test calculation with zero overhead"""
        service = CostingService()
        
        product_data = {
            "raw_material_cost": 100.0,
            "labour_cost_per_unit": 20.0,
            "overhead_percentage": 0.0
        }
        
        result = service.calculate_product_cost(product_data)
        
        assert result["direct_cost"] == 120.0
        assert result["overhead_cost"] == 0.0
        assert result["total_cost"] == 120.0
    
    def test_negative_values_validation(self):
        """Test that negative values are handled properly"""
        service = CostingService()
        
        with pytest.raises(ValueError):
            service.calculate_product_cost({
                "raw_material_cost": -100.0,
                "labour_cost_per_unit": 20.0,
                "overhead_percentage": 10.0
            })
