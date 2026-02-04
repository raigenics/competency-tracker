"""
BACKWARD COMPATIBILITY WRAPPER

This module maintains backward compatibility with the old import location.
The actual implementation has been refactored into:
app/services/imports/master_import/

Usage:
    from app.services.master_import_service import MasterImportService
    # Works exactly as before, but uses refactored code under the hood
"""
import logging
from sqlalchemy.orm import Session

# Import from new location
from app.services.imports.master_import import MasterImportService as _MasterImportService

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['MasterImportService']


class MasterImportService:
    """Service for processing master skills imports with conflict detection.
    
    BACKWARD COMPATIBILITY WRAPPER - delegates to refactored implementation.
    """
    
    def __init__(self, db: Session):
        self._service = _MasterImportService(db)
        self.db = db
    
    @property
    def errors(self):
        """Expose errors from underlying service."""
        # Combine errors from all components
        all_errors = []
        if hasattr(self._service, 'conflict_detector'):
            all_errors.extend(self._service.conflict_detector.errors)
        if hasattr(self._service, 'upserter'):
            all_errors.extend(self._service.upserter.errors)
        return all_errors
    
    @property
    def stats(self):
        """Expose stats from underlying service."""
        if hasattr(self._service, 'upserter'):
            return self._service.upserter.stats
        return {
            'categories': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'subcategories': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'skills': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'aliases': {'inserted': 0, 'existing': 0, 'conflicts': 0},
        }
    
    def load_caches(self):
        """Load caches (backward compatibility method)."""
        if hasattr(self._service, 'cache'):
            self._service.cache.load_all()
    
    def detect_file_duplicates(self, rows):
        """Detect file duplicates (backward compatibility method)."""
        return self._service.conflict_detector.detect_file_duplicates(rows)
    
    def upsert_category(self, category_name: str, category_norm: str) -> int:
        """Upsert category (backward compatibility method)."""
        return self._service.upserter.upsert_category(category_name, category_norm)
    
    def upsert_subcategory(self, subcategory_name: str, subcategory_norm: str, 
                          category_id: int, category_norm: str) -> int:
        """Upsert subcategory (backward compatibility method)."""
        return self._service.upserter.upsert_subcategory(
            subcategory_name, subcategory_norm, category_id, category_norm
        )
    
    def upsert_skill(self, row, subcategory_id: int):
        """Upsert skill (backward compatibility method)."""
        return self._service.upserter.upsert_skill(row, subcategory_id)
    
    def upsert_aliases(self, row, skill_id: int) -> bool:
        """Upsert aliases (backward compatibility method)."""
        return self._service.upserter.upsert_aliases(row, skill_id)
    
    def process_import(self, rows):
        """Process import - main method."""
        return self._service.process_import(rows)
