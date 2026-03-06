# backend/app/core/template_config.py

"""
Email template configuration using Jinja2.

This module sets up the Jinja2 template engine for email rendering.

Requirements: 14.1, 14.2, 14.8
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from datetime import datetime
from typing import Dict, Any

from app.logging_config import get_logger

logger = get_logger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "emails"


def get_jinja_env() -> Environment:
    """
    Get configured Jinja2 environment for email templates.
    
    Returns:
        Configured Jinja2 Environment
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add custom filters
    env.filters['datetime'] = lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ''
    env.filters['date'] = lambda dt: dt.strftime('%Y-%m-%d') if dt else ''
    env.filters['currency'] = lambda amount: f"₹{amount:,.2f}" if amount else '₹0.00'
    
    # Add global variables
    env.globals['year'] = datetime.now().year
    
    return env


def validate_templates() -> Dict[str, bool]:
    """
    Validate that all required email templates exist.
    
    Returns:
        Dictionary mapping template names to existence status
    """
    required_templates = [
        'base.html',
        'base.txt',
        'order_evaluation_complete.html',
        'order_evaluation_complete.txt',
        'scenario_analysis_ready.html',
        'scenario_analysis_ready.txt',
        'sync_status.html',
        'sync_status.txt',
        'low_margin_alert.html',
        'low_margin_alert.txt',
        'overdue_receivables.html',
        'overdue_receivables.txt'
    ]
    
    results = {}
    for template_name in required_templates:
        template_path = TEMPLATE_DIR / template_name
        results[template_name] = template_path.exists()
    
    missing = [name for name, exists in results.items() if not exists]
    if missing:
        logger.warning(
            "email_templates_missing",
            missing_templates=missing,
            message="Some email templates are missing"
        )
    else:
        logger.info(
            "email_templates_validated",
            message="All required email templates found"
        )
    
    return results


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render an email template with the given context.
    
    Args:
        template_name: Name of the template file (e.g., 'order_evaluation_complete.html')
        context: Template context data
    
    Returns:
        Rendered template string
    
    Raises:
        TemplateNotFound: If template doesn't exist
    """
    env = get_jinja_env()
    
    try:
        template = env.get_template(template_name)
        rendered = template.render(**context)
        
        logger.debug(
            "template_rendered",
            template_name=template_name,
            context_keys=list(context.keys())
        )
        
        return rendered
        
    except TemplateNotFound:
        logger.error(
            "template_not_found",
            template_name=template_name,
            template_dir=str(TEMPLATE_DIR)
        )
        raise
    except Exception as e:
        logger.exception(
            "template_render_error",
            template_name=template_name,
            error=str(e)
        )
        raise
