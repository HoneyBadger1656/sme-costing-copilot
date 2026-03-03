"""Tests for financial service"""

import pytest
from datetime import datetime
from app.services.financial_service import FinancialService


class TestFinancialService:
    """Test financial calculations and ratios"""
    
    def test_calculate_current_ratio(self):
        """Test current ratio calculation"""
        service = FinancialService()
        
        current_assets = 500000.0
        current_liabilities = 300000.0
        
        ratio = service.calculate_current_ratio(current_assets, current_liabilities)
        
        # Current ratio = 500000 / 300000 = 1.67
        assert round(ratio, 2) == 1.67
    
    def test_calculate_quick_ratio(self):
        """Test quick ratio calculation"""
        service = FinancialService()
        
        current_assets = 500000.0
        inventory = 100000.0
        current_liabilities = 300000.0
        
        ratio = service.calculate_quick_ratio(current_assets, inventory, current_liabilities)
        
        # Quick ratio = (500000 - 100000) / 300000 = 1.33
        assert round(ratio, 2) == 1.33
    
    def test_calculate_debt_equity_ratio(self):
        """Test debt to equity ratio calculation"""
        service = FinancialService()
        
        total_debt = 400000.0
        total_equity = 600000.0
        
        ratio = service.calculate_debt_equity_ratio(total_debt, total_equity)
        
        # Debt/Equity = 400000 / 600000 = 0.67
        assert round(ratio, 2) == 0.67
    
    def test_calculate_gross_margin(self):
        """Test gross margin calculation"""
        service = FinancialService()
        
        revenue = 1000000.0
        cogs = 600000.0
        
        margin = service.calculate_gross_margin(revenue, cogs)
        
        # Gross margin = (1000000 - 600000) / 1000000 = 0.40 (40%)
        assert margin == 40.0
    
    def test_calculate_net_margin(self):
        """Test net margin calculation"""
        service = FinancialService()
        
        revenue = 1000000.0
        net_income = 150000.0
        
        margin = service.calculate_net_margin(revenue, net_income)
        
        # Net margin = 150000 / 1000000 = 0.15 (15%)
        assert margin == 15.0
    
    def test_calculate_roa(self):
        """Test return on assets calculation"""
        service = FinancialService()
        
        net_income = 150000.0
        total_assets = 1000000.0
        
        roa = service.calculate_roa(net_income, total_assets)
        
        # ROA = 150000 / 1000000 = 0.15 (15%)
        assert roa == 15.0
    
    def test_calculate_roe(self):
        """Test return on equity calculation"""
        service = FinancialService()
        
        net_income = 150000.0
        total_equity = 600000.0
        
        roe = service.calculate_roe(net_income, total_equity)
        
        # ROE = 150000 / 600000 = 0.25 (25%)
        assert roe == 25.0
    
    def test_zero_denominator_handling(self):
        """Test handling of zero denominators"""
        service = FinancialService()
        
        # Should return 0 or raise appropriate error
        with pytest.raises(ValueError):
            service.calculate_current_ratio(500000.0, 0.0)
    
    def test_negative_values_handling(self):
        """Test handling of negative values"""
        service = FinancialService()
        
        # Negative equity should be handled
        ratio = service.calculate_debt_equity_ratio(400000.0, -100000.0)
        assert ratio < 0  # Negative ratio indicates negative equity
    
    def test_calculate_working_capital(self):
        """Test working capital calculation"""
        service = FinancialService()
        
        current_assets = 500000.0
        current_liabilities = 300000.0
        
        wc = service.calculate_working_capital(current_assets, current_liabilities)
        
        # Working capital = 500000 - 300000 = 200000
        assert wc == 200000.0
    
    def test_calculate_cash_conversion_cycle(self):
        """Test cash conversion cycle calculation"""
        service = FinancialService()
        
        days_inventory_outstanding = 45
        days_sales_outstanding = 60
        days_payables_outstanding = 30
        
        ccc = service.calculate_cash_conversion_cycle(
            days_inventory_outstanding,
            days_sales_outstanding,
            days_payables_outstanding
        )
        
        # CCC = 45 + 60 - 30 = 75 days
        assert ccc == 75
