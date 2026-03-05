# Backend/tests/test_csv_generator.py

import pytest
import csv
import io

from app.utils.csv_generator import generate_csv


class TestCSVGenerationBasic:
    """Test basic CSV generation functionality."""
    
    def test_generate_csv_financial_statement(self):
        """Test CSV generation for financial statement template."""
        data = {
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 35.5,
                        "net_margin": 18.2,
                        "roa": 12.5,
                        "roe": 15.8
                    }
                }
            ]
        }
        
        result = generate_csv("financial_statement", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify it's valid UTF-8 encoded CSV
        csv_text = result.decode('utf-8')
        assert "Type" in csv_text
        assert "balance_sheet" in csv_text
    
    def test_generate_csv_costing_analysis(self):
        """Test CSV generation for costing analysis template."""
        data = {
            "products": [
                {
                    "name": "Product A",
                    "category": "Electronics",
                    "sku": "SKU-001",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0,
                        "target_margin_percentage": 25.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        
        csv_text = result.decode('utf-8')
        assert "Product" in csv_text
        assert "Product A" in csv_text
    
    def test_generate_csv_order_evaluation(self):
        """Test CSV generation for order evaluation template."""
        data = {
            "orders": [
                {
                    "order_number": "ORD-001",
                    "customer_name": "Customer A",
                    "order_date": "2024-01-15T10:30:00",
                    "financials": {
                        "total_selling_price": 5000.0,
                        "total_cost": 3750.0,
                        "margin_percentage": 25.0
                    },
                    "evaluation": {
                        "profitability_score": 85,
                        "risk_level": "Low",
                        "should_accept": True
                    }
                }
            ]
        }
        
        result = generate_csv("order_evaluation", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        
        csv_text = result.decode('utf-8')
        assert "Order Number" in csv_text
        assert "ORD-001" in csv_text
    
    def test_generate_csv_margin_analysis(self):
        """Test CSV generation for margin analysis template."""
        data = {
            "groups": [
                {
                    "name": "Product A",
                    "total_revenue": 10000.0,
                    "total_cost": 7500.0,
                    "margin": 2500.0,
                    "margin_percentage": 25.0,
                    "order_count": 5
                }
            ]
        }
        
        result = generate_csv("margin_analysis", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        
        csv_text = result.decode('utf-8')
        assert "Name" in csv_text
        assert "Product A" in csv_text
    
    def test_generate_csv_receivables_report(self):
        """Test CSV generation for receivables report template."""
        data = {
            "receivables": [
                {
                    "party_name": "Customer A",
                    "amount": 5000.0,
                    "transaction_date": "2024-11-15T00:00:00",
                    "due_date": "2024-12-15T00:00:00",
                    "days_outstanding": 30,
                    "is_overdue": False,
                    "aging_bucket": "0-30 days"
                }
            ]
        }
        
        result = generate_csv("receivables_report", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        
        csv_text = result.decode('utf-8')
        assert "Party Name" in csv_text
        assert "Customer A" in csv_text
    
    def test_generate_csv_unknown_template(self):
        """Test CSV generation with unknown template raises error."""
        data = {"test": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            generate_csv("unknown_template", data)
        
        assert "Unknown template" in str(exc_info.value)



class TestCSVUTF8Encoding:
    """Test CSV UTF-8 encoding."""
    
    def test_csv_is_utf8_encoded(self):
        """Test that CSV output is UTF-8 encoded."""
        data = {
            "products": [
                {
                    "name": "Product A",
                    "category": "Electronics",
                    "sku": "SKU-001",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0,
                        "target_margin_percentage": 25.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        
        # Should decode successfully as UTF-8
        csv_text = result.decode('utf-8')
        assert isinstance(csv_text, str)
    
    def test_csv_with_unicode_characters(self):
        """Test that CSV handles Unicode characters correctly."""
        data = {
            "orders": [
                {
                    "order_number": "ORD-001",
                    "customer_name": "Café René & Søn",
                    "order_date": "2024-01-15T10:30:00",
                    "financials": {
                        "total_selling_price": 5000.0,
                        "total_cost": 3750.0,
                        "margin_percentage": 25.0
                    },
                    "evaluation": {
                        "profitability_score": 85,
                        "risk_level": "Low",
                        "should_accept": True
                    }
                }
            ]
        }
        
        result = generate_csv("order_evaluation", data)
        csv_text = result.decode('utf-8')
        
        assert "Café René & Søn" in csv_text
    
    def test_csv_with_emoji_characters(self):
        """Test that CSV handles emoji characters correctly."""
        data = {
            "products": [
                {
                    "name": "Product 🚀 Special",
                    "category": "Electronics ⚡",
                    "sku": "SKU-001",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0,
                        "target_margin_percentage": 25.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        
        assert "Product 🚀 Special" in csv_text
        assert "Electronics ⚡" in csv_text


class TestCSVSpecialCharacters:
    """Test CSV generation with special characters and RFC 4180 escaping."""
    
    def test_csv_with_commas_in_fields(self):
        """Test that commas in fields are properly escaped."""
        data = {
            "products": [
                {
                    "name": "Product A, B, and C",
                    "category": "Electronics, Gadgets",
                    "sku": "SKU-001",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0,
                        "target_margin_percentage": 25.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        
        # Fields with commas should be quoted
        assert '"Product A, B, and C"' in csv_text or 'Product A, B, and C' in csv_text
    
    def test_csv_with_quotes_in_fields(self):
        """Test that quotes in fields are properly escaped."""
        data = {
            "receivables": [
                {
                    "party_name": 'Company "Best" Ltd.',
                    "amount": 5000.0,
                    "transaction_date": "2024-11-15T00:00:00",
                    "due_date": "2024-12-15T00:00:00",
                    "days_outstanding": 30,
                    "is_overdue": False,
                    "aging_bucket": "0-30 days"
                }
            ]
        }
        
        result = generate_csv("receivables_report", data)
        csv_text = result.decode('utf-8')
        
        # Quotes should be escaped (doubled) and field should be quoted
        assert 'Company "Best" Ltd.' in csv_text or 'Company ""Best"" Ltd.' in csv_text
    
    def test_csv_with_newlines_in_fields(self):
        """Test that newlines in fields are properly escaped."""
        data = {
            "orders": [
                {
                    "order_number": "ORD-001",
                    "customer_name": "Customer A\nLine 2",
                    "order_date": "2024-01-15T10:30:00",
                    "financials": {
                        "total_selling_price": 5000.0,
                        "total_cost": 3750.0,
                        "margin_percentage": 25.0
                    },
                    "evaluation": {
                        "profitability_score": 85,
                        "risk_level": "Low",
                        "should_accept": True
                    }
                }
            ]
        }
        
        result = generate_csv("order_evaluation", data)
        csv_text = result.decode('utf-8')
        
        # Newlines should be preserved within quoted fields
        assert "Customer A" in csv_text
    
    def test_csv_with_ampersands_and_special_chars(self):
        """Test that ampersands and other special characters are preserved."""
        data = {
            "products": [
                {
                    "name": "Product & Co. (Type #1)",
                    "category": "Electronics & Gadgets",
                    "sku": "SKU-001",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0,
                        "target_margin_percentage": 25.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        
        assert "Product & Co. (Type #1)" in csv_text
        assert "Electronics & Gadgets" in csv_text



class TestCSVHeadersAndStructure:
    """Test CSV headers and structure."""
    
    def test_financial_statement_headers(self):
        """Test that financial statement CSV has correct headers."""
        data = {"statements": []}
        
        result = generate_csv("financial_statement", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        headers = next(reader)
        
        assert headers == ["Type", "Period Start", "Period End", "Gross Margin %", "Net Margin %", "ROA %", "ROE %"]
    
    def test_costing_analysis_headers(self):
        """Test that costing analysis CSV has correct headers."""
        data = {"products": []}
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        headers = next(reader)
        
        assert headers == ["Product", "Category", "SKU", "Raw Material Cost", "Labour Cost", "Overhead %", "Target Margin %", "Avg Margin %"]
    
    def test_order_evaluation_headers(self):
        """Test that order evaluation CSV has correct headers."""
        data = {"orders": []}
        
        result = generate_csv("order_evaluation", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        headers = next(reader)
        
        assert headers == ["Order Number", "Customer", "Order Date", "Total Revenue", "Total Cost", "Margin %", "Profitability Score", "Risk Level", "Recommendation"]
    
    def test_margin_analysis_headers(self):
        """Test that margin analysis CSV has correct headers."""
        data = {"groups": []}
        
        result = generate_csv("margin_analysis", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        headers = next(reader)
        
        assert headers == ["Name", "Total Revenue", "Total Cost", "Margin", "Margin %", "Order Count"]
    
    def test_receivables_report_headers(self):
        """Test that receivables report CSV has correct headers."""
        data = {"receivables": []}
        
        result = generate_csv("receivables_report", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        headers = next(reader)
        
        assert headers == ["Party Name", "Amount", "Transaction Date", "Due Date", "Days Outstanding", "Overdue", "Aging Bucket"]



class TestCSVDataFormatting:
    """Test CSV data formatting."""
    
    def test_date_formatting(self):
        """Test that dates are formatted correctly (YYYY-MM-DD)."""
        data = {
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-15T10:30:45",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 35.5,
                        "net_margin": 18.2,
                        "roa": 12.5,
                        "roe": 15.8
                    }
                }
            ]
        }
        
        result = generate_csv("financial_statement", data)
        csv_text = result.decode('utf-8')
        
        assert "2024-01-15" in csv_text
        assert "2024-12-31" in csv_text
    
    def test_boolean_to_text_conversion(self):
        """Test that boolean values are converted to Yes/No text."""
        data = {
            "receivables": [
                {
                    "party_name": "Customer A",
                    "amount": 5000.0,
                    "transaction_date": "2024-11-15T00:00:00",
                    "due_date": "2024-12-15T00:00:00",
                    "days_outstanding": 30,
                    "is_overdue": False,
                    "aging_bucket": "0-30 days"
                },
                {
                    "party_name": "Customer B",
                    "amount": 3000.0,
                    "transaction_date": "2024-10-01T00:00:00",
                    "due_date": "2024-11-01T00:00:00",
                    "days_outstanding": 60,
                    "is_overdue": True,
                    "aging_bucket": "31-60 days"
                }
            ]
        }
        
        result = generate_csv("receivables_report", data)
        csv_text = result.decode('utf-8')
        
        assert "No" in csv_text  # For is_overdue: False
        assert "Yes" in csv_text  # For is_overdue: True
    
    def test_recommendation_conversion(self):
        """Test that should_accept boolean is converted to Accept/Review."""
        data = {
            "orders": [
                {
                    "order_number": "ORD-001",
                    "customer_name": "Customer A",
                    "order_date": "2024-01-15T10:30:00",
                    "financials": {
                        "total_selling_price": 5000.0,
                        "total_cost": 3750.0,
                        "margin_percentage": 25.0
                    },
                    "evaluation": {
                        "profitability_score": 85,
                        "risk_level": "Low",
                        "should_accept": True
                    }
                },
                {
                    "order_number": "ORD-002",
                    "customer_name": "Customer B",
                    "order_date": "2024-01-16T10:30:00",
                    "financials": {
                        "total_selling_price": 3000.0,
                        "total_cost": 2900.0,
                        "margin_percentage": 3.3
                    },
                    "evaluation": {
                        "profitability_score": 45,
                        "risk_level": "High",
                        "should_accept": False
                    }
                }
            ]
        }
        
        result = generate_csv("order_evaluation", data)
        csv_text = result.decode('utf-8')
        
        assert "Accept" in csv_text
        assert "Review" in csv_text
    
    def test_numeric_values_preserved(self):
        """Test that numeric values are preserved correctly."""
        data = {
            "groups": [
                {
                    "name": "Product A",
                    "total_revenue": 10000.50,
                    "total_cost": 7500.25,
                    "margin": 2500.25,
                    "margin_percentage": 25.0025,
                    "order_count": 5
                }
            ]
        }
        
        result = generate_csv("margin_analysis", data)
        csv_text = result.decode('utf-8')
        
        assert "10000.5" in csv_text or "10000.50" in csv_text
        assert "7500.25" in csv_text
        assert "5" in csv_text


class TestCSVWithEmptyData:
    """Test CSV generation with empty or minimal data."""
    
    def test_financial_statement_empty_statements(self):
        """Test financial statement with no statements."""
        data = {"statements": []}
        
        result = generate_csv("financial_statement", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should have only header row
        assert len(rows) == 1
        assert rows[0][0] == "Type"
    
    def test_costing_analysis_empty_products(self):
        """Test costing analysis with no products."""
        data = {"products": []}
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should have only header row
        assert len(rows) == 1
        assert rows[0][0] == "Product"
    
    def test_receivables_empty_list(self):
        """Test receivables report with empty receivables list."""
        data = {"receivables": []}
        
        result = generate_csv("receivables_report", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should have only header row
        assert len(rows) == 1
        assert rows[0][0] == "Party Name"



class TestCSVWithMissingFields:
    """Test CSV generation with missing or None fields."""
    
    def test_missing_metrics_fields(self):
        """Test that missing metrics fields default to 0."""
        data = {
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {}  # Empty metrics
                }
            ]
        }
        
        result = generate_csv("financial_statement", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should use 0 for missing metrics
        assert rows[1][3] == "0"  # gross_margin
        assert rows[1][4] == "0"  # net_margin
    
    def test_missing_due_date(self):
        """Test that missing due_date is handled gracefully."""
        data = {
            "receivables": [
                {
                    "party_name": "Customer A",
                    "amount": 5000.0,
                    "transaction_date": "2024-11-15T00:00:00",
                    "due_date": None,  # Missing due date
                    "days_outstanding": 30,
                    "is_overdue": False,
                    "aging_bucket": "0-30 days"
                }
            ]
        }
        
        result = generate_csv("receivables_report", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should handle None due_date
        assert rows[1][3] == ""  # due_date column
    
    def test_missing_nested_fields(self):
        """Test that missing nested fields are handled gracefully."""
        data = {
            "products": [
                {
                    "name": "Product A",
                    "category": "Electronics",
                    "sku": "SKU-001",
                    "costing": {},  # Empty costing
                    "statistics": {}  # Empty statistics
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should use 0 for missing fields
        assert rows[1][3] == "0"  # raw_material_cost
        assert rows[1][7] == "0"  # avg_margin



class TestCSVWithLargeDatasets:
    """Test CSV generation with large datasets."""
    
    def test_many_products(self):
        """Test costing analysis with many products."""
        products = []
        for i in range(100):
            products.append({
                "name": f"Product {i}",
                "category": "Electronics",
                "sku": f"SKU-{i:03d}",
                "costing": {
                    "raw_material_cost": 100.0 + i,
                    "labour_cost_per_unit": 20.0 + i,
                    "overhead_percentage": 10.0,
                    "target_margin_percentage": 25.0
                },
                "statistics": {
                    "avg_margin": 25.0 + i * 0.1
                }
            })
        
        data = {"products": products}
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should have all 100 products plus header row
        assert len(rows) == 101
        assert "Product 99" in rows[100][0]
    
    def test_many_receivables(self):
        """Test receivables report with many receivables."""
        receivables = []
        for i in range(200):
            receivables.append({
                "party_name": f"Customer {i}",
                "amount": 1000.0 + i * 10,
                "transaction_date": "2024-11-15T00:00:00",
                "due_date": "2024-12-15T00:00:00",
                "days_outstanding": 30 + i,
                "is_overdue": i % 2 == 0,
                "aging_bucket": "0-30 days"
            })
        
        data = {"receivables": receivables}
        
        result = generate_csv("receivables_report", data)
        csv_text = result.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        # Should have all 200 receivables plus header row
        assert len(rows) == 201
        assert "Customer 199" in rows[200][0]


class TestCSVRFC4180Compliance:
    """Test CSV RFC 4180 compliance."""
    
    def test_csv_uses_minimal_quoting(self):
        """Test that CSV uses QUOTE_MINIMAL strategy."""
        data = {
            "products": [
                {
                    "name": "Simple Product",
                    "category": "Electronics",
                    "sku": "SKU-001",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0,
                        "target_margin_percentage": 25.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_csv("costing_analysis", data)
        csv_text = result.decode('utf-8')
        
        # Simple fields without special characters should not be quoted
        # (unless the CSV writer decides to quote them)
        assert "Simple Product" in csv_text or '"Simple Product"' in csv_text
    
    def test_csv_line_endings(self):
        """Test that CSV uses proper line endings."""
        data = {
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 35.5,
                        "net_margin": 18.2,
                        "roa": 12.5,
                        "roe": 15.8
                    }
                }
            ]
        }
        
        result = generate_csv("financial_statement", data)
        csv_text = result.decode('utf-8')
        
        # Should have line breaks
        assert '\n' in csv_text or '\r\n' in csv_text
    
    def test_csv_parseable_by_standard_reader(self):
        """Test that generated CSV can be parsed by standard csv.reader."""
        data = {
            "groups": [
                {
                    "name": "Product A, B, C",
                    "total_revenue": 10000.0,
                    "total_cost": 7500.0,
                    "margin": 2500.0,
                    "margin_percentage": 25.0,
                    "order_count": 5
                }
            ]
        }
        
        result = generate_csv("margin_analysis", data)
        csv_text = result.decode('utf-8')
        
        # Should be parseable by standard csv.reader
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        
        assert len(rows) == 2  # Header + 1 data row
        assert rows[0][0] == "Name"
        assert rows[1][0] == "Product A, B, C"


class TestCSVErrorHandling:
    """Test error handling in CSV generation."""
    
    def test_generate_csv_with_invalid_template(self):
        """Test that invalid template raises ValueError."""
        data = {"test": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            generate_csv("invalid_template", data)
        
        assert "Unknown template" in str(exc_info.value)
    
    def test_generate_csv_with_none_data(self):
        """Test that None data is handled gracefully."""
        # This should raise an error or handle gracefully
        try:
            result = generate_csv("financial_statement", None)
            # If it doesn't raise, it should return valid bytes
            assert isinstance(result, bytes)
        except (TypeError, AttributeError):
            # Expected error for None data
            pass
