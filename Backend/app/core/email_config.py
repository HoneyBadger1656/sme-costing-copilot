# backend/app/core/email_config.py

"""
Email service configuration module.

This module provides centralized email configuration management with validation.
Supports SendGrid and AWS SES providers.

Requirements: 13.1-13.3, 27.1, 27.2, 27.7
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.utils.validation import validate_email, ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EmailConfig:
    """Email service configuration"""
    provider: str
    api_key: str
    from_address: str
    from_name: str
    rate_limit_per_hour: int
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate email configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate provider
        if self.provider not in ["sendgrid", "ses"]:
            raise ValueError(
                f"Invalid EMAIL_PROVIDER: {self.provider}. "
                "Must be 'sendgrid' or 'ses'"
            )
        
        # Validate API key
        if not self.api_key:
            raise ValueError("EMAIL_API_KEY is required")
        
        if len(self.api_key) < 10:
            raise ValueError("EMAIL_API_KEY appears to be invalid (too short)")
        
        # Validate from address
        if not self.from_address:
            raise ValueError("EMAIL_FROM_ADDRESS is required")
        
        try:
            validate_email(self.from_address)
        except ValidationError as e:
            raise ValueError(f"Invalid EMAIL_FROM_ADDRESS: {e}")
        
        # Validate from name
        if not self.from_name:
            logger.warning(
                "email_config_no_from_name",
                message="EMAIL_FROM_NAME not set, using default"
            )
        
        # Validate rate limit
        if self.rate_limit_per_hour < 1:
            raise ValueError(
                f"Invalid RATE_LIMIT_EMAILS_PER_HOUR: {self.rate_limit_per_hour}. "
                "Must be at least 1"
            )
        
        if self.rate_limit_per_hour > 10000:
            logger.warning(
                "email_config_high_rate_limit",
                rate_limit=self.rate_limit_per_hour,
                message="Rate limit is very high, consider reducing"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "provider": self.provider,
            "from_address": self.from_address,
            "from_name": self.from_name,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "api_key_set": bool(self.api_key)
        }


def load_email_config() -> Optional[EmailConfig]:
    """
    Load email configuration from environment variables.
    
    Returns:
        EmailConfig if all required variables are set, None otherwise
    
    Raises:
        ValueError: If configuration is invalid
    """
    provider = os.getenv("EMAIL_PROVIDER", "sendgrid")
    api_key = os.getenv("EMAIL_API_KEY", "")
    from_address = os.getenv("EMAIL_FROM_ADDRESS", "")
    from_name = os.getenv("EMAIL_FROM_NAME", "SME Costing Copilot")
    rate_limit = int(os.getenv("RATE_LIMIT_EMAILS_PER_HOUR", "50"))
    
    # Check if email is configured
    if not api_key or not from_address:
        logger.warning(
            "email_not_configured",
            message="Email service not configured. Set EMAIL_API_KEY and EMAIL_FROM_ADDRESS"
        )
        return None
    
    try:
        config = EmailConfig(
            provider=provider,
            api_key=api_key,
            from_address=from_address,
            from_name=from_name,
            rate_limit_per_hour=rate_limit
        )
        
        logger.info(
            "email_config_loaded",
            provider=config.provider,
            from_address=config.from_address,
            rate_limit_per_hour=config.rate_limit_per_hour
        )
        
        return config
        
    except ValueError as e:
        logger.error(
            "email_config_invalid",
            error=str(e),
            message="Email configuration is invalid"
        )
        raise


def validate_email_config_on_startup() -> bool:
    """
    Validate email configuration on application startup.
    
    Returns:
        True if email is configured and valid, False otherwise
    """
    try:
        config = load_email_config()
        if config is None:
            logger.warning(
                "email_startup_not_configured",
                message="Email service is not configured. Email features will be disabled."
            )
            return False
        
        logger.info(
            "email_startup_validated",
            provider=config.provider,
            message="Email service configuration validated successfully"
        )
        return True
        
    except ValueError as e:
        logger.error(
            "email_startup_validation_failed",
            error=str(e),
            message="Email service configuration validation failed"
        )
        return False


# Global email configuration instance
_email_config: Optional[EmailConfig] = None


def get_email_config() -> Optional[EmailConfig]:
    """
    Get the global email configuration instance.
    
    Returns:
        EmailConfig if configured, None otherwise
    """
    global _email_config
    
    if _email_config is None:
        _email_config = load_email_config()
    
    return _email_config


def reset_email_config() -> None:
    """Reset the global email configuration (useful for testing)"""
    global _email_config
    _email_config = None
