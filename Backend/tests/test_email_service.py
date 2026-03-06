# backend/tests/test_email_service.py

"""
Unit tests for email service with security validation.

Tests cover:
- Email validation in send operations
- Configuration validation
- Email injection prevention
"""

import pytest
import os
from unittest.mock import patch

from app.services.email_service import EmailService
from app.utils.validation import ValidationError


class TestEmailServiceConfiguration:
    """Tests for email service configuration"""
    
    def test_email_service_initialization(self):
        """Test email service initializes with environment variables"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            assert service.provider == "sendgrid"
            assert service.api_key == "test_key"
            assert service.from_address == "noreply@example.com"
    
    def test_email_service_validates_from_address(self):
        """Test that invalid from address is rejected"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "invalid-email"
        }):
            with pytest.raises(ValueError, match="Invalid EMAIL_FROM_ADDRESS"):
                EmailService()
    
    def test_email_service_test_configuration(self):
        """Test configuration testing endpoint"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            status = service.test_configuration()
            assert status["configured"] is True
            assert status["provider"] == "sendgrid"
            assert status["from_address_valid"] is True


class TestEmailServiceSendEmail:
    """Tests for email sending with validation"""
    
    def test_send_email_with_valid_recipients(self):
        """Test sending email with valid recipients"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            result = service.send_email(
                recipients=["user@example.com"],
                subject="Test Subject",
                body="Test Body"
            )
            assert result["status"] == "success"
            assert "user@example.com" in result["recipients"]
    
    def test_send_email_validates_recipients(self):
        """Test that invalid recipients are rejected"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            with pytest.raises(ValidationError, match="Invalid email address format"):
                service.send_email(
                    recipients=["invalid-email"],
                    subject="Test",
                    body="Test"
                )
    
    def test_send_email_prevents_injection_in_recipients(self):
        """Test that email injection in recipients is prevented"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            with pytest.raises(ValidationError, match="Invalid characters"):
                service.send_email(
                    recipients=["user@example.com\nBcc: attacker@evil.com"],
                    subject="Test",
                    body="Test"
                )
    
    def test_send_email_rejects_too_many_recipients(self):
        """Test that too many recipients are rejected"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            recipients = [f"user{i}@example.com" for i in range(101)]
            with pytest.raises(ValidationError, match="Too many recipients"):
                service.send_email(
                    recipients=recipients,
                    subject="Test",
                    body="Test"
                )
    
    def test_send_email_requires_configuration(self):
        """Test that email sending requires configuration"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": ""
        }, clear=True):
            # This should not raise during init since we only warn
            service = EmailService()
            service.api_key = None
            service.from_address = None
            
            with pytest.raises(ValueError, match="not configured"):
                service.send_email(
                    recipients=["user@example.com"],
                    subject="Test",
                    body="Test"
                )
    
    def test_send_email_normalizes_recipients(self):
        """Test that recipient emails are normalized (lowercased)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            result = service.send_email(
                recipients=["User@Example.COM"],
                subject="Test",
                body="Test"
            )
            assert "user@example.com" in result["recipients"]


class TestEmailServiceNotifications:
    """Tests for notification sending"""
    
    def test_send_notification_validates_recipients(self):
        """Test that notification recipients are validated"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            with pytest.raises(ValidationError):
                service.send_notification(
                    recipients=["invalid-email"],
                    template_name="test_template",
                    context={}
                )
    
    def test_send_notification_with_valid_recipients(self):
        """Test sending notification with valid recipients"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            result = service.send_notification(
                recipients=["user@example.com"],
                template_name="test_template",
                context={"key": "value"}
            )
            assert result["status"] == "success"


class TestEmailServiceProviders:
    """Tests for different email providers"""
    
    def test_sendgrid_provider(self):
        """Test SendGrid provider"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            result = service.send_email(
                recipients=["user@example.com"],
                subject="Test",
                body="Test"
            )
            assert result["provider"] == "sendgrid"
    
    def test_ses_provider(self):
        """Test AWS SES provider"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "ses",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            service = EmailService()
            result = service.send_email(
                recipients=["user@example.com"],
                subject="Test",
                body="Test"
            )
            assert result["provider"] == "ses"


class TestEmailServiceRateLimiting:
    """Tests for email rate limiting (Requirement 30.3)"""
    
    def test_rate_limiting_enforced(self):
        """Test that rate limiting prevents excessive email sending"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RATE_LIMIT_EMAILS_PER_HOUR": "5"
        }):
            from app.services.email_service import RateLimitExceeded
            service = EmailService()
            recipient = "user@example.com"
            
            # Send 5 emails (should succeed)
            for i in range(5):
                result = service.send_email(
                    recipients=[recipient],
                    subject=f"Test {i}",
                    body="Test"
                )
                assert result["status"] == "success"
            
            # 6th email should be rate limited
            with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
                service.send_email(
                    recipients=[recipient],
                    subject="Test 6",
                    body="Test"
                )
    
    def test_rate_limiting_per_recipient(self):
        """Test that rate limiting is per recipient"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RATE_LIMIT_EMAILS_PER_HOUR": "5"
        }):
            service = EmailService()
            
            # Send 5 emails to first recipient
            for i in range(5):
                service.send_email(
                    recipients=["user1@example.com"],
                    subject=f"Test {i}",
                    body="Test"
                )
            
            # Should still be able to send to different recipient
            result = service.send_email(
                recipients=["user2@example.com"],
                subject="Test",
                body="Test"
            )
            assert result["status"] == "success"
    
    def test_rate_limit_status(self):
        """Test getting rate limit status for a recipient"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RATE_LIMIT_EMAILS_PER_HOUR": "10"
        }):
            service = EmailService()
            recipient = "user@example.com"
            
            # Check initial status
            status = service.get_rate_limit_status(recipient)
            assert status["max_per_hour"] == 10
            assert status["remaining"] == 10
            assert status["can_send"] is True
            
            # Send 3 emails
            for i in range(3):
                service.send_email(
                    recipients=[recipient],
                    subject=f"Test {i}",
                    body="Test"
                )
            
            # Check updated status
            status = service.get_rate_limit_status(recipient)
            assert status["remaining"] == 7
            assert status["can_send"] is True
    
    def test_rate_limit_configuration_from_env(self):
        """Test that rate limit is configured from environment variable"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RATE_LIMIT_EMAILS_PER_HOUR": "100"
        }):
            service = EmailService()
            status = service.test_configuration()
            assert status["rate_limit_per_hour"] == 100
    
    def test_rate_limit_default_value(self):
        """Test that rate limit uses default value when not configured"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }, clear=True):
            service = EmailService()
            status = service.test_configuration()
            assert status["rate_limit_per_hour"] == 50  # Default value
    
    def test_rate_limiting_multiple_recipients(self):
        """Test rate limiting when sending to multiple recipients"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RATE_LIMIT_EMAILS_PER_HOUR": "5"
        }):
            from app.services.email_service import RateLimitExceeded
            service = EmailService()
            
            # Send 5 emails to first recipient
            for i in range(5):
                service.send_email(
                    recipients=["user1@example.com"],
                    subject=f"Test {i}",
                    body="Test"
                )
            
            # Try to send to both recipients (should fail because user1 is rate limited)
            with pytest.raises(RateLimitExceeded, match="user1@example.com"):
                service.send_email(
                    recipients=["user1@example.com", "user2@example.com"],
                    subject="Test",
                    body="Test"
                )

