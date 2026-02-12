"""
Master Data services module.

Provides:
- skill_taxonomy_service: Read operations for taxonomy hierarchy
- taxonomy_update_service: Update operations for taxonomy entities
- exceptions: Custom exception types (NotFoundError, ConflictError, ValidationError)
- validators: Input validation helpers
"""
from app.services.master_data.skill_taxonomy_service import get_skill_taxonomy
from app.services.master_data import taxonomy_update_service
from app.services.master_data.exceptions import (
    MasterDataError,
    NotFoundError,
    ConflictError,
    ValidationError,
)
from app.services.master_data.validators import (
    normalize_name,
    validate_required_name,
)

__all__ = [
    "get_skill_taxonomy",
    "taxonomy_update_service",
    "MasterDataError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "normalize_name",
    "validate_required_name",
]
