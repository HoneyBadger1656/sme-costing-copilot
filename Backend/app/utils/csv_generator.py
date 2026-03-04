# backend/app/utils/csv_generator.py

import csv
import io
from typing import Dict, Any, List
from datetime import datetime

from app.logging_config import get_logger

logger = get_logger(__name__)


def generate_csv(template_id: str, data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
    """
    Generate CSV report from template and data.
    
    Args:
        template_id: Report template ID
        data: Report data
        options: Generation options
    
    Returns:
        CSV file as bytes (UTF-8 encoded)
    """
    try:
        buffer = io.StringIO()
        
        # Generate CSV based on template
        if template_id == "financial_statement":
            _generate_financial_statement_csv(buffer, data)
        elif template_id == "costing_analysis":
            _generate_costing_analysis_csv(buffer, data)
        elif template_id == "order_evaluation":
            _generate_order_evaluation_csv(buffer, data)
        elif template_id == "margin_analysis":
            _generate_margin_analysis_csv(buffer, data)
        elif template_id == "receivables_report":
            _generate_receivables_report_csv(buffer, data)
        else:
            raise ValueError(f"Unknown template: {template_id}")
        
        # Convert to bytes with UTF-8 encoding
        csv_bytes = buffer.getvalue().encode('utf-8')
        buffer.close()
        
        logger.info("csv_generated", template_id=template_id, size=len(csv_bytes))
        return csv_bytes
        
    except Exception as e:
        logger.error("csv_generation_error", error=str(e), template_id=template_id)
        raise


def _generate_financial_statement_csv(buffer: io.StringIO, data: Dict[str, Any]):
    """Generate financial statement CSV"""
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    
    # Headers
    writer.writerow(["Type", "Period Start", "Period End", "Gross Margin %", "Net Margin %", "ROA %", "ROE %"])
    
    # Data
    statements = data.get("statements", [])
    for stmt in statements:
        metrics = stmt.get("metrics", {})
        writer.writerow([
            stmt.get("statement_type", ""),
            stmt.get("period_start", "")[:10],
            stmt.get("period_end", "")[:10],
            metrics.get("gross_margin", 0),
            metrics.get("net_margin", 0),
            metrics.get("roa", 0),
            metrics.get("roe", 0)
        ])


def _generate_costing_analysis_csv(buffer: io.StringIO, data: Dict[str, Any]):
    """Generate costing analysis CSV"""
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    
    # Headers
    writer.writerow(["Product", "Category", "SKU", "Raw Material Cost", "Labour Cost", "Overhead %", "Target Margin %", "Avg Margin %"])
    
    # Data
    products = data.get("products", [])
    for product in products:
        costing = product.get("costing", {})
        stats = product.get("statistics", {})
        writer.writerow([
            product.get("name", ""),
            product.get("category", ""),
            product.get("sku", ""),
            costing.get("raw_material_cost", 0),
            costing.get("labour_cost_per_unit", 0),
            costing.get("overhead_percentage", 0),
            costing.get("target_margin_percentage", 0),
            stats.get("avg_margin", 0)
        ])


def _generate_order_evaluation_csv(buffer: io.StringIO, data: Dict[str, Any]):
    """Generate order evaluation CSV"""
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    
    # Headers
    writer.writerow(["Order Number", "Customer", "Order Date", "Total Revenue", "Total Cost", "Margin %", "Profitability Score", "Risk Level", "Recommendation"])
    
    # Data
    orders = data.get("orders", [])
    for order in orders:
        financials = order.get("financials", {})
        evaluation = order.get("evaluation", {})
        writer.writerow([
            order.get("order_number", ""),
            order.get("customer_name", ""),
            order.get("order_date", "")[:10],
            financials.get("total_selling_price", 0),
            financials.get("total_cost", 0),
            financials.get("margin_percentage", 0),
            evaluation.get("profitability_score", 0),
            evaluation.get("risk_level", ""),
            "Accept" if evaluation.get("should_accept") else "Review"
        ])


def _generate_margin_analysis_csv(buffer: io.StringIO, data: Dict[str, Any]):
    """Generate margin analysis CSV"""
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    
    # Headers
    writer.writerow(["Name", "Total Revenue", "Total Cost", "Margin", "Margin %", "Order Count"])
    
    # Data
    groups = data.get("groups", [])
    for group in groups:
        writer.writerow([
            group.get("name", ""),
            group.get("total_revenue", 0),
            group.get("total_cost", 0),
            group.get("margin", 0),
            group.get("margin_percentage", 0),
            group.get("order_count", 0)
        ])


def _generate_receivables_report_csv(buffer: io.StringIO, data: Dict[str, Any]):
    """Generate receivables report CSV"""
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    
    # Headers
    writer.writerow(["Party Name", "Amount", "Transaction Date", "Due Date", "Days Outstanding", "Overdue", "Aging Bucket"])
    
    # Data
    receivables = data.get("receivables", [])
    for receivable in receivables:
        writer.writerow([
            receivable.get("party_name", ""),
            receivable.get("amount", 0),
            receivable.get("transaction_date", "")[:10],
            receivable.get("due_date", "")[:10] if receivable.get("due_date") else "",
            receivable.get("days_outstanding", 0),
            "Yes" if receivable.get("is_overdue") else "No",
            receivable.get("aging_bucket", "")
        ])
