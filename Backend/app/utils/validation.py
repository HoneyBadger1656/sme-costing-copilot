# backend/app/utils/validation.py

"""
Input validation and sanitization utilities for security.

This module provides functions to validate and sanitize user inputs
to prevent injection attacks, directory traversal, and other security vulnerabilities.
"""

import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, date


class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass


def sanitize_string(value: str, max_length: int = 1000, allow_newlines: bool = False) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters
    
    Returns:
        Sanitized string
    
    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"Expected string, got {type(value).__name__}")
    
    # Check length
    if len(value) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")
    
    # Remove null bytes
    if '\x00' in value:
        raise ValidationError("Null bytes not allowed in string input")
    
    # Remove or validate newlines
    if not allow_newlines and ('\n' in value or '\r' in value):
        raise ValidationError("Newline characters not allowed")
    
    # Remove control characters except allowed ones
    allowed_control = {'\n', '\r', '\t'} if allow_newlines else {'\t'}
    sanitized = ''.join(
        char for char in value
        if not (ord(char) < 32 and char not in allowed_control)
    )
    
    return sanitized.strip()


def sanitize_report_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize report parameters to prevent injection attacks.
    
    Args:
        parameters: Report parameters dictionary
    
    Returns:
        Sanitized parameters dictionary
    
    Raises:
        ValidationError: If parameters contain invalid data
    """
    if not isinstance(parameters, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    sanitized = {}
    
    for key, value in parameters.items():
        # Sanitize key
        sanitized_key = sanitize_string(key, max_length=100, allow_newlines=False)
        
        # Validate key format (alphanumeric and underscores only)
        if not re.match(r'^[a-zA-Z0-9_]+$', sanitized_key):
            raise ValidationError(f"Invalid parameter key format: {key}")
        
        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[sanitized_key] = sanitize_string(value, max_length=1000)
        elif isinstance(value, (int, float, bool)):
            sanitized[sanitized_key] = value
        elif isinstance(value, (datetime, date)):
            sanitized[sanitized_key] = value
        elif isinstance(value, list):
            sanitized[sanitized_key] = sanitize_list(value)
        elif isinstance(value, dict):
            sanitized[sanitized_key] = sanitize_report_parameters(value)
        elif value is None:
            sanitized[sanitized_key] = None
        else:
            raise ValidationError(f"Unsupported parameter type: {type(value).__name__}")
    
    return sanitized


def sanitize_list(items: List[Any], max_items: int = 1000) -> List[Any]:
    """
    Sanitize list items.
    
    Args:
        items: List to sanitize
        max_items: Maximum number of items allowed
    
    Returns:
        Sanitized list
    
    Raises:
        ValidationError: If list is invalid
    """
    if not isinstance(items, list):
        raise ValidationError("Expected list")
    
    if len(items) > max_items:
        raise ValidationError(f"List exceeds maximum length of {max_items}")
    
    sanitized = []
    for item in items:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item, max_length=1000))
        elif isinstance(item, (int, float, bool)):
            sanitized.append(item)
        elif isinstance(item, dict):
            sanitized.append(sanitize_report_parameters(item))
        elif item is None:
            sanitized.append(None)
        else:
            raise ValidationError(f"Unsupported list item type: {type(item).__name__}")
    
    return sanitized


def validate_file_path(file_path: str, base_directory: str) -> Path:
    """
    Validate file path to prevent directory traversal attacks.
    
    Args:
        file_path: File path to validate
        base_directory: Base directory that file must be within
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If path is invalid or attempts directory traversal
    """
    if not isinstance(file_path, str):
        raise ValidationError("File path must be a string")
    
    # Remove null bytes
    if '\x00' in file_path:
        raise ValidationError("Null bytes not allowed in file path")
    
    # Check for suspicious patterns
    suspicious_patterns = ['..', '~', '$', '`', '|', ';', '&', '\n', '\r']
    for pattern in suspicious_patterns:
        if pattern in file_path:
            raise ValidationError(f"Suspicious pattern '{pattern}' detected in file path")
    
    # Resolve paths
    try:
        base_path = Path(base_directory).resolve()
        target_path = (base_path / file_path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(f"Invalid file path: {e}")
    
    # Ensure target is within base directory
    try:
        target_path.relative_to(base_path)
    except ValueError:
        raise ValidationError("File path attempts directory traversal")
    
    return target_path


def validate_email(email: str) -> str:
    """
    Validate email address format to prevent email injection.
    
    Args:
        email: Email address to validate
    
    Returns:
        Validated email address (lowercased)
    
    Raises:
        ValidationError: If email is invalid
    """
    if not isinstance(email, str):
        raise ValidationError("Email must be a string")
    
    # Remove whitespace
    email = email.strip()
    
    # Check length
    if len(email) > 254:  # RFC 5321
        raise ValidationError("Email address too long")
    
    if len(email) < 3:
        raise ValidationError("Email address too short")
    
    # Check for null bytes and control characters
    if '\x00' in email or any(ord(c) < 32 for c in email):
        raise ValidationError("Invalid characters in email address")
    
    # Check for email injection patterns
    injection_patterns = ['\n', '\r', '%0a', '%0d', 'bcc:', 'cc:', 'to:', 'content-type:']
    email_lower = email.lower()
    for pattern in injection_patterns:
        if pattern in email_lower:
            raise ValidationError("Email injection pattern detected")
    
    # Validate format using RFC 5322 simplified regex
    # This is a practical regex that catches most valid emails
    pattern = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
        r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    )
    
    if not pattern.match(email):
        raise ValidationError("Invalid email address format")
    
    # Additional checks
    local, domain = email.rsplit('@', 1)
    
    # Local part checks
    if len(local) > 64:  # RFC 5321
        raise ValidationError("Email local part too long")
    
    if local.startswith('.') or local.endswith('.'):
        raise ValidationError("Email local part cannot start or end with dot")
    
    if '..' in local:
        raise ValidationError("Email local part cannot contain consecutive dots")
    
    # Domain checks
    if len(domain) > 253:  # RFC 1035
        raise ValidationError("Email domain too long")
    
    if domain.startswith('-') or domain.endswith('-'):
        raise ValidationError("Email domain cannot start or end with hyphen")
    
    # Check domain has at least one dot
    if '.' not in domain:
        raise ValidationError("Email domain must contain at least one dot")
    
    return email.lower()


def validate_email_list(emails: List[str], max_recipients: int = 100) -> List[str]:
    """
    Validate a list of email addresses.
    
    Args:
        emails: List of email addresses
        max_recipients: Maximum number of recipients allowed
    
    Returns:
        List of validated email addresses
    
    Raises:
        ValidationError: If any email is invalid
    """
    if not isinstance(emails, list):
        raise ValidationError("Emails must be a list")
    
    if not emails:
        raise ValidationError("Email list cannot be empty")
    
    if len(emails) > max_recipients:
        raise ValidationError(f"Too many recipients (max {max_recipients})")
    
    validated = []
    seen = set()
    
    for email in emails:
        validated_email = validate_email(email)
        
        # Check for duplicates
        if validated_email in seen:
            raise ValidationError(f"Duplicate email address: {email}")
        
        seen.add(validated_email)
        validated.append(validated_email)
    
    return validated


def sanitize_sql_like_pattern(pattern: str) -> str:
    """
    Sanitize SQL LIKE pattern to prevent SQL injection.
    
    Args:
        pattern: LIKE pattern string
    
    Returns:
        Sanitized pattern
    """
    if not isinstance(pattern, str):
        raise ValidationError("Pattern must be a string")
    
    # Escape special SQL LIKE characters
    pattern = pattern.replace('\\', '\\\\')
    pattern = pattern.replace('%', '\\%')
    pattern = pattern.replace('_', '\\_')
    
    return sanitize_string(pattern, max_length=255)


def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    Validate and convert to integer.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    
    Returns:
        Validated integer
    
    Raises:
        ValidationError: If value is invalid
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid integer value: {value}")
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(f"Value {int_value} is less than minimum {min_value}")
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(f"Value {int_value} is greater than maximum {max_value}")
    
    return int_value


def validate_date_string(date_str: str) -> date:
    """
    Validate and parse date string.
    
    Args:
        date_str: Date string in ISO format
    
    Returns:
        Parsed date object
    
    Raises:
        ValidationError: If date is invalid
    """
    if not isinstance(date_str, str):
        raise ValidationError("Date must be a string")
    
    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.date()
    except (ValueError, AttributeError) as e:
        raise ValidationError(f"Invalid date format: {e}")
