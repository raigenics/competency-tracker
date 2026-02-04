"""
Name normalization utilities for employee import.

Single Responsibility: Normalize names for case-insensitive comparison.
"""
import logging
import re

logger = logging.getLogger(__name__)


class NameNormalizer:
    """Handles name normalization matching database constraints."""
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize any name for case-insensitive comparison.
        Matches database unique constraints: lower(trim(name))

        Args:
            name: Raw name from Excel

        Returns:
            Normalized name (trimmed, collapsed spaces, lowercased)
        """
        if not name:
            return ""
        # Strip leading/trailing spaces and collapse multiple internal spaces
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        # Return lowercased for comparison
        return name.lower()
