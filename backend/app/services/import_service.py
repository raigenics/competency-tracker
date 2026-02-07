"""
BACKWARD COMPATIBILITY WRAPPER

This module maintains backward compatibility with the old import location.
The actual implementation has been refactored into:
app/services/imports/employee_import/

Usage:
    from app.services.import_service import ImportService
    # Works exactly as before, but uses refactored code under the hood
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Import from new location
from app.services.imports.employee_import import EmployeeImportOrchestrator, ImportServiceError as _ImportServiceError

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['ImportService', 'ImportServiceError']


class ImportServiceError(_ImportServiceError):
    """Custom exception for import service errors."""
    pass


class ImportService:
    """Service class for handling Excel imports with PostgreSQL compatibility.
    
    BACKWARD COMPATIBILITY WRAPPER - delegates to refactored implementation.
    """
    
    def __init__(self, db_session: Optional[Session] = None, job_id: Optional[str] = None):
        self._orchestrator = EmployeeImportOrchestrator(db_session, job_id=job_id)
    
    @property
    def db(self):
        """Expose db session from orchestrator."""
        return self._orchestrator.db
    
    @property
    def import_stats(self):
        """Expose import stats from orchestrator."""
        return self._orchestrator.import_stats
    
    def import_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Import Excel file data.
        
        Args:
            file_path (str): Path to the Excel file

        Returns:
            Dict with import statistics

        Raises:
            ImportServiceError: If import fails
        """
        return self._orchestrator.import_excel(file_path)
    
    # Expose individual methods for backward compatibility (if needed)
    def _parse_date_safely(self, date_str: str, field_name: str, record_id: str = ""):
        """Backward compatibility method."""
        return self._orchestrator.date_parser.parse_date_safely(date_str, field_name, record_id)
    
    def _normalize_name(self, name: str) -> str:
        """Backward compatibility method."""
        return self._orchestrator.name_normalizer.normalize_name(name)
    
    def _normalize_subcategory_name(self, name: str) -> str:
        """Backward compatibility method."""
        return self._orchestrator.name_normalizer.normalize_name(name)
    
    def _sanitize_integer_field(self, value, field_name: str, zid: str):
        """Backward compatibility method."""
        return self._orchestrator.field_sanitizer.sanitize_integer_field(value, field_name, zid)
