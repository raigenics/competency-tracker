"""
Dashboard Section: Role Distribution

SERVICE LAYER for computing role distribution data across organizational hierarchy.

PUBLIC ENTRYPOINT:
- get_role_distribution(db, segment_id, sub_segment_id, project_id, team_id, top_n, max_roles, include_empty)
  -> RoleDistributionResult

CONTEXT RESOLUTION:
- No sub_segment_id => SEGMENT context (breakdown = sub_segments in segment)
- sub_segment_id provided, no project_id => SUB_SEGMENT context (breakdown = projects)
- sub_segment_id + project_id, no team_id => PROJECT context (breakdown = teams)
- All provided => TEAM context (single breakdown row)

ISOLATION:
- This file is self-contained and does NOT import from other dashboard sections.
- Changes here must NOT affect other dashboard sections.
"""
from typing import Dict, Any, List, Optional, Tuple, Literal
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.models.employee import Employee
from app.models.role import Role
from app.models.team import Team
from app.models.project import Project
from app.models.sub_segment import SubSegment
from app.models.segment import Segment


# =============================================================================
# TYPES & DATACLASSES
# =============================================================================

ContextLevel = Literal["SEGMENT", "SUB_SEGMENT", "PROJECT", "TEAM"]
BreakdownLabel = Literal["Sub-Segment", "Project", "Team"]


@dataclass
class RoleCountData:
    """Internal data for role count."""
    role_id: int
    role_name: str
    employee_count: int


@dataclass
class BreakdownRowData:
    """Internal data for a breakdown row."""
    breakdown_id: int
    breakdown_name: str
    total_employees: int = 0
    roles: List[RoleCountData] = field(default_factory=list)


@dataclass
class ScopeData:
    """Internal data for scope context."""
    segment_id: int
    segment_name: str
    sub_segment_id: Optional[int] = None
    sub_segment_name: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None


@dataclass
class RoleDistributionResult:
    """Final result from the service."""
    context_level: ContextLevel
    title: str
    subtitle: str
    breakdown_label: BreakdownLabel
    scope: ScopeData
    rows: List[BreakdownRowData]


# =============================================================================
# EXCEPTIONS
# =============================================================================

class InvalidHierarchyError(ValueError):
    """Raised when provided IDs don't form valid hierarchy."""
    pass


class EntityNotFoundError(ValueError):
    """Raised when an entity is not found or is soft-deleted."""
    pass


# =============================================================================
# MAIN PUBLIC ENTRYPOINT
# =============================================================================

def get_role_distribution(
    db: Session,
    segment_id: int,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    top_n: int = 3,
    max_roles: int = 10,
    include_empty: bool = True
) -> RoleDistributionResult:
    """
    Get role distribution data for the dashboard section.
    
    Args:
        db: Database session
        segment_id: Required segment ID (always needed)
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
        top_n: Number of top roles for inline chips (default 3)
        max_roles: Maximum roles to return in all_roles (default 10)
        include_empty: Include breakdown items with zero employees (default True)
    
    Returns:
        RoleDistributionResult with all data needed for UI
    
    Raises:
        EntityNotFoundError: If segment/sub_segment/project/team not found
        InvalidHierarchyError: If IDs don't form valid hierarchy chain
    """
    # Step 1: Validate hierarchy and build scope
    scope = _validate_and_build_scope(
        db, segment_id, sub_segment_id, project_id, team_id
    )
    
    # Step 2: Resolve context level
    context_level = _resolve_context_level(sub_segment_id, project_id, team_id)
    
    # Step 3: Build title and subtitle
    title = _build_title(context_level, scope)
    subtitle = _build_subtitle(context_level)
    breakdown_label = _get_breakdown_label(context_level)
    
    # Step 4: Get breakdown entities (sub_segments/projects/teams)
    breakdown_entities = _get_breakdown_entities(
        db, context_level, segment_id, sub_segment_id, project_id, team_id
    )
    
    # Step 5: Get role aggregates
    role_aggregates = _get_role_aggregates(
        db, context_level, segment_id, sub_segment_id, project_id, team_id
    )
    
    # Step 6: Build rows by merging entities with aggregates
    rows = _build_rows(
        breakdown_entities, role_aggregates, top_n, max_roles, include_empty
    )
    
    return RoleDistributionResult(
        context_level=context_level,
        title=title,
        subtitle=subtitle,
        breakdown_label=breakdown_label,
        scope=scope,
        rows=rows
    )


# =============================================================================
# HELPER: VALIDATE HIERARCHY & BUILD SCOPE
# =============================================================================

def _validate_and_build_scope(
    db: Session,
    segment_id: int,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> ScopeData:
    """
    Validate that provided IDs form a valid hierarchy and build scope data.
    
    Validation chain:
    - segment must exist and not be deleted
    - sub_segment (if provided) must exist, not deleted, and belong to segment
    - project (if provided) must exist, not deleted, and belong to sub_segment
    - team (if provided) must exist, not deleted, and belong to project
    
    Raises:
        EntityNotFoundError: If any entity not found or deleted
        InvalidHierarchyError: If hierarchy chain is broken
    """
    # Validate segment
    segment = db.query(Segment).filter(
        Segment.segment_id == segment_id,
        Segment.deleted_at.is_(None)
    ).first()
    
    if not segment:
        raise EntityNotFoundError(f"Segment with ID {segment_id} not found or deleted")
    
    scope = ScopeData(
        segment_id=segment.segment_id,
        segment_name=segment.segment_name
    )
    
    # Validate sub_segment if provided
    if sub_segment_id is not None:
        sub_segment = db.query(SubSegment).filter(
            SubSegment.sub_segment_id == sub_segment_id,
            SubSegment.deleted_at.is_(None)
        ).first()
        
        if not sub_segment:
            raise EntityNotFoundError(f"Sub-segment with ID {sub_segment_id} not found or deleted")
        
        if sub_segment.segment_id != segment_id:
            raise InvalidHierarchyError(
                f"Sub-segment {sub_segment_id} does not belong to segment {segment_id}"
            )
        
        scope.sub_segment_id = sub_segment.sub_segment_id
        scope.sub_segment_name = sub_segment.sub_segment_name
    
    # Validate project if provided
    if project_id is not None:
        if sub_segment_id is None:
            raise InvalidHierarchyError("project_id requires sub_segment_id")
        
        project = db.query(Project).filter(
            Project.project_id == project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found or deleted")
        
        if project.sub_segment_id != sub_segment_id:
            raise InvalidHierarchyError(
                f"Project {project_id} does not belong to sub-segment {sub_segment_id}"
            )
        
        scope.project_id = project.project_id
        scope.project_name = project.project_name
    
    # Validate team if provided
    if team_id is not None:
        if project_id is None:
            raise InvalidHierarchyError("team_id requires project_id")
        
        team = db.query(Team).filter(
            Team.team_id == team_id,
            Team.deleted_at.is_(None)
        ).first()
        
        if not team:
            raise EntityNotFoundError(f"Team with ID {team_id} not found or deleted")
        
        if team.project_id != project_id:
            raise InvalidHierarchyError(
                f"Team {team_id} does not belong to project {project_id}"
            )
        
        scope.team_id = team.team_id
        scope.team_name = team.team_name
    
    return scope


# =============================================================================
# HELPER: RESOLVE CONTEXT LEVEL
# =============================================================================

def _resolve_context_level(
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> ContextLevel:
    """
    Determine context level from filter parameters.
    
    Rules:
    - No sub_segment_id => SEGMENT (breakdown by sub-segments)
    - sub_segment_id, no project_id => SUB_SEGMENT (breakdown by projects)
    - sub_segment_id + project_id, no team_id => PROJECT (breakdown by teams)
    - All provided => TEAM (single team row)
    """
    if sub_segment_id is None:
        return "SEGMENT"
    if project_id is None:
        return "SUB_SEGMENT"
    if team_id is None:
        return "PROJECT"
    return "TEAM"


# =============================================================================
# HELPER: BUILD TITLE & SUBTITLE
# =============================================================================

def _build_title(context_level: ContextLevel, scope: ScopeData) -> str:
    """
    Build dynamic title based on context level.
    
    Titles:
    - SEGMENT: "Role Distribution by Segment {segment_name}"
    - SUB_SEGMENT: "Role Distribution by Sub-Segment {sub_segment_name}"
    - PROJECT: "Role Distribution by Sub-Segment → Project {project_name}"
    - TEAM: "Role Distribution by Sub-Segment → Project → Team {team_name}"
    """
    if context_level == "SEGMENT":
        return f"Role Distribution by Segment {scope.segment_name}"
    elif context_level == "SUB_SEGMENT":
        return f"Role Distribution by Sub-Segment {scope.sub_segment_name}"
    elif context_level == "PROJECT":
        return f"Role Distribution by Sub-Segment → Project {scope.project_name}"
    else:  # TEAM
        return f"Role Distribution by Sub-Segment → Project → Team {scope.team_name}"


def _build_subtitle(context_level: ContextLevel) -> str:
    """
    Build dynamic subtitle based on context level.
    
    Subtitles:
    - SEGMENT: "Employee count by role across Sub-Segments"
    - SUB_SEGMENT: "Employee count by role across Projects"
    - PROJECT: "Employee count by role across Teams"
    - TEAM: "Employee count by role across Employees"
    """
    breakdown_map = {
        "SEGMENT": "Sub-Segments",
        "SUB_SEGMENT": "Projects",
        "PROJECT": "Teams",
        "TEAM": "Employees"
    }
    return f"Employee count by role across {breakdown_map[context_level]}"


def _get_breakdown_label(context_level: ContextLevel) -> BreakdownLabel:
    """Get the first column header label based on context level."""
    label_map: Dict[ContextLevel, BreakdownLabel] = {
        "SEGMENT": "Sub-Segment",
        "SUB_SEGMENT": "Project",
        "PROJECT": "Team",
        "TEAM": "Team"
    }
    return label_map[context_level]


# =============================================================================
# HELPER: GET BREAKDOWN ENTITIES
# =============================================================================

def _get_breakdown_entities(
    db: Session,
    context_level: ContextLevel,
    segment_id: int,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> List[Tuple[int, str]]:
    """
    Get breakdown entities (id, name) for the current context.
    
    Returns:
        List of (breakdown_id, breakdown_name) tuples
    
    Example for SEGMENT context:
        Returns all sub_segments under the segment: [(1, "ADT"), (2, "AU"), ...]
    """
    if context_level == "SEGMENT":
        # Get sub-segments under segment
        results = db.query(
            SubSegment.sub_segment_id,
            SubSegment.sub_segment_name
        ).filter(
            SubSegment.segment_id == segment_id,
            SubSegment.deleted_at.is_(None)
        ).order_by(SubSegment.sub_segment_name).all()
        
        return [(r.sub_segment_id, r.sub_segment_name) for r in results]
    
    elif context_level == "SUB_SEGMENT":
        # Get projects under sub-segment
        results = db.query(
            Project.project_id,
            Project.project_name
        ).filter(
            Project.sub_segment_id == sub_segment_id,
            Project.deleted_at.is_(None)
        ).order_by(Project.project_name).all()
        
        return [(r.project_id, r.project_name) for r in results]
    
    elif context_level == "PROJECT":
        # Get teams under project
        results = db.query(
            Team.team_id,
            Team.team_name
        ).filter(
            Team.project_id == project_id,
            Team.deleted_at.is_(None)
        ).order_by(Team.team_name).all()
        
        return [(r.team_id, r.team_name) for r in results]
    
    else:  # TEAM
        # Single team
        team = db.query(
            Team.team_id,
            Team.team_name
        ).filter(
            Team.team_id == team_id,
            Team.deleted_at.is_(None)
        ).first()
        
        return [(team.team_id, team.team_name)] if team else []


# =============================================================================
# HELPER: GET ROLE AGGREGATES
# =============================================================================

def _get_role_aggregates(
    db: Session,
    context_level: ContextLevel,
    segment_id: int,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> Dict[int, List[Tuple[int, str, int]]]:
    """
    Get role aggregates grouped by breakdown entity.
    
    Returns:
        Dict mapping breakdown_id -> List of (role_id, role_name, count)
        Already sorted by count descending within each breakdown.
    """
    # Build base query with proper joins
    # employees -> teams -> projects -> sub_segments -> segments
    # employees -> roles
    
    if context_level == "SEGMENT":
        # Group by sub_segment + role
        query = db.query(
            SubSegment.sub_segment_id.label("breakdown_id"),
            Role.role_id,
            Role.role_name,
            func.count(Employee.employee_id).label("emp_count")
        ).select_from(Employee).join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Project, Team.project_id == Project.project_id
        ).join(
            SubSegment, Project.sub_segment_id == SubSegment.sub_segment_id
        ).join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            SubSegment.segment_id == segment_id,
            Employee.deleted_at.is_(None),
            Team.deleted_at.is_(None),
            Project.deleted_at.is_(None),
            SubSegment.deleted_at.is_(None),
            Role.deleted_at.is_(None)
        ).group_by(
            SubSegment.sub_segment_id,
            Role.role_id,
            Role.role_name
        ).order_by(
            SubSegment.sub_segment_id,
            func.count(Employee.employee_id).desc()
        )
    
    elif context_level == "SUB_SEGMENT":
        # Group by project + role
        query = db.query(
            Project.project_id.label("breakdown_id"),
            Role.role_id,
            Role.role_name,
            func.count(Employee.employee_id).label("emp_count")
        ).select_from(Employee).join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Project, Team.project_id == Project.project_id
        ).join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            Project.sub_segment_id == sub_segment_id,
            Employee.deleted_at.is_(None),
            Team.deleted_at.is_(None),
            Project.deleted_at.is_(None),
            Role.deleted_at.is_(None)
        ).group_by(
            Project.project_id,
            Role.role_id,
            Role.role_name
        ).order_by(
            Project.project_id,
            func.count(Employee.employee_id).desc()
        )
    
    elif context_level == "PROJECT":
        # Group by team + role
        query = db.query(
            Team.team_id.label("breakdown_id"),
            Role.role_id,
            Role.role_name,
            func.count(Employee.employee_id).label("emp_count")
        ).select_from(Employee).join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            Team.project_id == project_id,
            Employee.deleted_at.is_(None),
            Team.deleted_at.is_(None),
            Role.deleted_at.is_(None)
        ).group_by(
            Team.team_id,
            Role.role_id,
            Role.role_name
        ).order_by(
            Team.team_id,
            func.count(Employee.employee_id).desc()
        )
    
    else:  # TEAM
        # Group by team (single) + role
        query = db.query(
            Team.team_id.label("breakdown_id"),
            Role.role_id,
            Role.role_name,
            func.count(Employee.employee_id).label("emp_count")
        ).select_from(Employee).join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            Team.team_id == team_id,
            Employee.deleted_at.is_(None),
            Team.deleted_at.is_(None),
            Role.deleted_at.is_(None)
        ).group_by(
            Team.team_id,
            Role.role_id,
            Role.role_name
        ).order_by(
            Team.team_id,
            func.count(Employee.employee_id).desc()
        )
    
    # Execute query and build result dict
    results = query.all()
    
    aggregates: Dict[int, List[Tuple[int, str, int]]] = {}
    for row in results:
        breakdown_id = row.breakdown_id
        if breakdown_id not in aggregates:
            aggregates[breakdown_id] = []
        aggregates[breakdown_id].append((row.role_id, row.role_name, row.emp_count))
    
    return aggregates


# =============================================================================
# HELPER: BUILD ROWS
# =============================================================================

def _build_rows(
    breakdown_entities: List[Tuple[int, str]],
    role_aggregates: Dict[int, List[Tuple[int, str, int]]],
    top_n: int,
    max_roles: int,
    include_empty: bool
) -> List[BreakdownRowData]:
    """
    Build final breakdown rows by merging entities with aggregates.
    
    Args:
        breakdown_entities: List of (id, name) for breakdown items
        role_aggregates: Dict of breakdown_id -> [(role_id, role_name, count), ...]
        top_n: Number of top roles to include
        max_roles: Maximum roles to return in all_roles
        include_empty: Include items with zero employees
    
    Returns:
        List of BreakdownRowData objects
    """
    rows = []
    
    for breakdown_id, breakdown_name in breakdown_entities:
        # Get aggregates for this breakdown (already sorted by count desc)
        aggregates = role_aggregates.get(breakdown_id, [])
        
        # Calculate total employees
        total_employees = sum(count for _, _, count in aggregates)
        
        # Skip empty rows if include_empty is False
        if not include_empty and total_employees == 0:
            continue
        
        # Build role count objects
        all_role_counts = [
            RoleCountData(
                role_id=role_id,
                role_name=role_name,
                employee_count=count
            )
            for role_id, role_name, count in aggregates[:max_roles]
        ]
        
        # Top N roles
        top_roles = all_role_counts[:top_n]
        
        # More roles count (roles beyond top_n but within max_roles)
        more_roles_count = max(0, len(all_role_counts) - top_n)
        
        rows.append(BreakdownRowData(
            breakdown_id=breakdown_id,
            breakdown_name=breakdown_name,
            total_employees=total_employees,
            roles=all_role_counts
        ))
    
    return rows


# =============================================================================
# UTILITY: CONVERT RESULT TO DICT (for API response)
# =============================================================================

def result_to_dict(result: RoleDistributionResult, top_n: int = 3) -> Dict[str, Any]:
    """
    Convert RoleDistributionResult to dictionary for API response.
    
    This function transforms the internal dataclasses to the exact
    shape expected by the Pydantic response schema.
    """
    return {
        "context_level": result.context_level,
        "title": result.title,
        "subtitle": result.subtitle,
        "breakdown_label": result.breakdown_label,
        "scope": {
            "segment_id": result.scope.segment_id,
            "segment_name": result.scope.segment_name,
            "sub_segment_id": result.scope.sub_segment_id,
            "sub_segment_name": result.scope.sub_segment_name,
            "project_id": result.scope.project_id,
            "project_name": result.scope.project_name,
            "team_id": result.scope.team_id,
            "team_name": result.scope.team_name,
        },
        "rows": [
            {
                "breakdown_id": row.breakdown_id,
                "breakdown_name": row.breakdown_name,
                "total_employees": row.total_employees,
                "top_roles": [
                    {
                        "role_id": r.role_id,
                        "role_name": r.role_name,
                        "employee_count": r.employee_count
                    }
                    for r in row.roles[:top_n]
                ],
                "all_roles": [
                    {
                        "role_id": r.role_id,
                        "role_name": r.role_name,
                        "employee_count": r.employee_count
                    }
                    for r in row.roles
                ],
                "more_roles_count": max(0, len(row.roles) - top_n)
            }
            for row in result.rows
        ]
    }
