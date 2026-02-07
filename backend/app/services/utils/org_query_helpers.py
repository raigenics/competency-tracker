"""
Organizational Query Helpers - Phase 1 Behavioral Normalization

PURPOSE:
Centralized helper functions for applying organizational filters to Employee queries.
This module enforces the canonical rule: employee.team_id is the ONLY source of truth.

PHASE 1 BEHAVIORAL NORMALIZATION:
- Database schema remains unchanged (sub_segment_id, project_id columns still exist)
- Query logic now derives these values through joins instead of direct column access
- Canonical hierarchy: Employee -> Team -> Project -> SubSegment

CANONICAL RULE:
- employee.team_id = source of truth (direct FK)
- employee.project_id = DERIVED via employee.team.project_id
- employee.sub_segment_id = DERIVED via employee.team.project.sub_segment_id

USAGE:
Apply organizational filters using joins instead of direct Employee column filters:

    query = db.query(Employee)
    query = apply_org_filters(query, sub_segment_id=5, project_id=None, team_id=None)

WHY THIS MATTERS:
- Prepares codebase for future schema normalization (Phase 2)
- Enforces single source of truth (team_id)
- Prevents data inconsistency from using redundant columns
- Centralizes org filtering logic (DRY principle)

CONSTRAINTS:
- These helpers are READ-ONLY (no write operations)
- API contracts remain unchanged
- Frontend receives identical data
- All existing tests must pass
"""
from typing import Optional
from sqlalchemy.orm import Query

from app.models.employee import Employee
from app.models.team import Team
from app.models.project import Project
from app.models.sub_segment import SubSegment


def apply_org_filters(
    query: Query,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None
) -> Query:
    """
    Apply organizational scope filters to an Employee query using canonical joins.
    
    NORMALIZATION PRINCIPLE:
    - Filters by team_id directly (canonical FK)
    - Filters by project_id via Team join (derived)
    - Filters by sub_segment_id via Team->Project join (derived)
    
    Hierarchy: Team (most specific) > Project > SubSegment > Organization (no filter)
    
    Args:
        query: Base SQLAlchemy query on Employee model
        sub_segment_id: Filter employees in this sub-segment (via join)
        project_id: Filter employees in this project (via join)
        team_id: Filter employees in this team (direct FK)
    
    Returns:
        Filtered query with appropriate joins applied
        
    Example:
        >>> query = db.query(Employee)
        >>> query = apply_org_filters(query, project_id=5)
        >>> # Result: Employees whose team.project_id == 5
    
    Phase 1 Notes:
        - employee.project_id and employee.sub_segment_id columns still exist
        - We deliberately DO NOT filter on them directly
        - This enforces team_id as canonical source of truth
    """
    # Most specific filter wins (team > project > sub_segment)
    if team_id:
        # Direct filter on canonical FK (no join needed)
        query = query.filter(Employee.team_id == team_id)
    
    elif project_id:
        # PHASE 1 NORMALIZATION: Derive project membership via Team join
        # OLD (deprecated): query.filter(Employee.project_id == project_id)
        # NEW (canonical): Join through team relationship
        query = query.join(Team).filter(Team.project_id == project_id)
    
    elif sub_segment_id:
        # PHASE 1 NORMALIZATION: Derive sub-segment membership via Team->Project joins
        # OLD (deprecated): query.filter(Employee.sub_segment_id == sub_segment_id)
        # NEW (canonical): Join through team->project relationship
        query = (query
                 .join(Team)
                 .join(Project)
                 .filter(Project.sub_segment_id == sub_segment_id))
    
    # No filter = organization-wide scope (all employees)
    return query


def apply_org_filters_to_employee_ids(
    query: Query,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None
) -> Query:
    """
    Apply organizational filters to a query that selects employee IDs.
    
    Identical logic to apply_org_filters() but optimized for subqueries
    that only need employee_id (no relationship loading needed).
    
    Args:
        query: Base query selecting Employee.employee_id
        sub_segment_id: Filter by sub-segment (via join)
        project_id: Filter by project (via join)
        team_id: Filter by team (direct FK)
    
    Returns:
        Filtered query
        
    Usage:
        >>> query = db.query(Employee.employee_id)
        >>> query = apply_org_filters_to_employee_ids(query, sub_segment_id=3)
        >>> employee_ids = [row[0] for row in query.all()]
    """
    # Identical filter logic (reuse for consistency)
    return apply_org_filters(query, sub_segment_id, project_id, team_id)


def get_employee_org_context(employee: Employee) -> dict:
    """
    Get organizational context for an employee via canonical traversal.
    
    PHASE 1 NORMALIZATION:
    - Derives all org IDs through team relationship
    - Returns dict with both IDs and names
    - Used for response serialization
    
    Args:
        employee: Employee model instance with relationships loaded
    
    Returns:
        Dict with keys: team_id, team_name, project_id, project_name,
                       sub_segment_id, sub_segment_name
    
    Example:
        >>> context = get_employee_org_context(employee)
        >>> print(context['project_name'])  # From employee.team.project.project_name
    """
    if not employee.team:
        # Handle orphaned employees gracefully
        return {
            'team_id': employee.team_id,
            'team_name': None,
            'project_id': None,
            'project_name': None,
            'sub_segment_id': None,
            'sub_segment_name': None
        }
    
    project = employee.team.project
    sub_segment = project.sub_segment if project else None
    
    return {
        'team_id': employee.team.team_id,
        'team_name': employee.team.team_name,
        'project_id': project.project_id if project else None,
        'project_name': project.project_name if project else None,
        'sub_segment_id': sub_segment.sub_segment_id if sub_segment else None,
        'sub_segment_name': sub_segment.sub_segment_name if sub_segment else None
    }
