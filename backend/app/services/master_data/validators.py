"""
Validation helpers for Master Data operations.

Provides shared utility functions for input normalization and validation.
"""
from typing import Optional
from .exceptions import ValidationError


# Maximum length for name fields (consistent with typical DB constraints)
MAX_NAME_LENGTH = 255


def normalize_name(text: Optional[str]) -> Optional[str]:
    """
    Normalize a name field by trimming whitespace.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Trimmed text or None if input is None
    """
    if text is None:
        return None
    return text.strip()


def validate_name_not_empty(field_name: str, value: Optional[str]) -> str:
    """
    Validate that a name field is not empty after trimming.
    
    Args:
        field_name: Name of the field (for error message)
        value: Value to validate
        
    Returns:
        Trimmed, validated value
        
    Raises:
        ValidationError: If value is empty after trimming
    """
    normalized = normalize_name(value)
    
    if not normalized:
        raise ValidationError(
            field=field_name,
            message=f"{field_name} cannot be empty"
        )
    
    return normalized


def validate_name_length(field_name: str, value: str, max_length: int = MAX_NAME_LENGTH) -> str:
    """
    Validate that a name field doesn't exceed maximum length.
    
    Args:
        field_name: Name of the field (for error message)
        value: Value to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If value exceeds max length
    """
    if len(value) > max_length:
        raise ValidationError(
            field=field_name,
            message=f"{field_name} cannot exceed {max_length} characters"
        )
    
    return value


def validate_required_name(field_name: str, value: Optional[str], max_length: int = MAX_NAME_LENGTH) -> str:
    """
    Full validation for a required name field:
    1. Normalize (trim whitespace)
    2. Ensure not empty
    3. Ensure max length
    
    Args:
        field_name: Name of the field (for error message)
        value: Value to validate
        max_length: Maximum allowed length
        
    Returns:
        Normalized, validated value
        
    Raises:
        ValidationError: If validation fails
    """
    normalized = validate_name_not_empty(field_name, value)
    return validate_name_length(field_name, normalized, max_length)
