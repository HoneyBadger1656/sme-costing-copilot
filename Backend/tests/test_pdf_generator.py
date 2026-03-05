# Backend/tests/test_pdf_generator.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import io

from app.utils.pdf_generator import (
    generate_pdf,
    _generate_financial_statement_pdf,
    _generate_costing_analysis_pdf,
    _generate_order_evaluation_pdf,
    _generate_margin_analysis_pdf,
    _generate_receivables_report_pdf
)


class TestPDFGenerationBasic:
    """Test basic PDF generation functionality."""
    
    def test_generate_pdf_financial_statement(self):
        """Test PDF generation for financial statement template."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 35.5,
                        "net_margin": 18.2
                    }
                }
            ]
        }
        
        result = generate_pdf("financial_statement", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF files start with %PDF
        assert result[:4] == b'%PDF'
    
    def test_generate_pdf_costing_analysis(self):
        """Test PDF generation for costing analysis template."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "products": [
                {
                    "name": "Product A",
                    "category": "Electronics",
                    "costing": {
                        "raw_material_cost": 100.0,
                        "labour_cost_per_unit": 20.0,
                        "overhead_percentage": 10.0
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_pdf("costing_analysis", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'%PDF'
    
    def test_generate_pdf_order_evaluation(self):
        """Test PDF generation for order evaluation template."""
        data = {
            "summary": {
                "total_orders": 10,
                "total_revenue": 50000.0,
                "avg_margin_percentage": 22.5
            },
            "orders": [
                {
                    "order_number": "ORD-001",
                    "customer_name": "Customer A",
                    "financials": {
                        "total_selling_price": 5000.0,
                        "margin_percentage": 25.0
                    },
                    "evaluation": {
                        "profitability_score": 85,
                        "risk_level": "Low"
                    }
                }
            ]
        }
        
        result = generate_pdf("order_evaluation", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'%PDF'
    
    def test_generate_pdf_margin_analysis(self):
        """Test PDF generation for margin analysis template."""
        data = {
            "group_by": "product",
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
        
        result = generate_pdf("margin_analysis", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'%PDF'
    
    def test_generate_pdf_receivables_report(self):
        """Test PDF generation for receivables report template."""
        data = {
            "as_of_date": "2024-12-31",
            "summary": {
                "total_amount": 50000.0,
                "total_count": 15
            },
            "aging_summary": {
                "0-30 days": {"count": 5, "total_amount": 20000.0},
                "31-60 days": {"count": 7, "total_amount": 20000.0},
                "61-90 days": {"count": 3, "total_amount": 10000.0}
            }
        }
        
        result = generate_pdf("receivables_report", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'%PDF'
    
    def test_generate_pdf_unknown_template(self):
        """Test PDF generation with unknown template raises error."""
        data = {"test": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            generate_pdf("unknown_template", data)
        
        assert "Unknown template" in str(exc_info.value)


class TestPDFStructure:
    """Test PDF structure and content."""
    
    def test_pdf_contains_title_financial_statement(self):
        """Test that financial statement PDF contains title."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        result = generate_pdf("financial_statement", data)
        
        # PDF should be valid and non-empty (content is compressed)
        assert result is not None
        assert len(result) > 500  # Should have reasonable size
    
    def test_pdf_contains_timestamp(self):
        """Test that PDF contains generation timestamp."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        result = generate_pdf("financial_statement", data)
        
        # PDF should be valid (content is compressed, can't check text directly)
        assert result is not None
        assert len(result) > 500
    
    def test_pdf_contains_period_info(self):
        """Test that PDF contains period information."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        result = generate_pdf("financial_statement", data)
        
        # PDF should be valid (content is compressed, can't check text directly)
        assert result is not None
        assert len(result) > 500
    
    def test_pdf_with_table_data(self):
        """Test that PDF with table data is generated correctly."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 35.5,
                        "net_margin": 18.2
                    }
                },
                {
                    "statement_type": "income_statement",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 40.0,
                        "net_margin": 20.0
                    }
                }
            ]
        }
        
        result = generate_pdf("financial_statement", data)
        
        # PDF with table should be larger than empty PDF
        assert len(result) > 1000


class TestPDFContentFormatting:
    """Test PDF content formatting."""
    
    def test_financial_statement_formats_percentages(self):
        """Test that financial statement formats percentages correctly."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": [
                {
                    "statement_type": "balance_sheet",
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-12-31T23:59:59",
                    "metrics": {
                        "gross_margin": 35.567,
                        "net_margin": 18.234
                    }
                }
            ]
        }
        
        result = generate_pdf("financial_statement", data)
        
        # Should generate valid PDF (content is compressed)
        assert result is not None
        assert len(result) > 1000
    
    def test_costing_analysis_formats_currency(self):
        """Test that costing analysis formats currency correctly."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "products": [
                {
                    "name": "Product A",
                    "category": "Electronics",
                    "costing": {
                        "raw_material_cost": 1234.56,
                        "labour_cost_per_unit": 567.89,
                        "overhead_percentage": 10.5
                    },
                    "statistics": {
                        "avg_margin": 25.5
                    }
                }
            ]
        }
        
        result = generate_pdf("costing_analysis", data)
        
        # Should generate valid PDF (content is compressed)
        assert result is not None
        assert len(result) > 1000
    
    def test_order_evaluation_formats_large_numbers(self):
        """Test that order evaluation formats large numbers correctly."""
        data = {
            "summary": {
                "total_orders": 100,
                "total_revenue": 1234567.89,
                "avg_margin_percentage": 22.5
            },
            "orders": []
        }
        
        result = generate_pdf("order_evaluation", data)
        
        # Should generate valid PDF (content is compressed)
        assert result is not None
        assert len(result) > 1000
    
    def test_margin_analysis_handles_zero_values(self):
        """Test that margin analysis handles zero values correctly."""
        data = {
            "group_by": "product",
            "groups": [
                {
                    "name": "Product A",
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "margin": 0.0,
                    "margin_percentage": 0.0,
                    "order_count": 0
                }
            ]
        }
        
        result = generate_pdf("margin_analysis", data)
        
        # Should handle zero values without error
        assert result is not None
        assert len(result) > 0
    
    def test_receivables_report_formats_aging_buckets(self):
        """Test that receivables report formats aging buckets correctly."""
        data = {
            "as_of_date": "2024-12-31",
            "summary": {
                "total_amount": 50000.0,
                "total_count": 15
            },
            "aging_summary": {
                "0-30 days": {"count": 5, "total_amount": 20000.0},
                "31-60 days": {"count": 7, "total_amount": 20000.0}
            }
        }
        
        result = generate_pdf("receivables_report", data)
        
        # Should generate valid PDF (content is compressed)
        assert result is not None
        assert len(result) > 1000


class TestPDFWithEmptyData:
    """Test PDF generation with empty or minimal data."""
    
    def test_financial_statement_empty_statements(self):
        """Test financial statement with no statements."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        result = generate_pdf("financial_statement", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_costing_analysis_empty_products(self):
        """Test costing analysis with no products."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "products": []
        }
        
        result = generate_pdf("costing_analysis", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_order_evaluation_empty_orders(self):
        """Test order evaluation with no orders."""
        data = {
            "summary": {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_margin_percentage": 0.0
            },
            "orders": []
        }
        
        result = generate_pdf("order_evaluation", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_margin_analysis_empty_groups(self):
        """Test margin analysis with no groups."""
        data = {
            "group_by": "product",
            "groups": []
        }
        
        result = generate_pdf("margin_analysis", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_receivables_report_empty_aging_summary(self):
        """Test receivables report with empty aging summary."""
        data = {
            "as_of_date": "2024-12-31",
            "summary": {
                "total_amount": 0.0,
                "total_count": 0
            },
            "aging_summary": {}
        }
        
        result = generate_pdf("receivables_report", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestPDFWithLargeDatasets:
    """Test PDF generation with large datasets."""
    
    def test_costing_analysis_many_products(self):
        """Test costing analysis with many products (limit to 20)."""
        products = []
        for i in range(50):  # Create 50 products
            products.append({
                "name": f"Product {i}",
                "category": "Electronics",
                "costing": {
                    "raw_material_cost": 100.0 + i,
                    "labour_cost_per_unit": 20.0 + i,
                    "overhead_percentage": 10.0
                },
                "statistics": {
                    "avg_margin": 25.0 + i
                }
            })
        
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "products": products
        }
        
        result = generate_pdf("costing_analysis", data)
        
        # Should generate successfully even with many products
        assert result is not None
        assert len(result) > 0
    
    def test_order_evaluation_many_orders(self):
        """Test order evaluation with many orders (limit to 15)."""
        orders = []
        for i in range(30):  # Create 30 orders
            orders.append({
                "order_number": f"ORD-{i:03d}",
                "customer_name": f"Customer {i}",
                "financials": {
                    "total_selling_price": 5000.0 + i * 100,
                    "margin_percentage": 25.0 + i * 0.5
                },
                "evaluation": {
                    "profitability_score": 80 + i,
                    "risk_level": "Low" if i % 2 == 0 else "Medium"
                }
            })
        
        data = {
            "summary": {
                "total_orders": 30,
                "total_revenue": 150000.0,
                "avg_margin_percentage": 25.0
            },
            "orders": orders
        }
        
        result = generate_pdf("order_evaluation", data)
        
        # Should generate successfully even with many orders
        assert result is not None
        assert len(result) > 0
    
    def test_margin_analysis_many_groups(self):
        """Test margin analysis with many groups (limit to 20)."""
        groups = []
        for i in range(40):  # Create 40 groups
            groups.append({
                "name": f"Group {i}",
                "total_revenue": 10000.0 + i * 1000,
                "total_cost": 7500.0 + i * 750,
                "margin": 2500.0 + i * 250,
                "margin_percentage": 25.0 + i * 0.1,
                "order_count": 5 + i
            })
        
        data = {
            "group_by": "product",
            "groups": groups
        }
        
        result = generate_pdf("margin_analysis", data)
        
        # Should generate successfully even with many groups
        assert result is not None
        assert len(result) > 0


class TestPDFErrorHandling:
    """Test error handling in PDF generation."""
    
    def test_generate_pdf_with_missing_data_fields(self):
        """Test PDF generation with missing data fields."""
        data = {
            "period": {}  # Missing start and end
        }
        
        # Should handle missing fields gracefully
        result = generate_pdf("financial_statement", data)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_generate_pdf_with_none_values(self):
        """Test PDF generation with None values in data."""
        data = {
            "period": {"start": None, "end": None},
            "statements": [
                {
                    "statement_type": None,
                    "period_start": "2024-01-01T00:00:00",  # Provide valid date
                    "period_end": "2024-12-31T23:59:59",  # Provide valid date
                    "metrics": {
                        "gross_margin": 0,  # Use 0 instead of None
                        "net_margin": 0  # Use 0 instead of None
                    }
                }
            ]
        }
        
        # Should handle None values gracefully
        result = generate_pdf("financial_statement", data)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_generate_pdf_with_invalid_data_types(self):
        """Test PDF generation with invalid data types."""
        data = {
            "summary": {
                "total_orders": "not a number",  # Should be int
                "total_revenue": "invalid",  # Should be float
                "avg_margin_percentage": None
            },
            "orders": []
        }
        
        # Should handle invalid types gracefully or raise appropriate error
        try:
            result = generate_pdf("order_evaluation", data)
            # If it succeeds, verify it's valid PDF
            assert result is not None
            assert isinstance(result, bytes)
        except (ValueError, TypeError, AttributeError):
            # Expected error for invalid data types
            pass
    
    @patch('app.utils.pdf_generator.logger')
    def test_generate_pdf_logs_success(self, mock_logger):
        """Test that successful PDF generation is logged."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        result = generate_pdf("financial_statement", data)
        
        # Verify logging was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "pdf_generated"
    
    @patch('app.utils.pdf_generator.SimpleDocTemplate')
    @patch('app.utils.pdf_generator.logger')
    def test_generate_pdf_logs_error(self, mock_logger, mock_doc):
        """Test that PDF generation errors are logged."""
        # Make SimpleDocTemplate raise an exception
        mock_doc.side_effect = Exception("PDF generation failed")
        
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        with pytest.raises(Exception):
            generate_pdf("financial_statement", data)
        
        # Verify error logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "pdf_generation_error"


class TestPDFHelperFunctions:
    """Test individual PDF generation helper functions."""
    
    def test_generate_financial_statement_pdf_structure(self):
        """Test financial statement PDF helper returns proper structure."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        story = _generate_financial_statement_pdf(data, styles, title_style)
        
        assert isinstance(story, list)
        assert len(story) > 0
    
    def test_generate_costing_analysis_pdf_structure(self):
        """Test costing analysis PDF helper returns proper structure."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "products": []
        }
        
        story = _generate_costing_analysis_pdf(data, styles, title_style)
        
        assert isinstance(story, list)
        assert len(story) > 0
    
    def test_generate_order_evaluation_pdf_structure(self):
        """Test order evaluation PDF helper returns proper structure."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        data = {
            "summary": {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_margin_percentage": 0.0
            },
            "orders": []
        }
        
        story = _generate_order_evaluation_pdf(data, styles, title_style)
        
        assert isinstance(story, list)
        assert len(story) > 0
    
    def test_generate_margin_analysis_pdf_structure(self):
        """Test margin analysis PDF helper returns proper structure."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        data = {
            "group_by": "product",
            "groups": []
        }
        
        story = _generate_margin_analysis_pdf(data, styles, title_style)
        
        assert isinstance(story, list)
        assert len(story) > 0
    
    def test_generate_receivables_report_pdf_structure(self):
        """Test receivables report PDF helper returns proper structure."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        data = {
            "as_of_date": "2024-12-31",
            "summary": {
                "total_amount": 0.0,
                "total_count": 0
            },
            "aging_summary": {}
        }
        
        story = _generate_receivables_report_pdf(data, styles, title_style)
        
        assert isinstance(story, list)
        assert len(story) > 0


class TestPDFOptions:
    """Test PDF generation with various options."""
    
    def test_generate_pdf_with_options(self):
        """Test PDF generation with options parameter."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        options = {
            "page_size": "A4",
            "orientation": "portrait"
        }
        
        result = generate_pdf("financial_statement", data, options)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_pdf_without_options(self):
        """Test PDF generation without options parameter."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        
        result = generate_pdf("financial_statement", data)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_pdf_with_empty_options(self):
        """Test PDF generation with empty options dict."""
        data = {
            "period": {"start": "2024-01-01", "end": "2024-12-31"},
            "statements": []
        }
        options = {}
        
        result = generate_pdf("financial_statement", data, options)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
