# backend/tests/test_roundtrip_excel.py

"""
Property-based tests for Excel round-trip consistency.

These tests validate that data can be exported to Excel and parsed back
without loss of information or data corruption.

Requirements: 28.4, 28.5
"""

import pytest
import tempfile
import os
from decimal import Decimal
from datetime import datetime, date

from app.utils.excel_generator import generate_excel
from app.utils.excel_parser import parse_excel, validate_excel_data


class TestExcelRoundTrip:
    """Tests for Excel export/import round-trip consistency"""
    
    def test_simple_financial_data_roundtrip(self):
        """Test round-trip with simple financial data"""
        # Create test data matching financial_statement template
        data = {
            'statements': [
                {
                    'statement_type': 'Income Statement',
                    'period_start': '2024-01-01T00:00:00',
                    'period_end': '2024-12-31T00:00:00',
                    'metrics': {
                        'gross_margin': 25.0,
                        'net_margin': 15.0,
                        'roa': 10.0,
                        'roe': 12.0
                    }
                },
                {
                    'statement_type': 'Balance Sheet',
                    'period_start': '2024-01-01T00:00:00',
                    'period_end': '2024-12-31T00:00:00',
                    'metrics': {
                        'gross_margin': 30.0,
                        'net_margin': 18.0,
                        'roa': 11.0,
                        'roe': 13.0
                    }
                }
            ]
        }
        
        # Export to Excel
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('financial_statement', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            # Parse back
            parsed_data = parse_excel(tmp_path)
            
            # Validate structure
            assert 'worksheets' in parsed_data
            assert 'Financial Statements' in parsed_data['worksheets']
            
            worksheet = parsed_data['worksheets']['Financial Statements']
            assert worksheet['row_count'] == 2
            assert 'Type' in worksheet['headers']
            assert 'Gross Margin %' in worksheet['headers']
            
            # Validate data
            rows = worksheet['rows']
            assert len(rows) == 2
            
            # Check first row
            assert rows[0]['Type'] == 'Income Statement'
            assert abs(rows[0]['Gross Margin %'] - 25.0) < 0.01
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_multiple_worksheets_roundtrip(self):
        """Test round-trip with receivables report (has multiple worksheets)"""
        data = {
            'aging_summary': {
                'Current': {'count': 5, 'total_amount': 10000.00},
                '1-30 days': {'count': 3, 'total_amount': 5000.00},
                '31-60 days': {'count': 2, 'total_amount': 3000.00}
            },
            'receivables': [
                {
                    'party_name': 'Customer A',
                    'amount': 5000.00,
                    'transaction_date': '2024-01-15T00:00:00',
                    'due_date': '2024-02-15T00:00:00',
                    'days_outstanding': 10,
                    'is_overdue': False
                },
                {
                    'party_name': 'Customer B',
                    'amount': 3000.00,
                    'transaction_date': '2024-01-10T00:00:00',
                    'due_date': '2024-02-10T00:00:00',
                    'days_outstanding': 15,
                    'is_overdue': False
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('receivables_report', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            parsed_data = parse_excel(tmp_path)
            
            # Validate both worksheets exist
            assert 'Summary' in parsed_data['worksheets']
            assert 'Details' in parsed_data['worksheets']
            
            # Validate Summary sheet
            summary = parsed_data['worksheets']['Summary']
            assert summary['row_count'] == 3
            assert 'Aging Bucket' in summary['headers']
            
            # Validate Details sheet
            details = parsed_data['worksheets']['Details']
            assert details['row_count'] == 2
            assert details['rows'][0]['Party Name'] == 'Customer A'
            assert abs(details['rows'][0]['Amount'] - 5000.00) < 0.01
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_numeric_precision_roundtrip(self):
        """Test that numeric precision is preserved"""
        data = {
            'products': [
                {
                    'name': 'Product A',
                    'category': 'Category 1',
                    'costing': {
                        'raw_material_cost': 123.456789,
                        'labour_cost_per_unit': 12.345,
                        'overhead_percentage': 0.12345,
                        'target_margin_percentage': 25.0
                    },
                    'statistics': {
                        'avg_margin': 24.5
                    }
                },
                {
                    'name': 'Product B',
                    'category': 'Category 2',
                    'costing': {
                        'raw_material_cost': 0.000001,
                        'labour_cost_per_unit': 1.0,
                        'overhead_percentage': 0.99999,
                        'target_margin_percentage': 30.0
                    },
                    'statistics': {
                        'avg_margin': 29.8
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('costing_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            parsed_data = parse_excel(tmp_path)
            
            rows = parsed_data['worksheets']['Costing Analysis']['rows']
            
            # Check precision (allow small floating point errors)
            assert abs(rows[0]['Raw Material'] - 123.456789) < 0.01
            assert abs(rows[0]['Labour'] - 12.345) < 0.01
            assert abs(rows[0]['Overhead %'] - 0.12345) < 0.001
            
            assert abs(rows[1]['Raw Material'] - 0.000001) < 0.000001
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_special_characters_roundtrip(self):
        """Test that special characters are preserved"""
        data = {
            'groups': [
                {'name': 'Hello, World!', 'total_revenue': 100, 'total_cost': 50, 'margin': 50, 'margin_percentage': 50.0, 'order_count': 1},
                {'name': 'Quote: "test"', 'total_revenue': 200, 'total_cost': 100, 'margin': 100, 'margin_percentage': 50.0, 'order_count': 2},
                {'name': "Apostrophe: it's", 'total_revenue': 300, 'total_cost': 150, 'margin': 150, 'margin_percentage': 50.0, 'order_count': 3},
                {'name': 'Unicode: café', 'total_revenue': 400, 'total_cost': 200, 'margin': 200, 'margin_percentage': 50.0, 'order_count': 4},
                {'name': 'Symbols: @#$%', 'total_revenue': 500, 'total_cost': 250, 'margin': 250, 'margin_percentage': 50.0, 'order_count': 5}
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('margin_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            parsed_data = parse_excel(tmp_path)
            
            rows = parsed_data['worksheets']['Margin Analysis']['rows']
            
            assert rows[0]['Name'] == 'Hello, World!'
            assert rows[1]['Name'] == 'Quote: "test"'
            assert rows[2]['Name'] == "Apostrophe: it's"
            assert rows[3]['Name'] == 'Unicode: café'
            assert rows[4]['Name'] == 'Symbols: @#$%'
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_empty_cells_roundtrip(self):
        """Test that empty cells are handled correctly"""
        data = {
            'orders': [
                {
                    'order_number': 'ORD-001',
                    'customer_name': None,
                    'order_date': '2024-01-15T00:00:00',
                    'financials': {'total_selling_price': 1000, 'total_cost': 600, 'margin_percentage': 40.0},
                    'evaluation': {'profitability_score': 85, 'risk_level': 'Low', 'should_accept': True}
                },
                {
                    'order_number': None,
                    'customer_name': 'Customer B',
                    'order_date': '2024-01-16T00:00:00',
                    'financials': {'total_selling_price': 2000, 'total_cost': 1200, 'margin_percentage': 40.0},
                    'evaluation': {'profitability_score': 90, 'risk_level': 'Low', 'should_accept': True}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('order_evaluation', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            parsed_data = parse_excel(tmp_path)
            
            rows = parsed_data['worksheets']['Order Evaluations']['rows']
            
            # Check that None values are preserved
            assert rows[0]['Order #'] == 'ORD-001'
            assert rows[0]['Customer'] is None or rows[0]['Customer'] == ''
            
            assert rows[1]['Order #'] is None or rows[1]['Order #'] == ''
            assert rows[1]['Customer'] == 'Customer B'
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_large_dataset_roundtrip(self):
        """Test round-trip with a large dataset"""
        # Generate 1000 rows of data
        products = []
        for i in range(1000):
            products.append({
                'name': f'Product {i}',
                'category': f'Category {i % 10}',
                'costing': {
                    'raw_material_cost': i * 100.50,
                    'labour_cost_per_unit': i * 10.0,
                    'overhead_percentage': i / 1000.0,
                    'target_margin_percentage': 25.0
                },
                'statistics': {
                    'avg_margin': 24.5
                }
            })
        
        data = {'products': products}
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('costing_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            parsed_data = parse_excel(tmp_path)
            
            rows = parsed_data['worksheets']['Costing Analysis']['rows']
            
            # Verify row count
            assert len(rows) == 1000
            
            # Spot check some rows
            assert rows[0]['Product'] == 'Product 0'
            assert rows[0]['Category'] == 'Category 0'
            
            assert rows[500]['Product'] == 'Product 500'
            assert rows[500]['Category'] == 'Category 0'
            assert abs(rows[500]['Raw Material'] - 50250.0) < 0.01
            
            assert rows[999]['Product'] == 'Product 999'
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_validation_with_expected_structure(self):
        """Test validation against expected structure"""
        data = {
            'groups': [
                {'name': 'Group A', 'total_revenue': 1000, 'total_cost': 600, 'margin': 400, 'margin_percentage': 40.0, 'order_count': 5}
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            excel_bytes = generate_excel('margin_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(excel_bytes)
            
            parsed_data = parse_excel(tmp_path)
            
            # Define expected structure
            expected_structure = {
                'worksheets': {
                    'Margin Analysis': {
                        'headers': ['Name', 'Revenue', 'Cost', 'Margin', 'Margin %', 'Order Count']
                    }
                }
            }
            
            # Should pass validation
            assert validate_excel_data(parsed_data, expected_structure) is True
            
            # Should fail with wrong expected structure
            wrong_structure = {
                'worksheets': {
                    'Margin Analysis': {
                        'headers': ['WrongColumn1', 'WrongColumn2']
                    }
                }
            }
            
            with pytest.raises(ValueError, match="Header mismatch"):
                validate_excel_data(parsed_data, wrong_structure)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
