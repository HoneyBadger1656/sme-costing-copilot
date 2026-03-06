# backend/app/services/report_service.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
import os
import uuid
from pathlib import Path

from app.services.report_templates import get_template, validate_template_parameters, is_format_supported
from app.services.report_data_service import (
    get_financial_statement_data,
    get_costing_analysis_data,
    get_order_evaluation_data,
    get_margin_analysis_data,
    get_receivables_report_data
)
from app.utils.pdf_generator import generate_pdf
from app.utils.excel_generator import generate_excel
from app.utils.csv_generator import generate_csv
from app.utils.validation import sanitize_report_parameters, validate_file_path, ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class ReportService:
    """Service for report generation and management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_path = Path(os.getenv("REPORT_STORAGE_PATH", "/tmp/reports"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        template_id: str,
        format: str,
        parameters: Dict[str, Any],
        tenant_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Generate a report synchronously.
        
        Args:
            template_id: Report template ID
            format: Output format (pdf, excel, csv)
            parameters: Report parameters
            tenant_id: Tenant ID
            user_id: User ID requesting the report
        
        Returns:
            Report metadata including file path and task ID
        """
        try:
            # Sanitize report parameters to prevent injection attacks (Requirement 30.1)
            try:
                sanitized_parameters = sanitize_report_parameters(parameters)
            except ValidationError as e:
                logger.warning(
                    "report_parameter_validation_failed",
                    error=str(e),
                    tenant_id=tenant_id,
                    user_id=user_id
                )
                raise ValueError(f"Invalid report parameters: {e}")
            
            # Validate template and format
            template = get_template(template_id)
            if not is_format_supported(template_id, format):
                raise ValueError(f"Format '{format}' not supported for template '{template_id}'")
            
            # Validate parameters
            validate_template_parameters(template_id, sanitized_parameters)
            
            # Fetch data based on template
            data = self._fetch_report_data(template_id, sanitized_parameters, tenant_id)
            
            # Generate report file
            report_bytes = self._generate_report_file(template_id, format, data, sanitized_parameters)
            
            # Save to storage with path validation (Requirement 30.2)
            task_id = str(uuid.uuid4())
            file_extension = format if format != "excel" else "xlsx"
            file_name = f"{template_id}_{task_id}.{file_extension}"
            
            # Validate file path to prevent directory traversal
            try:
                file_path = validate_file_path(file_name, str(self.storage_path))
            except ValidationError as e:
                logger.error(
                    "report_file_path_validation_failed",
                    error=str(e),
                    file_name=file_name,
                    tenant_id=tenant_id
                )
                raise ValueError(f"Invalid file path: {e}")
            
            with open(file_path, 'wb') as f:
                f.write(report_bytes)
            
            logger.info(
                "report_generated",
                template_id=template_id,
                format=format,
                tenant_id=tenant_id,
                user_id=user_id,
                task_id=task_id,
                file_size=len(report_bytes)
                # correlation_id automatically included via structlog context
            )
            
            return {
                "task_id": task_id,
                "template_id": template_id,
                "format": format,
                "file_path": str(file_path),
                "file_name": file_name,
                "file_size": len(report_bytes),
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
        except Exception as e:
            logger.error(
                "report_generation_failed",
                error=str(e),
                template_id=template_id,
                format=format,
                tenant_id=tenant_id
                # correlation_id automatically included via structlog context
                # Requirement 29.6: Include correlation IDs in logs to trace requests across components
            )
            raise
    
    def _fetch_report_data(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        tenant_id: int
    ) -> Dict[str, Any]:
        """Fetch data for report based on template"""
        
        if template_id == "financial_statement":
            return get_financial_statement_data(
                self.db,
                tenant_id,
                self._parse_date(parameters.get("period_start")),
                self._parse_date(parameters.get("period_end")),
                parameters.get("statement_type")
            )
        
        elif template_id == "costing_analysis":
            date_range = parameters.get("date_range", {})
            return get_costing_analysis_data(
                self.db,
                tenant_id,
                self._parse_date(date_range.get("start")),
                self._parse_date(date_range.get("end")),
                parameters.get("product_ids")
            )
        
        elif template_id == "order_evaluation":
            date_range = parameters.get("date_range", {})
            return get_order_evaluation_data(
                self.db,
                tenant_id,
                self._parse_date(date_range.get("start")),
                self._parse_date(date_range.get("end")),
                parameters.get("status")
            )
        
        elif template_id == "margin_analysis":
            date_range = parameters.get("date_range", {})
            return get_margin_analysis_data(
                self.db,
                tenant_id,
                self._parse_date(date_range.get("start")),
                self._parse_date(date_range.get("end")),
                parameters.get("group_by", "product")
            )
        
        elif template_id == "receivables_report":
            return get_receivables_report_data(
                self.db,
                tenant_id,
                self._parse_date(parameters.get("as_of_date")),
                parameters.get("aging_buckets", [30, 60, 90])
            )
        
        else:
            raise ValueError(f"Unknown template: {template_id}")
    
    def _generate_report_file(
        self,
        template_id: str,
        format: str,
        data: Dict[str, Any],
        options: Dict[str, Any]
    ) -> bytes:
        """Generate report file in specified format"""
        
        if format == "pdf":
            return generate_pdf(template_id, data, options)
        elif format == "excel":
            return generate_excel(template_id, data, options)
        elif format == "csv":
            return generate_csv(template_id, data, options)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_report_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get report generation status.
        
        Args:
            task_id: Task ID
        
        Returns:
            Status information
        """
        # Check if report file exists
        report_files = list(self.storage_path.glob(f"*_{task_id}.*"))
        
        if not report_files:
            return {
                "task_id": task_id,
                "status": "not_found"
            }
        
        file_path = report_files[0]
        file_stat = file_path.stat()
        created_at = datetime.fromtimestamp(file_stat.st_ctime)
        expires_at = created_at + timedelta(hours=24)
        
        # Check if expired
        if datetime.utcnow() > expires_at:
            return {
                "task_id": task_id,
                "status": "expired",
                "created_at": created_at.isoformat(),
                "expires_at": expires_at.isoformat()
            }
        
        return {
            "task_id": task_id,
            "status": "completed",
            "file_name": file_path.name,
            "file_size": file_stat.st_size,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat()
        }
    
    def get_report_download_url(self, task_id: str) -> Optional[str]:
        """
        Get report download URL with 24-hour expiry.
        
        Args:
            task_id: Task ID
        
        Returns:
            Download URL or None if not found/expired
        """
        status = self.get_report_status(task_id)
        
        if status["status"] != "completed":
            return None
        
        # In production, this would generate a signed URL
        # For now, return a simple path
        return f"/api/reports/download/{task_id}"
    
    def get_report_file_path(self, task_id: str) -> Optional[Path]:
        """
        Get report file path.
        
        Args:
            task_id: Task ID
        
        Returns:
            File path or None if not found
        """
        report_files = list(self.storage_path.glob(f"*_{task_id}.*"))
        
        if not report_files:
            return None
        
        return report_files[0]
    
    def _parse_date(self, date_str: Any) -> date:
        """Parse date string to date object"""
        if isinstance(date_str, date):
            return date_str
        if isinstance(date_str, datetime):
            return date_str.date()
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        raise ValueError(f"Invalid date format: {date_str}")
