# backend/app/services/email_service.py

"""
Email notification service with secure email validation.

This service handles sending emails with proper validation to prevent
email injection attacks and other security vulnerabilities.
Includes rate limiting to prevent resource exhaustion (Requirement 30.3).
"""

from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

from app.core.email_config import get_email_config, EmailConfig
from app.core.template_config import render_template
from app.utils.validation import validate_email, validate_email_list, ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class EmailRateLimiter:
    """
    Rate limiter for email sending to prevent resource exhaustion.
    
    Implements a sliding window rate limiter per recipient.
    """
    
    def __init__(self, max_emails_per_hour: int):
        self.max_emails_per_hour = max_emails_per_hour
        self.email_timestamps: Dict[str, List[datetime]] = defaultdict(list)
        self.lock = Lock()
    
    def check_rate_limit(self, recipient: str) -> bool:
        """
        Check if sending to this recipient would exceed rate limit.
        
        Args:
            recipient: Email address to check
        
        Returns:
            True if within rate limit, False otherwise
        """
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=1)
            
            # Clean old timestamps
            self.email_timestamps[recipient] = [
                ts for ts in self.email_timestamps[recipient]
                if ts > cutoff
            ]
            
            # Check if limit exceeded
            return len(self.email_timestamps[recipient]) < self.max_emails_per_hour
    
    def record_email(self, recipient: str) -> None:
        """
        Record an email send for rate limiting.
        
        Args:
            recipient: Email address that was sent to
        """
        with self.lock:
            self.email_timestamps[recipient].append(datetime.utcnow())
    
    def get_remaining_quota(self, recipient: str) -> int:
        """
        Get remaining email quota for a recipient.
        
        Args:
            recipient: Email address to check
        
        Returns:
            Number of emails that can still be sent within the hour
        """
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=1)
            
            # Clean old timestamps
            self.email_timestamps[recipient] = [
                ts for ts in self.email_timestamps[recipient]
                if ts > cutoff
            ]
            
            return max(0, self.max_emails_per_hour - len(self.email_timestamps[recipient]))


class EmailService:
    """Service for sending email notifications with security validation and rate limiting"""
    
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "sendgrid")
        self.api_key = os.getenv("EMAIL_API_KEY")
        self.from_address = os.getenv("EMAIL_FROM_ADDRESS")
        self.max_retries = 3
        
        # Rate limiting configuration (Requirement 30.3)
        rate_limit_per_hour = int(os.getenv("RATE_LIMIT_EMAILS_PER_HOUR", "50"))
        self.rate_limiter = EmailRateLimiter(max_emails_per_hour=rate_limit_per_hour)
        
        # Validate configuration on initialization
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """
        Validate email service configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key:
            logger.warning("email_service_no_api_key", message="EMAIL_API_KEY not configured")
        
        if not self.from_address:
            logger.warning("email_service_no_from_address", message="EMAIL_FROM_ADDRESS not configured")
        elif self.from_address:
            try:
                # Validate from address (Requirement 30.4)
                validate_email(self.from_address)
            except ValidationError as e:
                raise ValueError(f"Invalid EMAIL_FROM_ADDRESS: {e}")
        
        if self.provider not in ["sendgrid", "ses"]:
            logger.warning(
                "email_service_unknown_provider",
                provider=self.provider,
                message="Unknown email provider, defaulting to sendgrid"
            )
    
    def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email with validated recipients and rate limiting.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            attachments: Optional list of attachments
        
        Returns:
            Result dictionary with status and message
        
        Raises:
            ValidationError: If email addresses are invalid
            ValueError: If email service is not configured
            RateLimitExceeded: If rate limit is exceeded for any recipient
        """
        # Validate recipients to prevent email injection (Requirement 30.4)
        try:
            validated_recipients = validate_email_list(recipients, max_recipients=100)
        except ValidationError as e:
            logger.error(
                "email_send_validation_failed",
                error=str(e),
                recipients_count=len(recipients) if isinstance(recipients, list) else 0
            )
            raise
        
        # Check rate limits for all recipients (Requirement 30.3)
        rate_limited_recipients = []
        for recipient in validated_recipients:
            if not self.rate_limiter.check_rate_limit(recipient):
                rate_limited_recipients.append(recipient)
        
        if rate_limited_recipients:
            logger.warning(
                "email_rate_limit_exceeded",
                rate_limited_recipients=rate_limited_recipients,
                subject=subject[:100]
            )
            raise RateLimitExceeded(
                f"Rate limit exceeded for recipients: {', '.join(rate_limited_recipients)}"
            )
        
        # Check configuration
        if not self.api_key or not self.from_address:
            logger.error(
                "email_send_not_configured",
                message="Email service not properly configured"
            )
            raise ValueError("Email service not configured")
        
        # Log email send attempt
        logger.info(
            "email_send_attempt",
            recipients_count=len(validated_recipients),
            subject=subject[:100],  # Truncate for logging
            provider=self.provider
        )
        
        try:
            # In a real implementation, this would call the actual email provider
            # For now, we'll simulate success
            result = self._send_via_provider(
                validated_recipients,
                subject,
                body,
                html_body,
                attachments
            )
            
            # Record successful sends for rate limiting
            for recipient in validated_recipients:
                self.rate_limiter.record_email(recipient)
            
            logger.info(
                "email_sent_successfully",
                recipients_count=len(validated_recipients),
                subject=subject[:100]
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "email_send_failed",
                error=str(e),
                recipients_count=len(validated_recipients),
                subject=subject[:100]
            )
            raise
    
    def _send_via_provider(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Send email via configured provider.
        
        Args:
            recipients: Validated recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            attachments: Optional attachments
        
        Returns:
            Result dictionary
        """
        # This is a placeholder implementation
        # In production, this would integrate with SendGrid, AWS SES, etc.
        
        if self.provider == "sendgrid":
            return self._send_via_sendgrid(recipients, subject, body, html_body, attachments)
        elif self.provider == "ses":
            return self._send_via_ses(recipients, subject, body, html_body, attachments)
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")
    
    def _send_via_sendgrid(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send email via SendGrid (placeholder implementation)"""
        # TODO: Implement actual SendGrid integration
        logger.info("sendgrid_email_placeholder", recipients_count=len(recipients))
        return {
            "status": "success",
            "provider": "sendgrid",
            "message_id": f"sendgrid_{datetime.utcnow().timestamp()}",
            "recipients": recipients
        }
    
    def _send_via_ses(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send email via AWS SES (placeholder implementation)"""
        # TODO: Implement actual AWS SES integration
        logger.info("ses_email_placeholder", recipients_count=len(recipients))
        return {
            "status": "success",
            "provider": "ses",
            "message_id": f"ses_{datetime.utcnow().timestamp()}",
            "recipients": recipients
        }
    
    def send_notification(
        self,
        recipients: List[str],
        template_name: str,
        context: Dict[str, Any],
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a notification email using a template.
        
        Args:
            recipients: List of recipient email addresses
            template_name: Name of the email template (without extension)
            context: Template context data
            subject: Optional custom subject line (defaults to template-based)
        
        Returns:
            Result dictionary
        
        Raises:
            ValidationError: If email addresses are invalid
            TemplateNotFound: If template doesn't exist
        """
        # Validate recipients (Requirement 30.4)
        try:
            validated_recipients = validate_email_list(recipients, max_recipients=100)
        except ValidationError as e:
            logger.error(
                "notification_validation_failed",
                error=str(e),
                template_name=template_name
            )
            raise
        
        # Render HTML and plain text templates
        try:
            html_body = render_template(f"{template_name}.html", context)
            text_body = render_template(f"{template_name}.txt", context)
            
            # Use custom subject or derive from template name
            if subject is None:
                subject = self._get_default_subject(template_name)
            
            logger.info(
                "notification_template_rendered",
                template_name=template_name,
                recipients_count=len(validated_recipients)
            )
            
        except Exception as e:
            logger.error(
                "notification_template_render_failed",
                error=str(e),
                template_name=template_name
            )
            raise
        
        return self.send_email(
            recipients=validated_recipients,
            subject=subject,
            body=text_body,
            html_body=html_body
        )
    
    def _get_default_subject(self, template_name: str) -> str:
        """
        Get default subject line for a template.
        
        Args:
            template_name: Template name
        
        Returns:
            Default subject line
        """
        subject_map = {
            "order_evaluation_complete": "Order Evaluation Complete",
            "scenario_analysis_ready": "Scenario Analysis Ready",
            "sync_status": "Integration Sync Status",
            "low_margin_alert": "⚠️ Low Margin Alert",
            "overdue_receivables": "⚠️ Overdue Receivables Alert"
        }
        
        return subject_map.get(template_name, f"Notification: {template_name}")
    
    def test_configuration(self) -> Dict[str, Any]:
        """
        Test email service configuration.
        
        Returns:
            Configuration status dictionary
        """
        status = {
            "configured": bool(self.api_key and self.from_address),
            "provider": self.provider,
            "from_address": self.from_address,
            "api_key_set": bool(self.api_key),
            "rate_limit_per_hour": self.rate_limiter.max_emails_per_hour
        }
        
        # Validate from address
        if self.from_address:
            try:
                validate_email(self.from_address)
                status["from_address_valid"] = True
            except ValidationError as e:
                status["from_address_valid"] = False
                status["from_address_error"] = str(e)
        
        return status
    
    def get_rate_limit_status(self, recipient: str) -> Dict[str, Any]:
        """
        Get rate limit status for a recipient.
        
        Args:
            recipient: Email address to check
        
        Returns:
            Dictionary with rate limit information
        """
        remaining = self.rate_limiter.get_remaining_quota(recipient)
        return {
            "recipient": recipient,
            "max_per_hour": self.rate_limiter.max_emails_per_hour,
            "remaining": remaining,
            "can_send": remaining > 0
        }
