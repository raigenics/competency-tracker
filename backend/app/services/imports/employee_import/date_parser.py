"""
Date parsing utilities for employee import.

Single Responsibility: Parse and validate date strings.
"""
import logging
from typing import Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)


class DateParser:
    """Handles date parsing with PostgreSQL compatibility."""
      # Common date formats to try
    DATE_FORMATS = [
        '%Y-%m-%d',      # 2011-02-02 (ISO format - PostgreSQL preferred)
        '%d-%m-%Y',      # 02-02-2011
        '%m/%d/%Y',      # 02/02/2011
        '%d/%m/%Y',      # 02/02/2011
        '%Y/%m/%d',      # 2011/02/02
        '%d-%b-%y',      # 1-Sep-25
        '%d-%B-%y',      # 1-September-25
        '%d-%b-%Y',      # 1-Sep-2025
        '%d-%B-%Y',      # 1-September-2025
        '%b-%y',         # Sep-25 (MMM-yy format - converts to 01-Sep-2025)
        '%B-%y',         # September-25 (Full month name)
    ]
    
    def parse_date_safely(self, date_str: str, field_name: str, record_id: str = "") -> Optional[date]:
        """
        Safely parse date strings with PostgreSQL compatibility.

        Args:
            date_str: Date string to parse
            field_name: Name of the field for logging
            record_id: ID of the record for logging

        Returns:
            Parsed date or None if parsing fails
        """
        if not date_str or str(date_str).lower() in ['nan', 'none', '']:
            return None

        try:
            # Clean the date string
            date_str = str(date_str).strip()

            # Try all date formats
            parsed_date = self._try_parse_formats(date_str)
            
            if parsed_date:
                # Validate date range for PostgreSQL compatibility
                if not self._is_valid_postgres_date(parsed_date):
                    logger.warning(f"Date year out of PostgreSQL range for {field_name} '{date_str}' in record {record_id}")
                    return None
                return parsed_date
            
            # Special case: try to extract year and create end-of-year date
            year_date = self._try_parse_year_only(date_str)
            if year_date:
                return year_date
            
            logger.warning(f"Could not parse {field_name} '{date_str}' for record {record_id}")
            return None
        
        except Exception as e:
            logger.warning(f"Date conversion error for {field_name} '{date_str}' in record {record_id}: {e}")
            return None
    
    def _try_parse_formats(self, date_str: str) -> Optional[date]:
        """Try parsing date string with all known formats."""
        for date_format in self.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, date_format).date()
            except ValueError:
                continue
        return None
    
    def _try_parse_year_only(self, date_str: str) -> Optional[date]:
        """Try parsing as year only and return end-of-year date."""
        try:
            year = int(date_str)
            if 1900 <= year <= 2100:
                return datetime(year, 12, 31).date()
        except ValueError:
            pass
        return None
    
    def _is_valid_postgres_date(self, date_obj: date) -> bool:
        """Check if date is within PostgreSQL valid range."""
        return 1000 <= date_obj.year <= 9999
