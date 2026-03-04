# backend/app/utils/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from typing import Dict, Any, List
import io

from app.logging_config import get_logger

logger = get_logger(__name__)


def generate_pdf(template_id: str, data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
    """
    Generate PDF report from template and data.
    
    Args:
        template_id: Report template ID
        data: Report data
        options: Generation options
    
    Returns:
        PDF file as bytes
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Add custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Generate content based on template
        if template_id == "financial_statement":
            story = _generate_financial_statement_pdf(data, styles, title_style)
        elif template_id == "costing_analysis":
            story = _generate_costing_analysis_pdf(data, styles, title_style)
        elif template_id == "order_evaluation":
            story = _generate_order_evaluation_pdf(data, styles, title_style)
        elif template_id == "margin_analysis":
            story = _generate_margin_analysis_pdf(data, styles, title_style)
        elif template_id == "receivables_report":
            story = _generate_receivables_report_pdf(data, styles, title_style)
        else:
            raise ValueError(f"Unknown template: {template_id}")
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info("pdf_generated", template_id=template_id, size=len(pdf_bytes))
        return pdf_bytes
        
    except Exception as e:
        logger.error("pdf_generation_error", error=str(e), template_id=template_id)
        raise


def _generate_financial_statement_pdf(data: Dict[str, Any], styles, title_style) -> List:
    """Generate financial statement PDF content"""
    story = []
    
    # Title
    story.append(Paragraph("Financial Statement Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Period info
    period = data.get("period", {})
    story.append(Paragraph(f"Period: {period.get('start', '')} to {period.get('end', '')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Statements summary
    statements = data.get("statements", [])
    if statements:
        table_data = [["Type", "Period Start", "Period End", "Gross Margin", "Net Margin"]]
        for stmt in statements:
            metrics = stmt.get("metrics", {})
            table_data.append([
                stmt.get("statement_type", ""),
                stmt.get("period_start", "")[:10],
                stmt.get("period_end", "")[:10],
                f"{metrics.get('gross_margin', 0):.2f}%",
                f"{metrics.get('net_margin', 0):.2f}%"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    
    return story


def _generate_costing_analysis_pdf(data: Dict[str, Any], styles, title_style) -> List:
    """Generate costing analysis PDF content"""
    story = []
    
    story.append(Paragraph("Costing Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    period = data.get("period", {})
    story.append(Paragraph(f"Period: {period.get('start', '')} to {period.get('end', '')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Products table
    products = data.get("products", [])
    if products:
        table_data = [["Product", "Category", "Raw Material", "Labour", "Overhead %", "Avg Margin"]]
        for product in products[:20]:  # Limit to 20 products
            costing = product.get("costing", {})
            stats = product.get("statistics", {})
            table_data.append([
                product.get("name", "")[:30],
                product.get("category", "")[:20],
                f"₹{costing.get('raw_material_cost', 0):.2f}",
                f"₹{costing.get('labour_cost_per_unit', 0):.2f}",
                f"{costing.get('overhead_percentage', 0):.1f}%",
                f"{stats.get('avg_margin', 0):.2f}%"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    
    return story


def _generate_order_evaluation_pdf(data: Dict[str, Any], styles, title_style) -> List:
    """Generate order evaluation PDF content"""
    story = []
    
    story.append(Paragraph("Order Evaluation Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    summary = data.get("summary", {})
    story.append(Paragraph(f"Total Orders: {summary.get('total_orders', 0)}", styles['Normal']))
    story.append(Paragraph(f"Total Revenue: ₹{summary.get('total_revenue', 0):,.2f}", styles['Normal']))
    story.append(Paragraph(f"Average Margin: {summary.get('avg_margin_percentage', 0):.2f}%", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Orders table
    orders = data.get("orders", [])
    if orders:
        table_data = [["Order #", "Customer", "Revenue", "Margin %", "Score", "Risk"]]
        for order in orders[:15]:  # Limit to 15 orders
            financials = order.get("financials", {})
            evaluation = order.get("evaluation", {})
            table_data.append([
                order.get("order_number", "")[:15],
                order.get("customer_name", "")[:20],
                f"₹{financials.get('total_selling_price', 0):,.0f}",
                f"{financials.get('margin_percentage', 0):.1f}%",
                f"{evaluation.get('profitability_score', 0):.0f}",
                evaluation.get('risk_level', 'N/A')
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    
    return story


def _generate_margin_analysis_pdf(data: Dict[str, Any], styles, title_style) -> List:
    """Generate margin analysis PDF content"""
    story = []
    
    story.append(Paragraph("Margin Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"Grouped by: {data.get('group_by', 'product').title()}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Margin groups table
    groups = data.get("groups", [])
    if groups:
        table_data = [["Name", "Revenue", "Cost", "Margin", "Margin %", "Orders"]]
        for group in groups[:20]:
            table_data.append([
                group.get("name", "")[:30],
                f"₹{group.get('total_revenue', 0):,.0f}",
                f"₹{group.get('total_cost', 0):,.0f}",
                f"₹{group.get('margin', 0):,.0f}",
                f"{group.get('margin_percentage', 0):.2f}%",
                str(group.get('order_count', 0))
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    
    return story


def _generate_receivables_report_pdf(data: Dict[str, Any], styles, title_style) -> List:
    """Generate receivables report PDF content"""
    story = []
    
    story.append(Paragraph("Receivables Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    summary = data.get("summary", {})
    story.append(Paragraph(f"As of: {data.get('as_of_date', '')}", styles['Normal']))
    story.append(Paragraph(f"Total Receivables: ₹{summary.get('total_amount', 0):,.2f}", styles['Normal']))
    story.append(Paragraph(f"Count: {summary.get('total_count', 0)}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Aging summary
    aging_summary = data.get("aging_summary", {})
    if aging_summary:
        table_data = [["Aging Bucket", "Count", "Amount"]]
        for bucket, info in aging_summary.items():
            table_data.append([
                bucket,
                str(info.get('count', 0)),
                f"₹{info.get('total_amount', 0):,.2f}"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    
    return story
