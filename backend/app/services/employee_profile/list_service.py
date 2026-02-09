"""
List Service - GET /employees

Handles paginated employee listing with optional filters.
Zero dependencies on other services.

NORMALIZED SCHEMA (HYBRID pattern):
- team_id is the only direct FK on Employee (source of truth)
- project/sub_segment/segment derived via joins: team -> project -> sub_segment -> segment
- Query logic enforces canonical navigation through relationships
- API contracts preserved (responses unchanged)

RBAC Integration:
- Accepts RbacContext for scope-based filtering
- Applies role-appropriate filters before user-defined filters
- All organizational filters use join-based derivation
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Employee, EmployeeSkill
from app.models.team import Team
from app.models.project import Project
from app.models.sub_segment import SubSegment
from app.schemas.employee import EmployeeResponse, EmployeeListResponse, OrganizationInfo
from app.schemas.common import PaginationParams
from app.services.utils.org_query_helpers import apply_org_filters
from app.security.rbac_policy import RbacContext

logger = logging.getLogger(__name__)


def get_employees_paginated(
    db: Session,
    pagination: PaginationParams,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    role_id: Optional[int] = None,
    search: Optional[str] = None,
    rbac_context: Optional[RbacContext] = None
) -> EmployeeListResponse:
    """
    Get paginated list of employees with optional filters.
    
    Args:
        db: Database session
        pagination: Pagination parameters (page, size, offset)
        sub_segment_id: Optional sub-segment ID filter
        project_id: Optional project ID filter
        team_id: Optional team ID filter
        role_id: Optional role ID filter
        search: Optional search by name or ZID
        rbac_context: RBAC context for scope-based filtering (optional for backward compat)
    
    Returns:
        EmployeeListResponse with paginated employee data
    """
    logger.info(f"Fetching employees: page={pagination.page}, size={pagination.size}, "
                f"sub_segment_id={sub_segment_id}, project_id={project_id}, "
                f"team_id={team_id}, role_id={role_id}, search={search}, "
                f"rbac_role={rbac_context.role if rbac_context else 'None'}")
    
    # Build filtered query
    query = _build_employee_query(db, sub_segment_id, project_id, team_id, role_id, search, rbac_context)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and fetch
    employees = query.offset(pagination.offset).limit(pagination.size).all()
    
    # Build response with skills count
    response_items = _build_employee_responses(db, employees)
    
    # Calculate total pages
    pages = (total + pagination.size - 1) // pagination.size if total > 0 else 0
    
    logger.info(f"Returning {len(response_items)} employees (total: {total})")
    
    return EmployeeListResponse(
        items=response_items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pages
    )


# === DATABASE QUERIES ===

def _build_employee_query(
    db: Session,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int],
    role_id: Optional[int],
    search: Optional[str],
    rbac_context: Optional[RbacContext] = None
):
    """
    Build filtered employee query with eager loading.
    Returns query object (not executed).
    
    PHASE 1 NORMALIZATION:
    - Organizational filters applied via centralized helper (join-based)
    - No longer filters directly on Employee.project_id or Employee.sub_segment_id
    - Canonical: team_id is source of truth, project/sub_segment derived via joins
    
    RBAC Filtering:
    - Applied BEFORE user-defined filters (row-level security)
    - SEGMENT_HEAD: requires join to SubSegment for segment_id
    - Other roles: filter on direct columns (sub_segment_id, project_id, team_id)
    """
    query = db.query(Employee).options(
        # NORMALIZED: Load org chain via team -> project -> sub_segment
        joinedload(Employee.team)
            .joinedload(Team.project)
            .joinedload(Project.sub_segment),
        joinedload(Employee.role)
    )
    
    # === RBAC SCOPE FILTERING ===
    # Apply role-based scope limits FIRST (cannot be overridden by user filters)
    if rbac_context:
        query = _apply_rbac_scope_filter(query, rbac_context)
    
    # PHASE 1 NORMALIZATION: Apply org filters using canonical join-based logic
    # OLD: Direct filters on Employee.sub_segment_id, Employee.project_id
    # NEW: Centralized helper enforces team_id as source of truth
    query = apply_org_filters(query, sub_segment_id, project_id, team_id)
    
    # Role filter (unchanged - not part of org hierarchy)
    if role_id:
        query = query.filter(Employee.role_id == role_id)
    
    # Search by name or ZID
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Employee.full_name.ilike(search_term)) |
            (Employee.zid.ilike(search_term))
        )
    
    return query


def _apply_rbac_scope_filter(query, rbac_context: RbacContext):
    """
    Apply RBAC scope filtering to employee query.
    
    Row-level security: limits which employees the user can see based on their role.
    
    NORMALIZED: All org filters use join-based derivation through team:
    - Employee.team_id -> Team.project_id -> Project.sub_segment_id -> SubSegment.segment_id
    
    Scope levels:
    - 'all': SUPER_ADMIN - no filtering
    - 'segment': SEGMENT_HEAD - join through team->project->sub_segment->segment
    - 'sub_segment': SUBSEGMENT_HEAD - join through team->project->sub_segment
    - 'project': PROJECT_MANAGER - join through team->project
    - 'team': TEAM_LEAD/TEAM_MEMBER - filter on Employee.team_id (direct)
    
    Returns:
        Modified query with RBAC filters applied.
    """
    scope_level = rbac_context.permissions.scope_level
    scope = rbac_context.scope
    
    if scope_level == "all":
        # SUPER_ADMIN - no filtering, see all employees
        return query
    
    if scope_level == "segment":
        # SEGMENT_HEAD - filter by segment (requires full join chain)
        if scope.segment_id is not None:
            return (query
                .join(Team, Employee.team_id == Team.team_id)
                .join(Project, Team.project_id == Project.project_id)
                .join(SubSegment, Project.sub_segment_id == SubSegment.sub_segment_id)
                .filter(SubSegment.segment_id == scope.segment_id))
        else:
            logger.warning("SEGMENT_HEAD role without segment_id scope - returning empty result")
            return query.filter(False)
    
    if scope_level == "sub_segment":
        # SUBSEGMENT_HEAD - filter by sub_segment (join through team->project)
        if scope.sub_segment_id is not None:
            return (query
                .join(Team, Employee.team_id == Team.team_id)
                .join(Project, Team.project_id == Project.project_id)
                .filter(Project.sub_segment_id == scope.sub_segment_id))
        else:
            logger.warning("SUBSEGMENT_HEAD role without sub_segment_id scope - returning empty result")
            return query.filter(False)
    
    if scope_level == "project":
        # PROJECT_MANAGER - filter by project (join through team)
        if scope.project_id is not None:
            return (query
                .join(Team, Employee.team_id == Team.team_id)
                .filter(Team.project_id == scope.project_id))
        else:
            logger.warning("PROJECT_MANAGER role without project_id scope - returning empty result")
            return query.filter(False)
    
    if scope_level == "team":
        # TEAM_LEAD or TEAM_MEMBER - filter by team (direct FK)
        if scope.team_id is not None:
            return query.filter(Employee.team_id == scope.team_id)
        else:
            logger.warning("TEAM_LEAD/TEAM_MEMBER role without team_id scope - returning empty result")
            return query.filter(False)
    
    # Unknown scope level - default to no results for safety
    logger.warning(f"Unknown RBAC scope_level '{scope_level}' - returning empty result")
    return query.filter(False)


def _get_skills_count(db: Session, employee_id: int) -> int:
    """
    Count skills for a specific employee.
    Returns 0 if no skills found.
    """
    count = db.query(func.count(EmployeeSkill.emp_skill_id)).filter(
        EmployeeSkill.employee_id == employee_id
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_employee_responses(
    db: Session,
    employees: List[Employee]
) -> List[EmployeeResponse]:
    """
    Build EmployeeResponse list from employee models.
    Queries skills count for each employee.
    """
    response_items = []
    
    for employee in employees:
        skills_count = _get_skills_count(db, employee.employee_id)
        
        employee_data = EmployeeResponse(
            employee_id=employee.employee_id,
            zid=employee.zid,
            full_name=employee.full_name,
            role=employee.role,
            start_date_of_working=employee.start_date_of_working,
            organization=_build_organization_info(employee),
            skills_count=skills_count
        )
        response_items.append(employee_data)
    
    return response_items


def _build_organization_info(employee: Employee) -> OrganizationInfo:
    """
    Build OrganizationInfo from employee relationships.
    Pure function - no DB access.
    
    NORMALIZED SCHEMA: Derives sub_segment/project via team relationship.
    Returns empty strings for missing relationships to preserve API contract.
    """
    team = employee.team
    project = team.project if team else None
    sub_segment = project.sub_segment if project else None
    
    return OrganizationInfo(
        sub_segment=sub_segment.sub_segment_name if sub_segment else "",
        project=project.project_name if project else "",
        team=team.team_name if team else ""
    )
