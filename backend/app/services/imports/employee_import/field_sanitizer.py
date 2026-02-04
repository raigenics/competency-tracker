"""
Field sanitization utilities for employee import.

Single Responsibility: Sanitize and validate field values.
"""
import logging
from typing import Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


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
