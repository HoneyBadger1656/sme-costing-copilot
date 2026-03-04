# backend/app/services/report_templates.py

from typing import Dict, List, Any
from enum import Enum


class ReportFormat(str, Enum):
    """Supported report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ReportTemplate:
    """Report template definition"""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        data_sources: List[str],
        supported_formats: List[ReportFormat],
        parameters: Dict[str, Any],
        layout_config: Dict[str, Any]
    ):
        self.id = id
        self.name = name
        self.description = description
        self.data_sources = data_sources
        self.supported_formats = supported_formats
        self.parameters = parameters
        self.layout_config = layout_config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "data_sources": self.data_sources,
            "supported_formats": [f.value for f in self.supported_formats],
            "parameters": self.parameters,
            "layout_config": self.layout_config
        }


# Define available report templates
REPORT_TEMPLATES = {
    "financial_statement": ReportTemplate(
        id="financial_statement",
        name="Financial Statement",
        description="Comprehensive financial statement including Balance Sheet, P&L, and Cash Flow",
        data_sources=["financial_statements", "financial_ratios"],
        supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL],
        parameters={
            "period_type": {
                "type": "string",
                "required": True,
                "options": ["monthly", "quarterly", "yearly"],
                "description": "Period type for the financial statement"
            },
            "period_start": {
                "type": "date",
                "required": True,
                "description": "Start date of the period"
            },
            "period_end": {
                "type": "date",
                "required": True,
                "description": "End date of the period"
            },
            "include_charts": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include charts and visualizations"
            },
            "include_ratios": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include financial ratios analysis"
            }
        },
        layout_config={
            "page_size": "A4",
            "orientation": "portrait",
            "sections": ["cover", "balance_sheet", "profit_loss", "cash_flow", "ratios"]
        }
    ),
    
    "costing_analysis": ReportTemplate(
        id="costing_analysis",
        name="Costing Analysis",
        description="Detailed product costing analysis with margin breakdown",
        data_sources=["products", "bom_items", "orders"],
        supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL, ReportFormat.CSV],
        parameters={
            "date_range": {
                "type": "object",
                "required": True,
                "description": "Date range for the analysis",
                "properties": {
                    "start": {"type": "date"},
                    "end": {"type": "date"}
                }
            },
            "product_ids": {
                "type": "array",
                "required": False,
                "description": "Specific product IDs to include (empty for all)"
            },
            "include_bom": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include Bill of Materials breakdown"
            },
            "min_margin_threshold": {
                "type": "number",
                "required": False,
                "default": 0,
                "description": "Minimum margin percentage threshold"
            }
        },
        layout_config={
            "page_size": "A4",
            "orientation": "landscape",
            "sections": ["summary", "product_details", "bom_breakdown", "margin_analysis"]
        }
    ),
    
    "order_evaluation": ReportTemplate(
        id="order_evaluation",
        name="Order Evaluation Report",
        description="Order profitability evaluation with recommendations",
        data_sources=["orders", "order_items", "order_evaluations"],
        supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL],
        parameters={
            "date_range": {
                "type": "object",
                "required": True,
                "description": "Date range for orders",
                "properties": {
                    "start": {"type": "date"},
                    "end": {"type": "date"}
                }
            },
            "status": {
                "type": "string",
                "required": False,
                "options": ["draft", "confirmed", "invoiced", "completed"],
                "description": "Filter by order status"
            },
            "min_profitability_score": {
                "type": "number",
                "required": False,
                "default": 0,
                "description": "Minimum profitability score (0-100)"
            }
        },
        layout_config={
            "page_size": "A4",
            "orientation": "portrait",
            "sections": ["summary", "order_list", "evaluations", "recommendations"]
        }
    ),
    
    "margin_analysis": ReportTemplate(
        id="margin_analysis",
        name="Margin Analysis Report",
        description="Product and order margin analysis with trends",
        data_sources=["products", "orders", "order_items"],
        supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL, ReportFormat.CSV],
        parameters={
            "date_range": {
                "type": "object",
                "required": True,
                "description": "Date range for the analysis",
                "properties": {
                    "start": {"type": "date"},
                    "end": {"type": "date"}
                }
            },
            "group_by": {
                "type": "string",
                "required": False,
                "options": ["product", "customer", "category"],
                "default": "product",
                "description": "Group margins by"
            },
            "include_trends": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include trend analysis"
            }
        },
        layout_config={
            "page_size": "A4",
            "orientation": "landscape",
            "sections": ["summary", "margin_breakdown", "trends", "insights"]
        }
    ),
    
    "receivables_report": ReportTemplate(
        id="receivables_report",
        name="Receivables Report",
        description="Accounts receivable aging and analysis",
        data_sources=["ledgers", "orders"],
        supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL, ReportFormat.CSV],
        parameters={
            "as_of_date": {
                "type": "date",
                "required": True,
                "description": "Report date"
            },
            "aging_buckets": {
                "type": "array",
                "required": False,
                "default": [30, 60, 90],
                "description": "Aging bucket days (e.g., [30, 60, 90])"
            },
            "include_overdue_only": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Include only overdue receivables"
            }
        },
        layout_config={
            "page_size": "A4",
            "orientation": "landscape",
            "sections": ["summary", "aging_analysis", "customer_breakdown", "overdue_details"]
        }
    )
}


def get_all_templates() -> List[Dict[str, Any]]:
    """
    Get all available report templates.
    
    Returns:
        List of template dictionaries
    """
    return [template.to_dict() for template in REPORT_TEMPLATES.values()]


def get_template(template_id: str) -> ReportTemplate:
    """
    Get a specific report template by ID.
    
    Args:
        template_id: Template ID
    
    Returns:
        ReportTemplate object
    
    Raises:
        ValueError: If template not found
    """
    if template_id not in REPORT_TEMPLATES:
        raise ValueError(f"Template '{template_id}' not found")
    
    return REPORT_TEMPLATES[template_id]


def validate_template_parameters(template_id: str, parameters: Dict[str, Any]) -> bool:
    """
    Validate parameters for a report template.
    
    Args:
        template_id: Template ID
        parameters: Parameters to validate
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If validation fails
    """
    template = get_template(template_id)
    
    # Check required parameters
    for param_name, param_config in template.parameters.items():
        if param_config.get("required", False):
            if param_name not in parameters:
                raise ValueError(f"Required parameter '{param_name}' is missing")
    
    # Validate parameter types and values
    for param_name, param_value in parameters.items():
        if param_name not in template.parameters:
            # Allow extra parameters (they might be used by specific implementations)
            continue
        
        param_config = template.parameters[param_name]
        param_type = param_config.get("type")
        
        # Validate options if specified
        if "options" in param_config:
            if param_value not in param_config["options"]:
                raise ValueError(
                    f"Parameter '{param_name}' must be one of {param_config['options']}"
                )
    
    return True


def is_format_supported(template_id: str, format: str) -> bool:
    """
    Check if a format is supported for a template.
    
    Args:
        template_id: Template ID
        format: Format to check (pdf, excel, csv)
    
    Returns:
        True if format is supported
    """
    template = get_template(template_id)
    
    try:
        format_enum = ReportFormat(format.lower())
        return format_enum in template.supported_formats
    except ValueError:
        return False
