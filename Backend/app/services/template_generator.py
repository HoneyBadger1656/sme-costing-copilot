# Backend/app/services/template_generator.py
# Generate Excel templates for financial data upload

import pandas as pd
from io import BytesIO
from typing import Dict, Any

class TemplateGenerator:
    
    @staticmethod
    def generate_balance_sheet_template() -> bytes:
        """Generate Excel template for balance sheet upload"""
        
        # Sample data structure
        sample_data = [
            {"item_name": "Cash and Bank", "category": "current_assets", "amount": 100000, "notes": "Cash in hand and bank balances"},
            {"item_name": "Accounts Receivable", "category": "current_assets", "amount": 250000, "notes": "Money owed by customers"},
            {"item_name": "Inventory", "category": "current_assets", "amount": 150000, "notes": "Stock of goods"},
            {"item_name": "Fixed Assets", "category": "fixed_assets", "amount": 500000, "notes": "Plant, machinery, equipment"},
            {"item_name": "Accounts Payable", "category": "current_liabilities", "amount": 80000, "notes": "Money owed to suppliers"},
            {"item_name": "Short-term Loans", "category": "current_liabilities", "amount": 50000, "notes": "Loans due within 1 year"},
            {"item_name": "Long-term Debt", "category": "long_term_liabilities", "amount": 200000, "notes": "Loans due after 1 year"},
            {"item_name": "Share Capital", "category": "equity", "amount": 300000, "notes": "Paid-up share capital"},
            {"item_name": "Retained Earnings", "category": "equity", "amount": 370000, "notes": "Accumulated profits"}
        ]
        
        df = pd.DataFrame(sample_data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Balance Sheet', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame([
                {"Instructions": "1. Fill in your company's balance sheet items"},
                {"Instructions": "2. Use the provided categories or similar ones"},
                {"Instructions": "3. Ensure amounts are in the same currency"},
                {"Instructions": "4. Categories: current_assets, fixed_assets, current_liabilities, long_term_liabilities, equity"},
                {"Instructions": "5. Save and upload the file"}
            ])
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def generate_profit_loss_template() -> bytes:
        """Generate Excel template for P&L statement upload"""
        
        sample_data = [
            {"item_name": "Sales Revenue", "category": "revenue", "amount": 1000000, "notes": "Total sales for the period"},
            {"item_name": "Service Income", "category": "revenue", "amount": 200000, "notes": "Income from services"},
            {"item_name": "Cost of Goods Sold", "category": "cost_of_goods_sold", "amount": 600000, "notes": "Direct cost of products sold"},
            {"item_name": "Salaries & Wages", "category": "operating_expenses", "amount": 150000, "notes": "Employee compensation"},
            {"item_name": "Rent", "category": "operating_expenses", "amount": 60000, "notes": "Office/factory rent"},
            {"item_name": "Utilities", "category": "operating_expenses", "amount": 25000, "notes": "Electricity, water, etc."},
            {"item_name": "Marketing", "category": "operating_expenses", "amount": 40000, "notes": "Advertising and promotion"},
            {"item_name": "Interest Expense", "category": "interest", "amount": 15000, "notes": "Interest on loans"},
            {"item_name": "Tax Expense", "category": "tax", "amount": 45000, "notes": "Income tax paid"}
        ]
        
        df = pd.DataFrame(sample_data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Profit & Loss', index=False)
            
            instructions = pd.DataFrame([
                {"Instructions": "1. Fill in your company's income and expense items"},
                {"Instructions": "2. Categories: revenue, cost_of_goods_sold, operating_expenses, interest, tax"},
                {"Instructions": "3. Use positive amounts for all items"},
                {"Instructions": "4. Ensure the period matches your reporting period"},
                {"Instructions": "5. Save and upload the file"}
            ])
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def generate_inventory_template() -> bytes:
        """Generate Excel template for inventory upload"""
        
        sample_data = [
            {"item_name": "Product A", "category": "finished_goods", "quantity": 100, "unit": "pcs", "unit_cost": 500, "total_value": 50000},
            {"item_name": "Raw Material X", "category": "raw_materials", "quantity": 500, "unit": "kg", "unit_cost": 50, "total_value": 25000},
            {"item_name": "Component Y", "category": "components", "quantity": 200, "unit": "pcs", "unit_cost": 75, "total_value": 15000},
            {"item_name": "Packaging Material", "category": "consumables", "quantity": 1000, "unit": "pcs", "unit_cost": 5, "total_value": 5000}
        ]
        
        df = pd.DataFrame(sample_data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            instructions = pd.DataFrame([
                {"Instructions": "1. List all inventory items with current quantities"},
                {"Instructions": "2. Categories: finished_goods, raw_materials, components, consumables"},
                {"Instructions": "3. Ensure unit costs are accurate"},
                {"Instructions": "4. Total value should equal quantity × unit_cost"},
                {"Instructions": "5. Use consistent units (pcs, kg, litre, etc.)"}
            ])
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        output.seek(0)
        return output.getvalue()