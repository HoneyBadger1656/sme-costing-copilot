# backend/tests/test_email_templates.py

"""
Unit tests for email templates and rendering.

Tests cover:
- Template rendering with various contexts
- Plain text fallback generation
- Template validation
"""

import pytest
from datetime import datetime
from jinja2 import TemplateNotFound

from app.core.template_config import (
    render_template,
    validate_templates,
    get_jinja_env
)


class TestTemplateRendering:
    """Tests for template rendering"""
    
    def test_render_order_evaluation_complete_html(self):
        """Test rendering order evaluation complete HTML template"""
        context = {
            "user_name": "John Doe",
            "order_name": "Test Order",
            "order_id": "ORD-001",
            "total_cost": 50000.00,
            "margin_percentage": 25.5,
            "status": "Completed",
            "order_url": "https://example.com/orders/1",
            "insights": [
                "Material costs are within budget",
                "Labor efficiency is above average"
            ]
        }
        
        result = render_template("order_evaluation_complete.html", context)
        
        assert "John Doe" in result
        assert "Test Order" in result
        assert "ORD-001" in result
        assert "Material costs are within budget" in result
    
    def test_render_order_evaluation_complete_txt(self):
        """Test rendering order evaluation complete plain text template"""
        context = {
            "user_name": "John Doe",
            "order_name": "Test Order",
            "order_id": "ORD-001",
            "total_cost": 50000.00,
            "margin_percentage": 25.5,
            "status": "Completed",
            "order_url": "https://example.com/orders/1",
            "insights": [
                "Material costs are within budget",
                "Labor efficiency is above average"
            ]
        }
        
        result = render_template("order_evaluation_complete.txt", context)
        
        assert "John Doe" in result
        assert "Test Order" in result
        assert "ORD-001" in result
        assert "Material costs are within budget" in result
    
    def test_render_scenario_analysis_ready_html(self):
        """Test rendering scenario analysis ready HTML template"""
        context = {
            "user_name": "Jane Smith",
            "scenario_name": "Q1 2024 Analysis",
            "scenario_id": "SCN-001",
            "scenario_count": 3,
            "best_option": "Option B",
            "potential_savings": 75000.00,
            "scenario_url": "https://example.com/scenarios/1",
            "recommendations": [
                "Implement Option B for maximum savings",
                "Review supplier contracts quarterly"
            ]
        }
        
        result = render_template("scenario_analysis_ready.html", context)
        
        assert "Jane Smith" in result
        assert "Q1 2024 Analysis" in result
        assert "Option B" in result
    
    def test_render_sync_status_success_html(self):
        """Test rendering sync status success HTML template"""
        context = {
            "user_name": "Admin User",
            "integration_name": "QuickBooks",
            "status": "success",
            "records_synced": 150,
            "sync_duration": "2 minutes",
            "completed_at": datetime(2024, 1, 15, 10, 30),
            "integration_url": "https://example.com/integrations/1",
            "sync_summary": [
                "150 invoices synced",
                "50 customers updated"
            ]
        }
        
        result = render_template("sync_status.html", context)
        
        assert "Admin User" in result
        assert "QuickBooks" in result
        assert "completed successfully" in result
        assert "150" in result
    
    def test_render_sync_status_failure_html(self):
        """Test rendering sync status failure HTML template"""
        context = {
            "user_name": "Admin User",
            "integration_name": "QuickBooks",
            "status": "failed",
            "error_message": "Authentication failed",
            "failed_at": datetime(2024, 1, 15, 10, 30),
            "integration_url": "https://example.com/integrations/1"
        }
        
        result = render_template("sync_status.html", context)
        
        assert "Admin User" in result
        assert "QuickBooks" in result
        assert "encountered an issue" in result
        assert "Authentication failed" in result
    
    def test_render_low_margin_alert_html(self):
        """Test rendering low margin alert HTML template"""
        context = {
            "user_name": "Manager",
            "product_count": 3,
            "margin_threshold": 15.0,
            "revenue_impact": 25000.00,
            "alert_date": datetime(2024, 1, 15, 9, 0),
            "products": [
                {"name": "Product A", "current_margin": 12.5, "target_margin": 20.0},
                {"name": "Product B", "current_margin": 10.0, "target_margin": 18.0},
                {"name": "Product C", "current_margin": 14.5, "target_margin": 22.0}
            ],
            "products_url": "https://example.com/products"
        }
        
        result = render_template("low_margin_alert.html", context)
        
        assert "Manager" in result
        assert "Product A" in result
        assert "12.5%" in result
    
    def test_render_overdue_receivables_html(self):
        """Test rendering overdue receivables HTML template"""
        context = {
            "user_name": "Finance Manager",
            "invoice_count": 5,
            "total_overdue": 125000.00,
            "oldest_invoice_days": 45,
            "alert_date": datetime(2024, 1, 15, 9, 0),
            "invoices": [
                {
                    "client_name": "Client A",
                    "invoice_number": "INV-001",
                    "amount": 50000.00,
                    "days_overdue": 45
                },
                {
                    "client_name": "Client B",
                    "invoice_number": "INV-002",
                    "amount": 75000.00,
                    "days_overdue": 30
                }
            ],
            "invoices_url": "https://example.com/invoices"
        }
        
        result = render_template("overdue_receivables.html", context)
        
        assert "Finance Manager" in result
        assert "Client A" in result
        assert "INV-001" in result


class TestTemplateValidation:
    """Tests for template validation"""
    
    def test_validate_templates_all_exist(self):
        """Test that all required templates exist"""
        results = validate_templates()
        
        # Check that base templates exist
        assert results.get("base.html") is True
        assert results.get("base.txt") is True
    
    def test_render_nonexistent_template_raises_error(self):
        """Test that rendering nonexistent template raises error"""
        with pytest.raises(TemplateNotFound):
            render_template("nonexistent_template.html", {})


class TestTemplateFilters:
    """Tests for custom Jinja2 filters"""
    
    def test_currency_filter(self):
        """Test currency filter formats amounts correctly"""
        env = get_jinja_env()
        template = env.from_string("{{ amount|currency }}")
        
        result = template.render(amount=50000.50)
        assert "₹50,000.50" in result
    
    def test_datetime_filter(self):
        """Test datetime filter formats dates correctly"""
        env = get_jinja_env()
        template = env.from_string("{{ date|datetime }}")
        
        result = template.render(date=datetime(2024, 1, 15, 10, 30, 45))
        assert "2024-01-15 10:30:45" in result
    
    def test_date_filter(self):
        """Test date filter formats dates correctly"""
        env = get_jinja_env()
        template = env.from_string("{{ date|date }}")
        
        result = template.render(date=datetime(2024, 1, 15, 10, 30, 45))
        assert "2024-01-15" in result


class TestTemplateIntegration:
    """Integration tests for email templates"""
    
    def test_template_extends_base(self):
        """Test that templates properly extend base template"""
        context = {
            "user_name": "Test User",
            "order_name": "Test",
            "order_id": "1",
            "total_cost": 1000,
            "margin_percentage": 20,
            "status": "Complete",
            "order_url": "http://test.com",
            "insights": []
        }
        
        result = render_template("order_evaluation_complete.html", context)
        
        # Check that base template elements are present
        assert "SME Costing Copilot" in result
        assert "email-container" in result
        assert "email-header" in result
        assert "email-body" in result
        assert "email-footer" in result
    
    def test_unsubscribe_link_included_when_provided(self):
        """Test that unsubscribe link is included when provided in context"""
        context = {
            "user_name": "Test User",
            "order_name": "Test",
            "order_id": "1",
            "total_cost": 1000,
            "margin_percentage": 20,
            "status": "Complete",
            "order_url": "http://test.com",
            "insights": [],
            "unsubscribe_url": "https://example.com/unsubscribe"
        }
        
        result = render_template("order_evaluation_complete.html", context)
        
        assert "unsubscribe" in result.lower()
        assert "https://example.com/unsubscribe" in result
