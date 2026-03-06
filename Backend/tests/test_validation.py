# backend/tests/test_validation.py

"""
Unit tests for input validation and sanitization utilities.

Tests cover:
- String sanitization
- Report parameter sanitization
- File path validation (directory traversal prevention)
- Email validation (injection prevention)
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.utils.validation import (
    sanitize_string,
    sanitize_report_parameters,
    sanitize_list,
    validate_file_path,
    validate_email,
    validate_email_list,
    sanitize_sql_like_pattern,
    validate_integer,
    validate_date_string,
    ValidationError
)


class TestSanitizeString:
    """Tests for string sanitization"""
    
    def test_sanitize_valid_string(self):
        """Test sanitizing a valid string"""
        result = sanitize_string("Hello World")
        assert result == "Hello World"
    
    def test_sanitize_string_with_whitespace(self):
        """Test sanitizing string with leading/trailing whitespace"""
        result = sanitize_string("  Hello World  ")
        assert result == "Hello World"
    
    def test_sanitize_string_removes_null_bytes(self):
        """Test that null bytes are rejected"""
        with pytest.raises(ValidationError, match="Null bytes not allowed"):
            sanitize_string("Hello\x00World")
    
    def test_sanitize_string_removes_control_characters(self):
        """Test that control characters are removed"""
        result = sanitize_string("Hello\x01\x02World")
        assert result == "HelloWorld"
    
    def test_sanitize_string_rejects_newlines_by_default(self):
        """Test that newlines are rejected by default"""
        with pytest.raises(ValidationError, match="Newline characters not allowed"):
            sanitize_string("Hello\nWorld")
    
    def test_sanitize_string_allows_newlines_when_enabled(self):
        """Test that newlines are allowed when enabled"""
        result = sanitize_string("Hello\nWorld", allow_newlines=True)
        assert result == "Hello\nWorld"
    
    def test_sanitize_string_exceeds_max_length(self):
        """Test that strings exceeding max length are rejected"""
        long_string = "a" * 1001
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitize_string(long_string, max_length=1000)
    
    def test_sanitize_string_non_string_input(self):
        """Test that non-string input is rejected"""
        with pytest.raises(ValidationError, match="Expected string"):
            sanitize_string(123)


class TestSanitizeReportParameters:
    """Tests for report parameter sanitization"""
    
    def test_sanitize_valid_parameters(self):
        """Test sanitizing valid parameters"""
        params = {
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "product_id": 123
        }
        result = sanitize_report_parameters(params)
        assert result["period_start"] == "2024-01-01"
        assert result["period_end"] == "2024-12-31"
        assert result["product_id"] == 123
    
    def test_sanitize_parameters_with_nested_dict(self):
        """Test sanitizing parameters with nested dictionaries"""
        params = {
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            }
        }
        result = sanitize_report_parameters(params)
        assert result["date_range"]["start"] == "2024-01-01"
        assert result["date_range"]["end"] == "2024-12-31"
    
    def test_sanitize_parameters_with_list(self):
        """Test sanitizing parameters with lists"""
        params = {
            "product_ids": [1, 2, 3]
        }
        result = sanitize_report_parameters(params)
        assert result["product_ids"] == [1, 2, 3]
    
    def test_sanitize_parameters_rejects_invalid_key_format(self):
        """Test that invalid key formats are rejected"""
        params = {
            "invalid-key!": "value"
        }
        with pytest.raises(ValidationError, match="Invalid parameter key format"):
            sanitize_report_parameters(params)
    
    def test_sanitize_parameters_rejects_unsupported_type(self):
        """Test that unsupported types are rejected"""
        params = {
            "invalid": object()
        }
        with pytest.raises(ValidationError, match="Unsupported parameter type"):
            sanitize_report_parameters(params)
    
    def test_sanitize_parameters_non_dict_input(self):
        """Test that non-dict input is rejected"""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            sanitize_report_parameters("not a dict")


class TestValidateFilePath:
    """Tests for file path validation (directory traversal prevention)"""
    
    def test_validate_safe_file_path(self):
        """Test validating a safe file path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_file_path("report.pdf", tmpdir)
            assert result == Path(tmpdir).resolve() / "report.pdf"
    
    def test_validate_file_path_with_subdirectory(self):
        """Test validating file path with subdirectory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_file_path("reports/report.pdf", tmpdir)
            assert result == Path(tmpdir).resolve() / "reports" / "report.pdf"
    
    def test_validate_file_path_rejects_parent_directory_traversal(self):
        """Test that parent directory traversal is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="Suspicious pattern"):
                validate_file_path("../etc/passwd", tmpdir)
    
    def test_validate_file_path_rejects_absolute_path_traversal(self):
        """Test that absolute path traversal is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="directory traversal"):
                validate_file_path("/etc/passwd", tmpdir)
    
    def test_validate_file_path_rejects_suspicious_patterns(self):
        """Test that suspicious patterns are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test various suspicious patterns
            suspicious = ["file;rm -rf", "file|cat", "file`whoami`", "file$HOME"]
            for pattern in suspicious:
                with pytest.raises(ValidationError, match="Suspicious pattern"):
                    validate_file_path(pattern, tmpdir)
    
    def test_validate_file_path_rejects_null_bytes(self):
        """Test that null bytes are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="Null bytes not allowed"):
                validate_file_path("file\x00.pdf", tmpdir)
    
    def test_validate_file_path_non_string_input(self):
        """Test that non-string input is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="must be a string"):
                validate_file_path(123, tmpdir)


class TestValidateEmail:
    """Tests for email validation (injection prevention)"""
    
    def test_validate_valid_email(self):
        """Test validating a valid email"""
        result = validate_email("user@example.com")
        assert result == "user@example.com"
    
    def test_validate_email_lowercases(self):
        """Test that email is lowercased"""
        result = validate_email("User@Example.COM")
        assert result == "user@example.com"
    
    def test_validate_email_with_plus(self):
        """Test validating email with plus sign"""
        result = validate_email("user+tag@example.com")
        assert result == "user+tag@example.com"
    
    def test_validate_email_with_subdomain(self):
        """Test validating email with subdomain"""
        result = validate_email("user@mail.example.com")
        assert result == "user@mail.example.com"
    
    def test_validate_email_rejects_injection_newline(self):
        """Test that newline injection is rejected"""
        with pytest.raises(ValidationError, match="Invalid characters"):
            validate_email("user@example.com\nBcc: attacker@evil.com")
    
    def test_validate_email_rejects_injection_carriage_return(self):
        """Test that carriage return injection is rejected"""
        with pytest.raises(ValidationError, match="Invalid characters"):
            validate_email("user@example.com\rBcc: attacker@evil.com")
    
    def test_validate_email_rejects_injection_encoded(self):
        """Test that encoded injection is rejected"""
        with pytest.raises(ValidationError, match="injection pattern detected"):
            validate_email("user@example.com%0aBcc: attacker@evil.com")
    
    def test_validate_email_rejects_injection_headers(self):
        """Test that email header injection is rejected"""
        headers = ["bcc:", "cc:", "to:", "content-type:"]
        for header in headers:
            with pytest.raises(ValidationError, match="injection pattern detected"):
                validate_email(f"user@example.com{header}attacker@evil.com")
    
    def test_validate_email_rejects_null_bytes(self):
        """Test that null bytes are rejected"""
        with pytest.raises(ValidationError, match="Invalid characters"):
            validate_email("user\x00@example.com")
    
    def test_validate_email_rejects_control_characters(self):
        """Test that control characters are rejected"""
        with pytest.raises(ValidationError, match="Invalid characters"):
            validate_email("user\x01@example.com")
    
    def test_validate_email_rejects_too_long(self):
        """Test that overly long emails are rejected"""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError, match="too long"):
            validate_email(long_email)
    
    def test_validate_email_rejects_too_short(self):
        """Test that too short emails are rejected"""
        with pytest.raises(ValidationError, match="too short"):
            validate_email("a@")
    
    def test_validate_email_rejects_no_at_sign(self):
        """Test that emails without @ are rejected"""
        with pytest.raises(ValidationError, match="Invalid email address format"):
            validate_email("userexample.com")
    
    def test_validate_email_rejects_no_domain_dot(self):
        """Test that emails without domain dot are rejected"""
        with pytest.raises(ValidationError, match="must contain at least one dot"):
            validate_email("user@example")
    
    def test_validate_email_rejects_consecutive_dots_in_local(self):
        """Test that consecutive dots in local part are rejected"""
        with pytest.raises(ValidationError, match="consecutive dots"):
            validate_email("user..name@example.com")
    
    def test_validate_email_rejects_leading_dot_in_local(self):
        """Test that leading dot in local part is rejected"""
        with pytest.raises(ValidationError, match="cannot start or end with dot"):
            validate_email(".user@example.com")
    
    def test_validate_email_rejects_trailing_dot_in_local(self):
        """Test that trailing dot in local part is rejected"""
        with pytest.raises(ValidationError, match="cannot start or end with dot"):
            validate_email("user.@example.com")
    
    def test_validate_email_non_string_input(self):
        """Test that non-string input is rejected"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_email(123)


class TestValidateEmailList:
    """Tests for email list validation"""
    
    def test_validate_valid_email_list(self):
        """Test validating a valid email list"""
        emails = ["user1@example.com", "user2@example.com"]
        result = validate_email_list(emails)
        assert result == ["user1@example.com", "user2@example.com"]
    
    def test_validate_email_list_removes_duplicates(self):
        """Test that duplicate emails are detected"""
        emails = ["user@example.com", "User@Example.COM"]
        with pytest.raises(ValidationError, match="Duplicate email"):
            validate_email_list(emails)
    
    def test_validate_email_list_rejects_empty(self):
        """Test that empty list is rejected"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_email_list([])
    
    def test_validate_email_list_rejects_too_many(self):
        """Test that too many recipients are rejected"""
        emails = [f"user{i}@example.com" for i in range(101)]
        with pytest.raises(ValidationError, match="Too many recipients"):
            validate_email_list(emails, max_recipients=100)
    
    def test_validate_email_list_non_list_input(self):
        """Test that non-list input is rejected"""
        with pytest.raises(ValidationError, match="must be a list"):
            validate_email_list("not a list")


class TestSanitizeSqlLikePattern:
    """Tests for SQL LIKE pattern sanitization"""
    
    def test_sanitize_sql_like_pattern_escapes_percent(self):
        """Test that percent signs are escaped"""
        result = sanitize_sql_like_pattern("test%pattern")
        assert result == "test\\%pattern"
    
    def test_sanitize_sql_like_pattern_escapes_underscore(self):
        """Test that underscores are escaped"""
        result = sanitize_sql_like_pattern("test_pattern")
        assert result == "test\\_pattern"
    
    def test_sanitize_sql_like_pattern_escapes_backslash(self):
        """Test that backslashes are escaped"""
        result = sanitize_sql_like_pattern("test\\pattern")
        assert result == "test\\\\pattern"


class TestValidateInteger:
    """Tests for integer validation"""
    
    def test_validate_valid_integer(self):
        """Test validating a valid integer"""
        result = validate_integer(42)
        assert result == 42
    
    def test_validate_integer_from_string(self):
        """Test validating integer from string"""
        result = validate_integer("42")
        assert result == 42
    
    def test_validate_integer_with_min_value(self):
        """Test validating integer with minimum value"""
        result = validate_integer(10, min_value=5)
        assert result == 10
    
    def test_validate_integer_below_min_value(self):
        """Test that integer below minimum is rejected"""
        with pytest.raises(ValidationError, match="less than minimum"):
            validate_integer(3, min_value=5)
    
    def test_validate_integer_with_max_value(self):
        """Test validating integer with maximum value"""
        result = validate_integer(10, max_value=20)
        assert result == 10
    
    def test_validate_integer_above_max_value(self):
        """Test that integer above maximum is rejected"""
        with pytest.raises(ValidationError, match="greater than maximum"):
            validate_integer(25, max_value=20)
    
    def test_validate_integer_invalid_input(self):
        """Test that invalid input is rejected"""
        with pytest.raises(ValidationError, match="Invalid integer"):
            validate_integer("not a number")


class TestValidateDateString:
    """Tests for date string validation"""
    
    def test_validate_valid_date_string(self):
        """Test validating a valid date string"""
        result = validate_date_string("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_validate_date_string_with_time(self):
        """Test validating date string with time"""
        result = validate_date_string("2024-01-15T10:30:00")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_validate_date_string_with_timezone(self):
        """Test validating date string with timezone"""
        result = validate_date_string("2024-01-15T10:30:00Z")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_validate_date_string_invalid_format(self):
        """Test that invalid date format is rejected"""
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date_string("15/01/2024")
    
    def test_validate_date_string_non_string_input(self):
        """Test that non-string input is rejected"""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_date_string(123)
