"""
Field sanitization utilities for employee import.

Single Responsibility: Sanitize and validate field values.
"""
import logging
from typing import Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Placeholder values that mean "not certified" — case-insensitive, trimmed
CERTIFICATION_PLACEHOLDERS = frozenset({
    'no',
    'none',
    'na',
    'n/a',
    'not certified',
    'no certification',
    '0',
})


class FieldSanitizer:
    """Handles field sanitization and validation."""
    
    def sanitize_integer_field(self, value: Any, field_name: str, zid: str) -> Optional[int]:
        """
        Sanitize integer fields - convert pandas NaN to None for PostgreSQL.
        
        Args:
            value: Raw value from Excel
            field_name: Name of the field for logging
            zid: Employee ZID for logging
            
        Returns:
            Integer value or None
        """
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid {field_name} value '{value}' for employee {zid}, setting to None")
            return None

    def normalize_certification(self, value: Any) -> Optional[str]:
        """
        Normalize certification field from Excel import.
        
        Treats placeholder values like "No", "None", "N/A", "Not Certified", "0"
        as "no certification" and returns None. Any other non-empty value is
        returned trimmed.
        
        Args:
            value: Raw certification value from Excel
            
        Returns:
            Trimmed certification string if valid, None if placeholder or empty
        """
        # Handle pandas NaN/NaT and Python None
        if value is None or pd.isna(value):
            return None
        
        # Convert to string and trim whitespace
        str_value = str(value).strip()
        
        # Empty or whitespace-only → no certification
        if not str_value:
            return None
        
        # Check against placeholder values (case-insensitive)
        if str_value.lower() in CERTIFICATION_PLACEHOLDERS:
            return None
        
        # Valid certification name — return as-is (trimmed)
        return str_value
