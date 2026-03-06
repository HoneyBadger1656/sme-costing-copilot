"""
Unit tests for email configuration module.

Tests cover:
- Email configuration initialization from environment variables
- Configuration validation (Requirements 13.1-13.3, 27.1, 27.2, 27.7)
- Support for SendGrid and AWS SES providers
- Validation error handling
- Configuration startup validation
"""

import pytest
import os
from unittest.mock import patch

from app.core.email_config import (
    EmailConfig,
    EmailProvider,
    get_email_config,
    validate_email_config
)


class TestEmailConfigInitialization:
    """Tests for email configuration initialization"""
    
    def test_email_config_loads_from_environment(self):
        """Test that email config loads from environment variables (Requirement 13.2)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "EMAIL_FROM_NAME": "Test App",
            "EMAIL_MAX_RETRIES": "5",
            "RATE_LIMIT_EMAILS_PER_HOUR": "100"
        }):
            config = EmailConfig()
            assert config.provider == "sendgrid"
            assert config.api_key == "test_api_key_12345"
            assert config.from_address == "noreply@example.com"
            assert config.from_name == "Test App"
            assert config.max_retries == 5
            assert config.rate_limit_per_hour == 100
    
    def test_email_config_uses_defaults(self):
        """Test that email config uses default values when not specified (Requirement 27.6)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }, clear=True):
            config = EmailConfig()
            assert config.from_name == "SME Costing Copilot"
            assert config.max_retries == 3
            assert config.rate_limit_per_hour == 50
    
    def test_email_config_supports_sendgrid_provider(self):
        """Test SendGrid provider support (Requirement 13.1)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            assert config.provider == EmailProvider.SENDGRID.value
    
    def test_email_config_supports_ses_provider(self):
        """Test AWS SES provider support (Requirement 13.1)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "ses",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            assert config.provider == EmailProvider.SES.value


class TestEmailConfigValidation:
    """Tests for email configuration validation"""
    
    def test_validate_succeeds_with_valid_config(self):
        """Test validation succeeds with valid configuration (Requirement 13.3)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            assert config.validate() is True
            assert config._validated is True
            assert len(config.get_validation_errors()) == 0
    
    def test_validate_fails_without_provider(self):
        """Test validation fails when provider is missing (Requirement 13.2, 27.5)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }, clear=True):
            config = EmailConfig()
            with pytest.raises(ValueError, match="EMAIL_PROVIDER is not set"):
                config.validate()
    
    def test_validate_fails_with_unsupported_provider(self):
        """Test validation fails with unsupported provider (Requirement 13.1)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "mailgun",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            with pytest.raises(ValueError, match="not supported"):
                config.validate()
    
    def test_validate_fails_without_api_key(self):
        """Test validation fails when API key is missing (Requirement 13.2, 27.5)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }, clear=True):
            config = EmailConfig()
            with pytest.raises(ValueError, match="EMAIL_API_KEY is not set"):
                config.validate()
    
    def test_validate_fails_with_short_api_key(self):
        """Test validation fails when API key is too short"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "short",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            with pytest.raises(ValueError, match="too short"):
                config.validate()
    
    def test_validate_fails_without_from_address(self):
        """Test validation fails when from address is missing (Requirement 13.2, 27.5)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": ""
        }, clear=True):
            config = EmailConfig()
            with pytest.raises(ValueError, match="EMAIL_FROM_ADDRESS is not set"):
                config.validate()
    
    def test_validate_fails_with_invalid_from_address(self):
        """Test validation fails with invalid from address (Requirement 30.4)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "invalid-email"
        }):
            config = EmailConfig()
            with pytest.raises(ValueError, match="EMAIL_FROM_ADDRESS is invalid"):
                config.validate()
    
    def test_validate_fails_with_invalid_max_retries(self):
        """Test validation fails with invalid max retries"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "EMAIL_MAX_RETRIES": "15"
        }):
            config = EmailConfig()
            with pytest.raises(ValueError, match="EMAIL_MAX_RETRIES must be between 0 and 10"):
                config.validate()
    
    def test_validate_fails_with_invalid_rate_limit(self):
        """Test validation fails with invalid rate limit"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RATE_LIMIT_EMAILS_PER_HOUR": "0"
        }):
            config = EmailConfig()
            with pytest.raises(ValueError, match="RATE_LIMIT_EMAILS_PER_HOUR must be at least 1"):
                config.validate()
    
    def test_validate_collects_multiple_errors(self):
        """Test validation collects all errors"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": ""
        }, clear=True):
            config = EmailConfig()
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            
            errors = config.get_validation_errors()
            assert len(errors) >= 3
            assert any("EMAIL_PROVIDER" in err for err in errors)
            assert any("EMAIL_API_KEY" in err for err in errors)
            assert any("EMAIL_FROM_ADDRESS" in err for err in errors)


class TestEmailConfigMethods:
    """Tests for email configuration methods"""
    
    def test_is_configured_returns_true_when_configured(self):
        """Test is_configured returns True when all required config is present"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_key",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            assert config.is_configured() is True
    
    def test_is_configured_returns_false_when_missing_config(self):
        """Test is_configured returns False when config is missing"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": ""
        }, clear=True):
            config = EmailConfig()
            assert config.is_configured() is False
    
    def test_get_config_dict_returns_config_with_masked_key(self):
        """Test get_config_dict returns configuration with masked API key"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "EMAIL_FROM_NAME": "Test App",
            "EMAIL_MAX_RETRIES": "5",
            "RATE_LIMIT_EMAILS_PER_HOUR": "100"
        }):
            config = EmailConfig()
            config_dict = config.get_config_dict()
            
            assert config_dict["provider"] == "sendgrid"
            assert config_dict["from_address"] == "noreply@example.com"
            assert config_dict["from_name"] == "Test App"
            assert config_dict["max_retries"] == 5
            assert config_dict["rate_limit_per_hour"] == 100
            assert config_dict["api_key_set"] is True
            assert config_dict["api_key_length"] == 19
            assert config_dict["configured"] is True
            # API key itself should not be in the dict
            assert "api_key" not in config_dict or config_dict.get("api_key") != "test_api_key_12345"
    
    def test_get_validation_errors_returns_empty_list_when_valid(self):
        """Test get_validation_errors returns empty list when valid"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            config = EmailConfig()
            config.validate()
            assert config.get_validation_errors() == []
    
    def test_get_validation_errors_returns_errors_when_invalid(self):
        """Test get_validation_errors returns errors when invalid"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": ""
        }, clear=True):
            config = EmailConfig()
            try:
                config.validate()
            except ValueError:
                pass
            
            errors = config.get_validation_errors()
            assert len(errors) > 0


class TestEmailConfigGlobalInstance:
    """Tests for global email configuration instance"""
    
    def test_get_email_config_returns_singleton(self):
        """Test get_email_config returns the global singleton instance"""
        config1 = get_email_config()
        config2 = get_email_config()
        assert config1 is config2
    
    def test_validate_email_config_validates_global_instance(self):
        """Test validate_email_config validates the global instance (Requirement 13.3)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }):
            # Reset the global instance
            from app.core import email_config as email_config_module
            email_config_module.email_config = EmailConfig()
            
            result = validate_email_config()
            assert result is True
    
    def test_validate_email_config_raises_on_invalid_config(self):
        """Test validate_email_config raises ValueError on invalid config (Requirement 27.5)"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": ""
        }, clear=True):
            # Reset the global instance
            from app.core import email_config as email_config_module
            email_config_module.email_config = EmailConfig()
            
            with pytest.raises(ValueError, match="Email configuration validation failed"):
                validate_email_config()


class TestEmailConfigProviderEnum:
    """Tests for EmailProvider enum"""
    
    def test_email_provider_enum_has_sendgrid(self):
        """Test EmailProvider enum includes SendGrid"""
        assert EmailProvider.SENDGRID.value == "sendgrid"
    
    def test_email_provider_enum_has_ses(self):
        """Test EmailProvider enum includes AWS SES"""
        assert EmailProvider.SES.value == "ses"
    
    def test_email_provider_enum_values(self):
        """Test EmailProvider enum has exactly the supported providers"""
        providers = [p.value for p in EmailProvider]
        assert "sendgrid" in providers
        assert "ses" in providers
        assert len(providers) == 2


class TestEmailConfigEdgeCases:
    """Tests for edge cases in email configuration"""
    
    def test_validate_with_whitespace_in_values(self):
        """Test validation handles whitespace in configuration values"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": " sendgrid ",
            "EMAIL_API_KEY": " test_api_key_12345 ",
            "EMAIL_FROM_ADDRESS": " noreply@example.com "
        }):
            config = EmailConfig()
            # Values should be trimmed or handled appropriately
            # Current implementation doesn't trim, so this tests actual behavior
            assert config.provider == " sendgrid "
    
    def test_validate_with_zero_max_retries(self):
        """Test validation allows zero max retries"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "EMAIL_MAX_RETRIES": "0"
        }):
            config = EmailConfig()
            assert config.validate() is True
            assert config.max_retries == 0
    
    def test_validate_with_negative_max_retries(self):
        """Test validation rejects negative max retries"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "test_api_key_12345",
            "EMAIL_FROM_ADDRESS": "noreply@example.com",
            "EMAIL_MAX_RETRIES": "-1"
        }):
            config = EmailConfig()
            with pytest.raises(ValueError, match="EMAIL_MAX_RETRIES must be between 0 and 10"):
                config.validate()
    
    def test_config_dict_with_no_api_key(self):
        """Test get_config_dict handles missing API key"""
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_API_KEY": "",
            "EMAIL_FROM_ADDRESS": "noreply@example.com"
        }, clear=True):
            config = EmailConfig()
            config_dict = config.get_config_dict()
            assert config_dict["api_key_set"] is False
            assert config_dict["api_key_length"] == 0
