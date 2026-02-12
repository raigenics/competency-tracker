"""
Dashboard Section: Employee Scope Count

PUBLIC ENTRYPOINT:
- get_employee_scope_count(db, sub_segment_id, project_id, team_id) -> Tuple[int, str, str]

HELPERS:
- _validate_filter_hierarchy() - Pure validation logic (unit testable without DB)
- _query_team_scope() - DB query for team-level scope
- _query_project_scope() - DB query for project-level scope
- _query_sub_segment_scope() - DB query for sub-segment-level scope
- _query_organization_scope() - DB query for organization-level scope

OUTPUT CONTRACT (MUST NOT CHANGE):
- Returns tuple: (employee_count: int, scope_level: str, scope_name: str)
- scope_level values: "TEAM", "PROJECT", "SUB_SEGMENT", "ORGANIZATION"
- Raises ValueError for invalid filters or missing entities

ISOLATION:
- This file is self-contained and does NOT import from other dashboard sections.
- Changes here must NOT affect other dashboard sections.
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.employee import Employee
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team
from app.services.utils.org_query_helpers import apply_org_filters


def get_employee_scope_count(
    db: Session,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None
) -> Tuple[int, str, str]:
    """
    Get employee count and scope information based on filters.
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        Tuple of (employee_count, scope_level, scope_name)
        - employee_count: Number of employees in scope
        - scope_level: "TEAM", "PROJECT", "SUB_SEGMENT", or "ORGANIZATION"
        - scope_name: Name of the scoped entity
    
    Raises:
        ValueError: If filter hierarchy is invalid or entity not found
    """
    # Validate filter hierarchy consistency
    _validate_filter_hierarchy(db, sub_segment_id, project_id, team_id)
    
    # Determine scope level and execute appropriate query
    if team_id:
        return _query_team_scope(db, team_id)
    elif project_id:
        return _query_project_scope(db, project_id)
    elif sub_segment_id:
        return _query_sub_segment_scope(db, sub_segment_id)
    else:
        return _query_organization_scope(db)


def _validate_filter_hierarchy(
    db: Session,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> None:
    """
    Validate that the filter hierarchy is consistent.
    
    Business rules:
    - Project filter requires sub_segment_id
    - Team filter requires project_id
    
    Args:
        db: Database session (not used but kept for consistency)
        sub_segment_id: Optional sub-segment ID
        project_id: Optional project ID
        team_id: Optional team ID
    
    Raises:
        ValueError: If hierarchy rules are violated
    """
    if project_id and not sub_segment_id:
        raise ValueError("Project filter requires sub_segment_id to be provided")
    if team_id and not project_id:
        raise ValueError("Team filter requires project_id to be provided")


def _query_team_scope(db: Session, team_id: int) -> Tuple[int, str, str]:
    """
    Query employee count and details for team-level scope.
    
    Args:
        db: Database session
        team_id: Team ID to filter by
    
    Returns:
        Tuple of (count, "TEAM", team_name)
    
    Raises:
        ValueError: If team not found
    """
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise ValueError(f"Team with ID {team_id} not found")
    
    count = db.query(func.count(Employee.employee_id)).filter(
        Employee.team_id == team_id,
        Employee.deleted_at.is_(None)
    ).scalar()
    
    return count, "TEAM", team.team_name


def _query_project_scope(db: Session, project_id: int) -> Tuple[int, str, str]:
    """
    Query employee count and details for project-level scope.
    
    PHASE 1 NORMALIZATION:
    - Counts employees via Team join (employee.team.project_id == project_id)
    - No longer filters directly on Employee.project_id
    - Canonical derivation: employee -> team -> project
    
    Args:
        db: Database session
        project_id: Project ID to filter by
    
    Returns:
        Tuple of (count, "PROJECT", project_name)
    
    Raises:
        ValueError: If project not found
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found")
    
    # PHASE 1 NORMALIZATION: Use join-based filtering
    # OLD: Employee.project_id == project_id (direct redundant column)
    # NEW: Join through Team to derive project membership
    query = db.query(func.count(Employee.employee_id)).filter(
        Employee.deleted_at.is_(None)
    )
    query = apply_org_filters(query, project_id=project_id)
    count = query.scalar()
    
    return count, "PROJECT", project.project_name


def _query_sub_segment_scope(db: Session, sub_segment_id: int) -> Tuple[int, str, str]:
    """
    Query employee count and details for sub-segment-level scope.
    
    PHASE 1 NORMALIZATION:
    - Counts employees via Team->Project joins
    - No longer filters directly on Employee.sub_segment_id
    - Canonical derivation: employee -> team -> project -> sub_segment
    
    Args:
        db: Database session
        sub_segment_id: Sub-segment ID to filter by
    
    Returns:
        Tuple of (count, "SUB_SEGMENT", sub_segment_name)
    
    Raises:
        ValueError: If sub-segment not found
    """
    sub_segment = db.query(SubSegment).filter(
        SubSegment.sub_segment_id == sub_segment_id
    ).first()
    if not sub_segment:
        raise ValueError(f"Sub-segment with ID {sub_segment_id} not found")
    
    # PHASE 1 NORMALIZATION: Use join-based filtering
    # OLD: Employee.sub_segment_id == sub_segment_id (direct redundant column)
    # NEW: Join through Team->Project to derive sub-segment membership
    query = db.query(func.count(Employee.employee_id)).filter(
        Employee.deleted_at.is_(None)
    )
    query = apply_org_filters(query, sub_segment_id=sub_segment_id)
    count = query.scalar()
    
    return count, "SUB_SEGMENT", sub_segment.sub_segment_name


def _query_organization_scope(db: Session) -> Tuple[int, str, str]:
    """
    Query employee count for organization-wide scope.
    
    Args:
        db: Database session
    
    Returns:
        Tuple of (count, "ORGANIZATION", "Organization-Wide")
    """
    count = db.query(func.count(Employee.employee_id)).filter(
        Employee.deleted_at.is_(None)
    ).scalar()
    
    return count, "ORGANIZATION", "Organization-Wide"
