"""
Dashboard service facade - thin wrapper for isolated dashboard section services.

ARCHITECTURE:
This file serves as a backward-compatible facade that delegates to isolated section services.
Each dashboard section is implemented in its own file to prevent cross-contamination of changes.

PUBLIC API (DO NOT CHANGE - Used by routers):
- get_employee_scope_count() -> delegates to scope_count_service
- get_org_skill_coverage() -> delegates to org_skill_coverage_service

ISOLATION PRINCIPLE:
Each section service is completely independent. Changes to one section do NOT affect others.
No shared utilities or common helpers between sections to prevent breaking changes.

NOTE: Some dashboard sections (top skills, skill momentum, skill update activity) are 
implemented directly in the router and do NOT have corresponding service methods here.
"""
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

# Import isolated section services
from app.services.dashboard.scope_count_service import (
    get_employee_scope_count as _get_employee_scope_count
)
from app.services.dashboard.org_skill_coverage_service import (
    get_org_skill_coverage as _get_org_skill_coverage
)


class DashboardService:
    """
    Service class for dashboard-related data operations.
    
    This is a thin facade that delegates to isolated section services.
    Maintains backward compatibility with existing router code.
    """

    @staticmethod
    def get_employee_scope_count(
        db: Session,
        sub_segment_id: Optional[int] = None,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> Tuple[int, str, str]:
        """
        Get employee count and scope information based on filters.
        
        Delegates to: scope_count_service.get_employee_scope_count()
        
        Args:
            db: Database session
            sub_segment_id: Optional sub-segment filter
            project_id: Optional project filter
            team_id: Optional team filter
        
        Returns:
            Tuple of (employee_count, scope_level, scope_name)
        
        Raises:
            ValueError: If filter hierarchy is invalid or entity not found
        """
        return _get_employee_scope_count(db, sub_segment_id, project_id, team_id)

    @staticmethod
    def get_org_skill_coverage(db: Session) -> Dict[str, Any]:
        """
        Get organization-wide skill coverage by sub-segment and role.
        
        Delegates to: org_skill_coverage_service.get_org_skill_coverage()
        
        This always returns organization-wide data and ignores any dashboard filters.
        
        Args:
            db: Database session
        
        Returns:
            Dict containing sub-segment breakdown and organization totals
        """
        return _get_org_skill_coverage(db)