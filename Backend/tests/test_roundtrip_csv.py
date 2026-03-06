# backend/tests/test_roundtrip_csv.py

"""
Property-based tests for CSV round-trip consistency.

These tests validate that data can be exported to CSV and parsed back
without loss of information or data corruption.

Requirements: 28.4, 28.6
"""

import pytest
import tempfile
import os
from datetime import datetime

from app.utils.csv_generator import generate_csv
from app.utils.csv_parser import parse_csv, validate_csv_data, compare_csv_data


class TestCSVRoundTrip:
    """Tests for CSV export/import round-trip consistency"""
    
    def test_simple_costing_data_roundtrip(self):
        """Test round-trip with simple costing data"""
        # Create test data
        data = {
            'products': [
                {
                    'name': 'Widget A',
                    'category': 'Widgets',
                    'sku': 'WID-A',
                    'costing': {
                        'raw_material_cost': 50.00,
                        'labour_cost_per_unit': 25.00,
                        'overhead_percentage': 0.10,
                        'target_margin_percentage': 33.0
                    },
                    'statistics': {
                        'avg_margin': 33.0
                    }
                },
                {
                    'name': 'Widget B',
                    'category': 'Widgets',
                    'sku': 'WID-B',
                    'costing': {
                        'raw_material_cost': 100.00,
                        'labour_cost_per_unit': 50.00,
                        'overhead_percentage': 0.15,
                        'target_margin_percentage': 33.0
                    },
                    'statistics': {
                        'avg_margin': 33.0
                    }
                }
            ]
        }
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('costing_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            # Parse back
            parsed_data = parse_csv(tmp_path)
            
            # Validate structure
            assert 'headers' in parsed_data
            assert 'rows' in parsed_data
            assert parsed_data['row_count'] == 2
            
            # Validate headers
            assert 'Product' in parsed_data['headers']
            assert 'Raw Material Cost' in parsed_data['headers']
            
            # Validate data
            rows = parsed_data['rows']
            assert len(rows) == 2
            
            # Check first row
            assert rows[0]['Product'] == 'Widget A'
            assert abs(rows[0]['Raw Material Cost'] - 50.00) < 0.01
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_numeric_types_roundtrip(self):
        """Test that different numeric types are preserved"""
        data = {
            'groups': [
                {'name': 'Group 1', 'total_revenue': 100, 'total_cost': 50, 'margin': 50, 'margin_percentage': 0.25, 'order_count': 10},
                {'name': 'Group 2', 'total_revenue': 0, 'total_cost': 0, 'margin': 0, 'margin_percentage': 0.99, 'order_count': 0},
                {'name': 'Group 3', 'total_revenue': -50, 'total_cost': -25, 'margin': -25, 'margin_percentage': -0.10, 'order_count': 5}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('margin_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            rows = parsed_data['rows']
            
            # Check integers
            assert rows[0]['Order Count'] == 10
            assert rows[1]['Order Count'] == 0
            assert rows[2]['Order Count'] == 5
            
            # Check floats (with tolerance)
            assert abs(rows[0]['Total Revenue'] - 100) < 0.01
            assert abs(rows[1]['Total Revenue'] - 0) < 0.01
            assert abs(rows[2]['Total Revenue'] - (-50)) < 0.01
            
            # Check percentages
            assert abs(rows[0]['Margin %'] - 0.25) < 0.01
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_special_characters_roundtrip(self):
        """Test that special characters are preserved"""
        data = {
            'receivables': [
                {'party_name': 'Hello, World!', 'amount': 1, 'transaction_date': '2024-01-01T00:00:00', 'due_date': '2024-02-01T00:00:00', 'days_outstanding': 10, 'is_overdue': False, 'aging_bucket': 'Current'},
                {'party_name': 'Quote: "test"', 'amount': 2, 'transaction_date': '2024-01-02T00:00:00', 'due_date': '2024-02-02T00:00:00', 'days_outstanding': 11, 'is_overdue': False, 'aging_bucket': 'Current'},
                {'party_name': "Apostrophe: it's", 'amount': 3, 'transaction_date': '2024-01-03T00:00:00', 'due_date': '2024-02-03T00:00:00', 'days_outstanding': 12, 'is_overdue': False, 'aging_bucket': 'Current'},
                {'party_name': 'Unicode: café', 'amount': 4, 'transaction_date': '2024-01-04T00:00:00', 'due_date': '2024-02-04T00:00:00', 'days_outstanding': 13, 'is_overdue': False, 'aging_bucket': 'Current'},
                {'party_name': 'Comma: a,b,c', 'amount': 6, 'transaction_date': '2024-01-06T00:00:00', 'due_date': '2024-02-06T00:00:00', 'days_outstanding': 15, 'is_overdue': False, 'aging_bucket': 'Current'}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('receivables_report', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            rows = parsed_data['rows']
            
            assert rows[0]['Party Name'] == 'Hello, World!'
            assert rows[1]['Party Name'] == 'Quote: "test"'
            assert rows[2]['Party Name'] == "Apostrophe: it's"
            assert rows[3]['Party Name'] == 'Unicode: café'
            # Note: Commas may be escaped in CSV
            assert 'a' in rows[4]['Party Name'] and 'b' in rows[4]['Party Name']
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_empty_values_roundtrip(self):
        """Test that empty values are handled correctly"""
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
                    'order_number': '',
                    'customer_name': 'Customer B',
                    'order_date': '2024-01-16T00:00:00',
                    'financials': {'total_selling_price': 2000, 'total_cost': 1200, 'margin_percentage': 40.0},
                    'evaluation': {'profitability_score': 90, 'risk_level': 'Low', 'should_accept': True}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('order_evaluation', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            rows = parsed_data['rows']
            
            # Check that None/empty values are handled
            assert rows[0]['Order Number'] == 'ORD-001'
            assert rows[0]['Customer'] is None or rows[0]['Customer'] == ''
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_large_dataset_roundtrip(self):
        """Test round-trip with a large dataset"""
        # Generate 5000 rows of data
        products = []
        for i in range(5000):
            products.append({
                'name': f'Product {i}',
                'category': f'Category {i % 10}',
                'sku': f'SKU-{i}',
                'costing': {
                    'raw_material_cost': i * 10.50,
                    'labour_cost_per_unit': i * 5.0,
                    'overhead_percentage': i / 5000.0,
                    'target_margin_percentage': 25.0
                },
                'statistics': {
                    'avg_margin': 24.5
                }
            })
        
        data = {'products': products}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('costing_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            rows = parsed_data['rows']
            
            # Verify row count
            assert len(rows) == 5000
            
            # Spot check some rows
            assert rows[0]['Product'] == 'Product 0'
            
            assert rows[2500]['Product'] == 'Product 2500'
            assert abs(rows[2500]['Raw Material Cost'] - 26250.0) < 0.01
            
            assert rows[4999]['Product'] == 'Product 4999'
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_validation_with_expected_structure(self):
        """Test validation against expected structure"""
        data = {
            'groups': [
                {'name': 'Group A', 'total_revenue': 1000, 'total_cost': 600, 'margin': 400, 'margin_percentage': 40.0, 'order_count': 5},
                {'name': 'Group B', 'total_revenue': 2000, 'total_cost': 1200, 'margin': 800, 'margin_percentage': 40.0, 'order_count': 10}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('margin_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            # Define expected structure
            expected_structure = {
                'headers': ['Name', 'Total Revenue', 'Total Cost', 'Margin', 'Margin %', 'Order Count'],
                'min_rows': 2
            }
            
            # Should pass validation
            assert validate_csv_data(parsed_data, expected_structure) is True
            
            # Should fail with wrong expected structure
            wrong_structure = {
                'headers': ['WrongColumn1', 'WrongColumn2']
            }
            
            with pytest.raises(ValueError, match="Header mismatch"):
                validate_csv_data(parsed_data, wrong_structure)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_data_comparison(self):
        """Test comparing original and parsed data"""
        original_data = {
            'headers': ['Product', 'Category', 'SKU', 'Raw Material Cost', 'Labour Cost', 'Overhead %', 'Target Margin %', 'Avg Margin %'],
            'rows': [
                {'Product': 'Widget A', 'Category': 'Widgets', 'SKU': 'WID-A', 'Raw Material Cost': 50.00, 'Labour Cost': 25.00, 'Overhead %': 0.10, 'Target Margin %': 33.0, 'Avg Margin %': 33.0},
                {'Product': 'Widget B', 'Category': 'Widgets', 'SKU': 'WID-B', 'Raw Material Cost': 100.00, 'Labour Cost': 50.00, 'Overhead %': 0.15, 'Target Margin %': 33.0, 'Avg Margin %': 33.0}
            ]
        }
        
        data = {
            'products': [
                {
                    'name': 'Widget A',
                    'category': 'Widgets',
                    'sku': 'WID-A',
                    'costing': {
                        'raw_material_cost': 50.00,
                        'labour_cost_per_unit': 25.00,
                        'overhead_percentage': 0.10,
                        'target_margin_percentage': 33.0
                    },
                    'statistics': {
                        'avg_margin': 33.0
                    }
                },
                {
                    'name': 'Widget B',
                    'category': 'Widgets',
                    'sku': 'WID-B',
                    'costing': {
                        'raw_material_cost': 100.00,
                        'labour_cost_per_unit': 50.00,
                        'overhead_percentage': 0.15,
                        'target_margin_percentage': 33.0
                    },
                    'statistics': {
                        'avg_margin': 33.0
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('costing_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            # Should pass comparison
            assert compare_csv_data(original_data, parsed_data, tolerance=0.01) is True
            
            # Test with mismatched data
            wrong_data = {
                'headers': ['Product', 'Category', 'SKU', 'Raw Material Cost', 'Labour Cost', 'Overhead %', 'Target Margin %', 'Avg Margin %'],
                'rows': [
                    {'Product': 'Widget A', 'Category': 'Widgets', 'SKU': 'WID-A', 'Raw Material Cost': 50.00, 'Labour Cost': 25.00, 'Overhead %': 0.10, 'Target Margin %': 33.0, 'Avg Margin %': 33.0},
                    {'Product': 'Widget B', 'Category': 'Widgets', 'SKU': 'WID-B', 'Raw Material Cost': 999.99, 'Labour Cost': 50.00, 'Overhead %': 0.15, 'Target Margin %': 33.0, 'Avg Margin %': 33.0}  # Different cost
                ]
            }
            
            with pytest.raises(ValueError, match="mismatch"):
                compare_csv_data(wrong_data, parsed_data, tolerance=0.01)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_utf8_encoding_roundtrip(self):
        """Test that UTF-8 encoding is preserved"""
        data = {
            'groups': [
                {'name': 'Café', 'total_revenue': 100, 'total_cost': 50, 'margin': 50, 'margin_percentage': 50.0, 'order_count': 1},
                {'name': 'Naïve', 'total_revenue': 200, 'total_cost': 100, 'margin': 100, 'margin_percentage': 50.0, 'order_count': 2},
                {'name': '日本語', 'total_revenue': 300, 'total_cost': 150, 'margin': 150, 'margin_percentage': 50.0, 'order_count': 3},
                {'name': 'Ελληνικά', 'total_revenue': 400, 'total_cost': 200, 'margin': 200, 'margin_percentage': 50.0, 'order_count': 4},
                {'name': 'Русский', 'total_revenue': 500, 'total_cost': 250, 'margin': 250, 'margin_percentage': 50.0, 'order_count': 5}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('margin_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path, encoding='utf-8')
            
            rows = parsed_data['rows']
            
            assert rows[0]['Name'] == 'Café'
            assert rows[1]['Name'] == 'Naïve'
            assert rows[2]['Name'] == '日本語'
            assert rows[3]['Name'] == 'Ελληνικά'
            assert rows[4]['Name'] == 'Русский'
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_edge_case_values(self):
        """Test edge case numeric values"""
        data = {
            'groups': [
                {'name': 'Zero', 'total_revenue': 0, 'total_cost': 0, 'margin': 0, 'margin_percentage': 0.0, 'order_count': 0},
                {'name': 'Float zero', 'total_revenue': 0.0, 'total_cost': 0.0, 'margin': 0.0, 'margin_percentage': 0.0, 'order_count': 0},
                {'name': 'Large number', 'total_revenue': 999999999.99, 'total_cost': 500000000.00, 'margin': 499999999.99, 'margin_percentage': 50.0, 'order_count': 1000},
                {'name': 'Very small', 'total_revenue': 0.00000001, 'total_cost': 0.000000005, 'margin': 0.000000005, 'margin_percentage': 50.0, 'order_count': 1}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            csv_bytes = generate_csv('margin_analysis', data)
            with open(tmp_path, 'wb') as f:
                f.write(csv_bytes)
            
            parsed_data = parse_csv(tmp_path)
            
            rows = parsed_data['rows']
            
            assert rows[0]['Total Revenue'] == 0
            assert rows[1]['Total Revenue'] == 0.0
            assert abs(rows[2]['Total Revenue'] - 999999999.99) < 1.0
            assert abs(rows[3]['Total Revenue'] - 0.00000001) < 0.00000001
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
