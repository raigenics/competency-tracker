"""
Scope entity name resolution service.

Maps scope type + scope ID to human-readable entity names
(e.g., SUB_SEGMENT:5 -> "Audiology Division")
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.auth.auth_scope_type import AuthScopeType
from app.models.employee import Employee
from app.models.segment import Segment
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team

logger = logging.getLogger(__name__)


class ScopeResolver:
    """Service for resolving scope entity names."""

    # Mapping of scope type names to database models and field names
    SCOPE_MAPPING = {
        'SEGMENT': (Segment, 'segment_id', 'segment_name'),
        'SUB_SEGMENT': (SubSegment, 'sub_segment_id', 'sub_segment_name'),
        'PROJECT': (Project, 'project_id', 'project_name'),
        'TEAM': (Team, 'team_id', 'team_name'),
        'EMPLOYEE': (Employee, 'employee_id', 'full_name'),
    }

    @staticmethod
    def get_scope_entity_name(
        db: Session,
        scope_type_id: int,
        scope_id: Optional[int]
    ) -> Optional[str]:
        """
        Get the name of a scope entity.
        
        Args:
            db: Database session
            scope_type_id: Scope type ID
            scope_id: Scope entity ID (can be None for GLOBAL)
        
        Returns:
            Scope entity name, "All Systems" for GLOBAL, or None if not found
        """
        # Handle GLOBAL scope
        if scope_id is None:
            return "All Systems"

        # Get scope type to determine which table to query
        scope_type = db.query(AuthScopeType).filter(
            AuthScopeType.scope_type_id == scope_type_id
        ).first()

        if not scope_type:
            logger.warning(f"Scope type ID {scope_type_id} not found")
            return None

        # Check if scope type is supported
        if scope_type.scope_type_code not in ScopeResolver.SCOPE_MAPPING:
            logger.warning(f"Unsupported scope type: {scope_type.scope_type_code}")
            return None

        # Query the appropriate table
        model, id_field, name_field = ScopeResolver.SCOPE_MAPPING[scope_type.scope_type_code]
        
        try:
            entity = db.query(model).filter(
                getattr(model, id_field) == scope_id
            ).first()
            
            if entity:
                return getattr(entity, name_field)
            else:
                logger.warning(
                    f"Scope entity not found: {scope_type.scope_type_code} ID {scope_id}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error resolving scope entity: {scope_type.scope_type_code} "
                f"ID {scope_id}: {str(e)}",
                exc_info=True
            )
            return None
