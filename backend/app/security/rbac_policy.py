"""
RBAC (Role-Based Access Control) Policy Module

This module implements role-based access control for the Data Management endpoints.
It provides:
- Role definitions and permissions
- FastAPI dependency for extracting RBAC context from request headers
- Data filtering utilities based on user scope

TEMPORARY IMPLEMENTATION:
Currently reads roles from HTTP headers (X-RBAC-Role, X-RBAC-Scope-*).
Once authentication is implemented, this should read from JWT tokens instead.

REPLACE WITH JWT:
1. Decode JWT from Authorization header
2. Extract role and scope from token claims
3. Remove header-based fallbacks
"""

from enum import Enum
from typing import Optional, List, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from fastapi import Header
from sqlalchemy.orm import Query

if TYPE_CHECKING:
    from app.models import Team, Project, SubSegment


class Role(str, Enum):
    """
    Available roles in the system.
    Maps to RBAC_ROLES in frontend/src/config/featureFlags.js
    """
    SUPER_ADMIN = "SUPER_ADMIN"
    SEGMENT_HEAD = "SEGMENT_HEAD"
    SUBSEGMENT_HEAD = "SUBSEGMENT_HEAD"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TEAM_LEAD = "TEAM_LEAD"
    TEAM_MEMBER = "TEAM_MEMBER"


@dataclass
class Permission:
    """
    Permission flags for a role.
    """
    can_view: bool = True
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
    scope_level: str = "all"  # 'all', 'segment', 'sub_segment', 'project', 'team'
    self_only: bool = False   # For TEAM_MEMBER: CRUD restricted to own record


# Role to Permission mapping
ROLE_PERMISSIONS: dict[Role, Permission] = {
    Role.SUPER_ADMIN: Permission(
        can_view=True,
        can_create=True,
        can_update=True,
        can_delete=True,
        scope_level="all"
    ),
    Role.SEGMENT_HEAD: Permission(
        can_view=True,
        can_create=False,
        can_update=False,
        can_delete=False,
        scope_level="segment"
    ),
    Role.SUBSEGMENT_HEAD: Permission(
        can_view=True,
        can_create=False,
        can_update=False,
        can_delete=False,
        scope_level="sub_segment"
    ),
    Role.PROJECT_MANAGER: Permission(
        can_view=True,
        can_create=True,
        can_update=True,
        can_delete=True,
        scope_level="project"
    ),
    Role.TEAM_LEAD: Permission(
        can_view=True,
        can_create=True,
        can_update=True,
        can_delete=True,
        scope_level="team"
    ),
    Role.TEAM_MEMBER: Permission(
        can_view=True,
        can_create=True,
        can_update=True,
        can_delete=True,
        scope_level="team",
        self_only=True  # CRUD restricted to own employee record
    ),
}


@dataclass
class Scope:
    """
    User's organizational scope context.
    Defines what data segments the user can access.
    """
    segment_id: Optional[int] = None
    sub_segment_id: Optional[int] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    employee_id: Optional[int] = None  # User's own employee ID (for self-only CRUD)


@dataclass
class RbacContext:
    """
    Complete RBAC context for a request.
    Contains role, scope, and resolved permissions.
    """
    role: Role
    scope: Scope
    permissions: Permission
    
    def can_view(self) -> bool:
        return self.permissions.can_view
    
    def can_create(self, target_employee_id: Optional[int] = None) -> bool:
        if not self.permissions.can_create:
            return False
        if self.permissions.self_only and target_employee_id:
            return target_employee_id == self.scope.employee_id
        return True
    
    def can_update(self, target_employee_id: Optional[int] = None) -> bool:
        if not self.permissions.can_update:
            return False
        if self.permissions.self_only and target_employee_id:
            return target_employee_id == self.scope.employee_id
        return True
    
    def can_delete(self, target_employee_id: Optional[int] = None) -> bool:
        if not self.permissions.can_delete:
            return False
        if self.permissions.self_only and target_employee_id:
            return target_employee_id == self.scope.employee_id
        return True


async def get_rbac_context(
    x_rbac_role: Optional[str] = Header(None, alias="X-RBAC-Role"),
    x_rbac_scope_segment: Optional[str] = Header(None, alias="X-RBAC-Scope-Segment"),
    x_rbac_scope_sub_segment: Optional[str] = Header(None, alias="X-RBAC-Scope-SubSegment"),
    x_rbac_scope_project: Optional[str] = Header(None, alias="X-RBAC-Scope-Project"),
    x_rbac_scope_team: Optional[str] = Header(None, alias="X-RBAC-Scope-Team"),
    x_rbac_scope_employee: Optional[str] = Header(None, alias="X-RBAC-Scope-Employee"),
) -> RbacContext:
    """
    FastAPI dependency to extract RBAC context from request headers.
    
    Headers expected:
      - X-RBAC-Role: Role name (e.g., "SUPER_ADMIN", "TEAM_LEAD")
      - X-RBAC-Scope-Segment: Segment ID (optional)
      - X-RBAC-Scope-SubSegment: Sub-segment ID (optional)
      - X-RBAC-Scope-Project: Project ID (optional)
      - X-RBAC-Scope-Team: Team ID (optional)
      - X-RBAC-Scope-Employee: Employee ID (optional, for self-only CRUD)
    
    Returns:
        RbacContext with role, scope, and resolved permissions.
    
    TEMPORARY: Defaults to SUPER_ADMIN if no role header provided.
    In production with JWT, should reject or default to lowest privilege.
    """
    # Parse role, default to SUPER_ADMIN for development
    try:
        role = Role(x_rbac_role) if x_rbac_role else Role.SUPER_ADMIN
    except ValueError:
        role = Role.SUPER_ADMIN
    
    # Parse scope IDs (convert to int, handle None/invalid)
    def parse_int(val: Optional[str]) -> Optional[int]:
        if val is None or val == "null" or val == "":
            return None
        try:
            return int(val)
        except ValueError:
            return None
    
    scope = Scope(
        segment_id=parse_int(x_rbac_scope_segment),
        sub_segment_id=parse_int(x_rbac_scope_sub_segment),
        project_id=parse_int(x_rbac_scope_project),
        team_id=parse_int(x_rbac_scope_team),
        employee_id=parse_int(x_rbac_scope_employee),
    )
    
    # Get permissions for role
    permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS[Role.TEAM_MEMBER])
    
    return RbacContext(
        role=role,
        scope=scope,
        permissions=permissions
    )


def apply_employee_scope_filter(
    query: Query,
    employee_model: Any,
    rbac_context: RbacContext
) -> Query:
    """
    Apply RBAC scope filtering to an Employee query.
    
    This function modifies the query to only return employees the user is allowed to see
    based on their role and scope.
    
    NORMALIZED SCHEMA (HYBRID pattern):
    - Employee.team_id is the only direct FK (source of truth)
    - segment/sub_segment/project derived via joins: team -> project -> sub_segment -> segment
    - For scope levels above team, joins are added to navigate the hierarchy
    
    Args:
        query: SQLAlchemy query object
        employee_model: The Employee SQLAlchemy model class
        rbac_context: Current user's RBAC context
    
    Returns:
        Modified query with appropriate scope filters applied.
    
    Scope filtering logic:
        - SUPER_ADMIN: No filter (sees all)
        - SEGMENT_HEAD: Join to SubSegment, filter by segment_id
        - SUBSEGMENT_HEAD: Join to Project, filter by sub_segment_id
        - PROJECT_MANAGER: Join to Team, filter by project_id
        - TEAM_LEAD: Filter by team_id directly
        - TEAM_MEMBER: Filter by team_id (view) but track self for CRUD
    """
    # Import here to avoid circular imports
    from app.models import Team, Project, SubSegment
    
    scope_level = rbac_context.permissions.scope_level
    scope = rbac_context.scope
    
    if scope_level == "all":
        # SUPER_ADMIN - no filtering
        return query
    
    if scope_level == "segment" and scope.segment_id is not None:
        # SEGMENT_HEAD - join through team -> project -> sub_segment, filter by segment
        # Employee.team_id -> Team.project_id -> Project.sub_segment_id -> SubSegment.segment_id
        return (query
            .join(Team, employee_model.team_id == Team.team_id)
            .join(Project, Team.project_id == Project.project_id)
            .join(SubSegment, Project.sub_segment_id == SubSegment.sub_segment_id)
            .filter(SubSegment.segment_id == scope.segment_id))
    
    if scope_level == "sub_segment" and scope.sub_segment_id is not None:
        # SUBSEGMENT_HEAD - join through team -> project, filter by sub_segment
        return (query
            .join(Team, employee_model.team_id == Team.team_id)
            .join(Project, Team.project_id == Project.project_id)
            .filter(Project.sub_segment_id == scope.sub_segment_id))
    
    if scope_level == "project" and scope.project_id is not None:
        # PROJECT_MANAGER - join through team, filter by project
        return (query
            .join(Team, employee_model.team_id == Team.team_id)
            .filter(Team.project_id == scope.project_id))
    
    if scope_level == "team" and scope.team_id is not None:
        # TEAM_LEAD or TEAM_MEMBER - filter by team directly
        return query.filter(employee_model.team_id == scope.team_id)
    
    # If scope level requires a filter but scope ID is missing,
    # return empty result for safety (prevent data leakage)
    if scope_level != "all":
        # Filter that matches nothing
        return query.filter(False)
    
    return query


def check_crud_permission(
    rbac_context: RbacContext,
    action: str,
    target_employee_id: Optional[int] = None
) -> bool:
    """
    Check if the current user can perform a CRUD action.
    
    Args:
        rbac_context: Current user's RBAC context
        action: 'create', 'update', or 'delete'
        target_employee_id: The employee ID being operated on (for self-only check)
    
    Returns:
        True if action is permitted, False otherwise.
    """
    if action == "view":
        return rbac_context.can_view()
    elif action == "create":
        return rbac_context.can_create(target_employee_id)
    elif action == "update":
        return rbac_context.can_update(target_employee_id)
    elif action == "delete":
        return rbac_context.can_delete(target_employee_id)
    else:
        return False
