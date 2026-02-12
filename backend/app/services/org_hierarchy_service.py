"""
Service layer for Org Hierarchy operations.

Provides efficient retrieval of the full organizational hierarchy:
Segment → SubSegment → Project → Team

Uses 4 bulk queries + in-memory grouping to avoid N+1 queries.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.segment import Segment
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team
from app.models.employee import Employee
from app.schemas.org_hierarchy import (
    OrgHierarchyResponse,
    SegmentNode,
    SubSegmentNode,
    ProjectNode,
    TeamNode,
    SegmentCreateResponse,
    SubSegmentCreateResponse,
    ProjectCreateResponse,
    TeamCreateResponse,
    SegmentUpdateResponse,
    SubSegmentUpdateResponse,
    ProjectUpdateResponse,
    TeamUpdateResponse,
    DependencyConflictResponse,
)

logger = logging.getLogger(__name__)


def get_org_hierarchy(db: Session) -> OrgHierarchyResponse:
    """
    Retrieve the full org hierarchy with all segments, sub-segments, projects, and teams.
    
    Query Strategy:
    - 4 separate bulk queries (one per table) selecting only needed columns
    - In-memory grouping using dict maps for O(1) lookups
    - Avoids N+1 by not using ORM relationship lazy loading
    - Excludes soft-deleted records (deleted_at IS NULL)
    - Results sorted by name for deterministic response
    
    Args:
        db: Database session
        
    Returns:
        OrgHierarchyResponse with nested hierarchy and counts
    """
    # Query 1: All segments (not soft-deleted), sorted by name
    segments = (
        db.query(Segment.segment_id, Segment.segment_name)
        .filter(Segment.deleted_at.is_(None))
        .order_by(Segment.segment_name)
        .all()
    )
    
    # Query 2: All sub-segments (not soft-deleted), sorted by name
    sub_segments = (
        db.query(SubSegment.sub_segment_id, SubSegment.sub_segment_name, SubSegment.segment_id)
        .filter(SubSegment.deleted_at.is_(None))
        .order_by(SubSegment.sub_segment_name)
        .all()
    )
    
    # Query 3: All projects (not soft-deleted), sorted by name
    projects = (
        db.query(Project.project_id, Project.project_name, Project.sub_segment_id)
        .filter(Project.deleted_at.is_(None))
        .order_by(Project.project_name)
        .all()
    )
    
    # Query 4: All teams (not soft-deleted), sorted by name
    teams = (
        db.query(Team.team_id, Team.team_name, Team.project_id)
        .filter(Team.deleted_at.is_(None))
        .order_by(Team.team_name)
        .all()
    )
    
    # Build lookup maps for O(1) grouping
    # Teams grouped by project_id
    teams_by_project: Dict[int, List[TeamNode]] = defaultdict(list)
    for team in teams:
        teams_by_project[team.project_id].append(
            TeamNode(team_id=team.team_id, team_name=team.team_name)
        )
    
    # Projects grouped by sub_segment_id
    projects_by_subseg: Dict[int, List[ProjectNode]] = defaultdict(list)
    for project in projects:
        projects_by_subseg[project.sub_segment_id].append(
            ProjectNode(
                project_id=project.project_id,
                project_name=project.project_name,
                teams=teams_by_project.get(project.project_id, [])
            )
        )
    
    # Sub-segments grouped by segment_id
    subseg_by_segment: Dict[int, List[SubSegmentNode]] = defaultdict(list)
    for subseg in sub_segments:
        if subseg.segment_id is not None:  # Handle legacy records with NULL segment_id
            subseg_by_segment[subseg.segment_id].append(
                SubSegmentNode(
                    sub_segment_id=subseg.sub_segment_id,
                    sub_segment_name=subseg.sub_segment_name,
                    projects=projects_by_subseg.get(subseg.sub_segment_id, [])
                )
            )
    
    # Build final segment nodes
    segment_nodes: List[SegmentNode] = []
    for segment in segments:
        segment_nodes.append(
            SegmentNode(
                segment_id=segment.segment_id,
                segment_name=segment.segment_name,
                sub_segments=subseg_by_segment.get(segment.segment_id, [])
            )
        )
    
    # Log counts for debugging
    logger.debug(
        f"Org hierarchy loaded: segments={len(segments)}, "
        f"sub_segments={len(sub_segments)}, projects={len(projects)}, teams={len(teams)}"
    )
    
    return OrgHierarchyResponse(
        segments=segment_nodes,
        total_segments=len(segments),
        total_sub_segments=len(sub_segments),
        total_projects=len(projects),
        total_teams=len(teams)
    )


# =============================================================================
# SEGMENT CREATE
# =============================================================================

def create_segment(
    db: Session,
    segment_name: str,
    actor: Optional[str] = None
) -> SegmentCreateResponse:
    """
    Create a new segment.
    
    Args:
        db: Database session
        segment_name: Name for the new segment (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SegmentCreateResponse with created segment data
        
    Raises:
        ValueError: If name is invalid or already exists
    """
    logger.info(f"Creating segment '{segment_name}' by {actor}")
    
    # Validate input
    validated_name = segment_name.strip()
    if not validated_name:
        raise ValueError("Segment name cannot be empty")
    
    # Check for duplicate name (case-insensitive), excluding soft-deleted
    existing = db.query(Segment).filter(
        func.lower(Segment.segment_name) == validated_name.lower(),
        Segment.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Segment with name '{validated_name}' already exists")
    
    # Create new segment
    new_segment = Segment(
        segment_name=validated_name,
        created_by=actor or "system"
    )
    
    db.add(new_segment)
    db.commit()
    db.refresh(new_segment)
    
    logger.info(f"Segment created with id {new_segment.segment_id}: '{validated_name}'")
    
    return SegmentCreateResponse(
        segment_id=new_segment.segment_id,
        segment_name=new_segment.segment_name,
        created_at=new_segment.created_at,
        created_by=new_segment.created_by,
        message="Segment created successfully"
    )


# =============================================================================
# SUB-SEGMENT CREATE
# =============================================================================

def create_sub_segment(
    db: Session,
    segment_id: int,
    sub_segment_name: str,
    actor: Optional[str] = None
) -> SubSegmentCreateResponse:
    """
    Create a new sub-segment under a segment.
    
    Args:
        db: Database session
        segment_id: ID of the parent segment
        sub_segment_name: Name for the new sub-segment (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SubSegmentCreateResponse with created sub-segment data
        
    Raises:
        ValueError: If name is invalid, parent not found, or name already exists
    """
    logger.info(f"Creating sub-segment '{sub_segment_name}' under segment {segment_id} by {actor}")
    
    # Validate input
    validated_name = sub_segment_name.strip()
    if not validated_name:
        raise ValueError("Sub-segment name cannot be empty")
    
    # Check parent segment exists and is not soft-deleted
    parent_segment = db.query(Segment).filter(
        Segment.segment_id == segment_id,
        Segment.deleted_at.is_(None)
    ).first()
    
    if not parent_segment:
        raise ValueError(f"Parent segment with id {segment_id} not found")
    
    # Check for duplicate name (case-insensitive, globally unique per model constraint)
    existing = db.query(SubSegment).filter(
        func.lower(SubSegment.sub_segment_name) == validated_name.lower(),
        SubSegment.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Sub-segment with name '{validated_name}' already exists")
    
    # Create new sub-segment
    new_sub_segment = SubSegment(
        sub_segment_name=validated_name,
        segment_id=segment_id,
        created_by=actor or "system"
    )
    
    db.add(new_sub_segment)
    db.commit()
    db.refresh(new_sub_segment)
    
    logger.info(f"Sub-segment created with id {new_sub_segment.sub_segment_id}: '{validated_name}'")
    
    return SubSegmentCreateResponse(
        sub_segment_id=new_sub_segment.sub_segment_id,
        sub_segment_name=new_sub_segment.sub_segment_name,
        segment_id=new_sub_segment.segment_id,
        created_at=new_sub_segment.created_at,
        created_by=new_sub_segment.created_by,
        message="Sub-segment created successfully"
    )


# =============================================================================
# SEGMENT UPDATE
# =============================================================================

def update_segment(
    db: Session,
    segment_id: int,
    segment_name: str,
    actor: Optional[str] = None
) -> SegmentUpdateResponse:
    """
    Update a segment's name.
    
    Args:
        db: Database session
        segment_id: ID of the segment to update
        segment_name: New name for the segment (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SegmentUpdateResponse with updated segment data
        
    Raises:
        ValueError: If segment not found, name is invalid, or name already exists
    """
    logger.info(f"Updating segment {segment_id} to '{segment_name}' by {actor}")
    
    # Validate input
    validated_name = segment_name.strip()
    if not validated_name:
        raise ValueError("Segment name cannot be empty")
    
    # Find segment (not soft-deleted)
    segment = db.query(Segment).filter(
        Segment.segment_id == segment_id,
        Segment.deleted_at.is_(None)
    ).first()
    
    if not segment:
        raise ValueError(f"Segment with id {segment_id} not found")
    
    # Check for duplicate name (case-insensitive), excluding self and soft-deleted
    existing = db.query(Segment).filter(
        func.lower(Segment.segment_name) == validated_name.lower(),
        Segment.segment_id != segment_id,
        Segment.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Segment with name '{validated_name}' already exists")
    
    # Update segment
    segment.segment_name = validated_name
    
    db.commit()
    db.refresh(segment)
    
    logger.info(f"Segment {segment_id} updated to '{validated_name}'")
    
    return SegmentUpdateResponse(
        segment_id=segment.segment_id,
        segment_name=segment.segment_name,
        message="Segment updated successfully"
    )


# =============================================================================
# SUB-SEGMENT UPDATE
# =============================================================================

def update_sub_segment(
    db: Session,
    sub_segment_id: int,
    sub_segment_name: str,
    actor: Optional[str] = None
) -> SubSegmentUpdateResponse:
    """
    Update a sub-segment's name.
    
    Args:
        db: Database session
        sub_segment_id: ID of the sub-segment to update
        sub_segment_name: New name for the sub-segment (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SubSegmentUpdateResponse with updated sub-segment data
        
    Raises:
        ValueError: If sub-segment not found, name is invalid, or name already exists
    """
    logger.info(f"Updating sub-segment {sub_segment_id} to '{sub_segment_name}' by {actor}")
    
    # Validate input
    validated_name = sub_segment_name.strip()
    if not validated_name:
        raise ValueError("Sub-segment name cannot be empty")
    
    # Find sub-segment (not soft-deleted)
    sub_segment = db.query(SubSegment).filter(
        SubSegment.sub_segment_id == sub_segment_id,
        SubSegment.deleted_at.is_(None)
    ).first()
    
    if not sub_segment:
        raise ValueError(f"Sub-segment with id {sub_segment_id} not found")
    
    # Check for duplicate name (case-insensitive), excluding self and soft-deleted
    existing = db.query(SubSegment).filter(
        func.lower(SubSegment.sub_segment_name) == validated_name.lower(),
        SubSegment.sub_segment_id != sub_segment_id,
        SubSegment.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Sub-segment with name '{validated_name}' already exists")
    
    # Update sub-segment
    sub_segment.sub_segment_name = validated_name
    
    db.commit()
    db.refresh(sub_segment)
    
    logger.info(f"Sub-segment {sub_segment_id} updated to '{validated_name}'")
    
    return SubSegmentUpdateResponse(
        sub_segment_id=sub_segment.sub_segment_id,
        sub_segment_name=sub_segment.sub_segment_name,
        segment_id=sub_segment.segment_id,
        message="Sub-segment updated successfully"
    )


# =============================================================================
# PROJECT UPDATE
# =============================================================================

def update_project(
    db: Session,
    project_id: int,
    project_name: str,
    actor: Optional[str] = None
) -> ProjectUpdateResponse:
    """
    Update a project's name.
    
    Args:
        db: Database session
        project_id: ID of the project to update
        project_name: New name for the project (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        ProjectUpdateResponse with updated project data
        
    Raises:
        ValueError: If project not found, name is invalid, or name already exists
    """
    logger.info(f"Updating project {project_id} to '{project_name}' by {actor}")
    
    # Validate input
    validated_name = project_name.strip()
    if not validated_name:
        raise ValueError("Project name cannot be empty")
    
    # Find project (not soft-deleted)
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise ValueError(f"Project with id {project_id} not found")
    
    # Check for duplicate name (case-insensitive), excluding self and soft-deleted
    existing = db.query(Project).filter(
        func.lower(Project.project_name) == validated_name.lower(),
        Project.project_id != project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Project with name '{validated_name}' already exists")
    
    # Update project
    project.project_name = validated_name
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"Project {project_id} updated to '{validated_name}'")
    
    return ProjectUpdateResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        sub_segment_id=project.sub_segment_id,
        message="Project updated successfully"
    )


# =============================================================================
# TEAM UPDATE
# =============================================================================

def update_team(
    db: Session,
    team_id: int,
    team_name: str,
    actor: Optional[str] = None
) -> TeamUpdateResponse:
    """
    Update a team's name.
    
    Args:
        db: Database session
        team_id: ID of the team to update
        team_name: New name for the team (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        TeamUpdateResponse with updated team data
        
    Raises:
        ValueError: If team not found, name is invalid, or name already exists
    """
    logger.info(f"Updating team {team_id} to '{team_name}' by {actor}")
    
    # Validate input
    validated_name = team_name.strip()
    if not validated_name:
        raise ValueError("Team name cannot be empty")
    
    # Find team (not soft-deleted)
    team = db.query(Team).filter(
        Team.team_id == team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if not team:
        raise ValueError(f"Team with id {team_id} not found")
    
    # Check for duplicate name (case-insensitive), excluding self and soft-deleted
    existing = db.query(Team).filter(
        func.lower(Team.team_name) == validated_name.lower(),
        Team.team_id != team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Team with name '{validated_name}' already exists")
    
    # Update team
    team.team_name = validated_name
    
    db.commit()
    db.refresh(team)
    
    logger.info(f"Team {team_id} updated to '{validated_name}'")
    
    return TeamUpdateResponse(
        team_id=team.team_id,
        team_name=team.team_name,
        project_id=team.project_id,
        message="Team updated successfully"
    )


# =============================================================================
# SEGMENT DELETE (soft delete)
# =============================================================================

def get_segment_dependencies(db: Session, segment_id: int) -> Dict[str, int]:
    """
    Get counts of active (non-deleted) dependencies for a segment.
    
    Uses efficient COUNT queries with joins to avoid N+1.
    
    Args:
        db: Database session
        segment_id: Segment ID to check
        
    Returns:
        Dictionary with counts: { sub_segments, projects, teams }
    """
    # Count active sub-segments under this segment
    sub_segment_count = db.query(func.count(SubSegment.sub_segment_id)).filter(
        SubSegment.segment_id == segment_id,
        SubSegment.deleted_at.is_(None)
    ).scalar() or 0
    
    # Count active projects under sub-segments of this segment
    project_count = db.query(func.count(Project.project_id)).join(
        SubSegment, SubSegment.sub_segment_id == Project.sub_segment_id
    ).filter(
        SubSegment.segment_id == segment_id,
        SubSegment.deleted_at.is_(None),
        Project.deleted_at.is_(None)
    ).scalar() or 0
    
    # Count active teams under projects of sub-segments of this segment
    team_count = db.query(func.count(Team.team_id)).join(
        Project, Project.project_id == Team.project_id
    ).join(
        SubSegment, SubSegment.sub_segment_id == Project.sub_segment_id
    ).filter(
        SubSegment.segment_id == segment_id,
        SubSegment.deleted_at.is_(None),
        Project.deleted_at.is_(None),
        Team.deleted_at.is_(None)
    ).scalar() or 0
    
    return {
        "sub_segments": sub_segment_count,
        "projects": project_count,
        "teams": team_count
    }


def delete_segment(
    db: Session,
    segment_id: int,
    actor: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, int]]]:
    """
    Soft delete a segment.
    
    Args:
        db: Database session
        segment_id: ID of the segment to delete
        actor: Username of the user performing the action (for audit)
        
    Returns:
        Tuple of (success: bool, dependencies: dict or None)
        - (True, None) if deletion succeeded
        - (False, { sub_segments, projects, teams }) if dependencies exist
        
    Raises:
        ValueError: If segment not found or already deleted
    """
    logger.info(f"Attempting to delete segment {segment_id} by {actor}")
    
    # Find segment (not soft-deleted)
    segment = db.query(Segment).filter(
        Segment.segment_id == segment_id,
        Segment.deleted_at.is_(None)
    ).first()
    
    if not segment:
        raise ValueError(f"Segment with id {segment_id} not found")
    
    # Check for dependencies
    dependencies = get_segment_dependencies(db, segment_id)
    total_deps = sum(dependencies.values())
    
    if total_deps > 0:
        logger.info(f"Cannot delete segment {segment_id}: has {total_deps} dependencies")
        return (False, dependencies)
    
    # No dependencies - soft delete
    segment.deleted_at = datetime.now(timezone.utc)
    segment.deleted_by = actor or "system"
    
    db.commit()
    
    logger.info(f"Segment {segment_id} soft deleted by {actor}")
    return (True, None)


# =============================================================================
# SUB-SEGMENT DELETE (soft delete)
# =============================================================================

def get_sub_segment_dependencies(db: Session, sub_segment_id: int) -> Dict[str, int]:
    """
    Get counts of active (non-deleted) dependencies for a sub-segment.
    
    Uses efficient COUNT queries with joins to avoid N+1.
    
    Args:
        db: Database session
        sub_segment_id: Sub-segment ID to check
        
    Returns:
        Dictionary with counts: { projects, teams }
    """
    # Count active projects under this sub-segment
    project_count = db.query(func.count(Project.project_id)).filter(
        Project.sub_segment_id == sub_segment_id,
        Project.deleted_at.is_(None)
    ).scalar() or 0
    
    # Count active teams under projects of this sub-segment
    team_count = db.query(func.count(Team.team_id)).join(
        Project, Project.project_id == Team.project_id
    ).filter(
        Project.sub_segment_id == sub_segment_id,
        Project.deleted_at.is_(None),
        Team.deleted_at.is_(None)
    ).scalar() or 0
    
    return {
        "projects": project_count,
        "teams": team_count
    }


def delete_sub_segment(
    db: Session,
    sub_segment_id: int,
    actor: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, int]]]:
    """
    Soft delete a sub-segment.
    
    Args:
        db: Database session
        sub_segment_id: ID of the sub-segment to delete
        actor: Username of the user performing the action (for audit)
        
    Returns:
        Tuple of (success: bool, dependencies: dict or None)
        - (True, None) if deletion succeeded
        - (False, { projects, teams }) if dependencies exist
        
    Raises:
        ValueError: If sub-segment not found or already deleted
    """
    logger.info(f"Attempting to delete sub-segment {sub_segment_id} by {actor}")
    
    # Find sub-segment (not soft-deleted)
    sub_segment = db.query(SubSegment).filter(
        SubSegment.sub_segment_id == sub_segment_id,
        SubSegment.deleted_at.is_(None)
    ).first()
    
    if not sub_segment:
        raise ValueError(f"Sub-segment with id {sub_segment_id} not found")
    
    # Check for dependencies
    dependencies = get_sub_segment_dependencies(db, sub_segment_id)
    total_deps = sum(dependencies.values())
    
    if total_deps > 0:
        logger.info(f"Cannot delete sub-segment {sub_segment_id}: has {total_deps} dependencies")
        return (False, dependencies)
    
    # No dependencies - soft delete
    sub_segment.deleted_at = datetime.now(timezone.utc)
    sub_segment.deleted_by = actor or "system"
    
    db.commit()
    
    logger.info(f"Sub-segment {sub_segment_id} soft deleted by {actor}")
    return (True, None)


# =============================================================================
# PROJECT CREATE
# =============================================================================

def create_project(
    db: Session,
    sub_segment_id: int,
    project_name: str,
    actor: Optional[str] = None
) -> ProjectCreateResponse:
    """
    Create a new project under a sub-segment.
    
    Args:
        db: Database session
        sub_segment_id: ID of the parent sub-segment
        project_name: Name for the new project (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        ProjectCreateResponse with created project data
        
    Raises:
        ValueError: If name is invalid, parent not found, or name already exists
    """
    logger.info(f"Creating project '{project_name}' under sub-segment {sub_segment_id} by {actor}")
    
    # Validate input
    validated_name = project_name.strip()
    if not validated_name:
        raise ValueError("Project name cannot be empty")
    
    # Check parent sub-segment exists and is not soft-deleted
    parent_sub_segment = db.query(SubSegment).filter(
        SubSegment.sub_segment_id == sub_segment_id,
        SubSegment.deleted_at.is_(None)
    ).first()
    
    if not parent_sub_segment:
        raise ValueError(f"Parent sub-segment with id {sub_segment_id} not found")
    
    # Check for duplicate name within the same sub-segment (case-insensitive)
    existing = db.query(Project).filter(
        func.lower(Project.project_name) == validated_name.lower(),
        Project.sub_segment_id == sub_segment_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Project with name '{validated_name}' already exists in this sub-segment")
    
    # Create new project
    new_project = Project(
        project_name=validated_name,
        sub_segment_id=sub_segment_id,
        created_by=actor or "system"
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    logger.info(f"Project created with id {new_project.project_id}: '{validated_name}'")
    
    return ProjectCreateResponse(
        project_id=new_project.project_id,
        project_name=new_project.project_name,
        sub_segment_id=new_project.sub_segment_id,
        created_at=new_project.created_at,
        created_by=new_project.created_by,
        message="Project created successfully"
    )


# =============================================================================
# TEAM CREATE
# =============================================================================

def create_team(
    db: Session,
    project_id: int,
    team_name: str,
    actor: Optional[str] = None
) -> TeamCreateResponse:
    """
    Create a new team under a project.
    
    Args:
        db: Database session
        project_id: ID of the parent project
        team_name: Name for the new team (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        TeamCreateResponse with created team data
        
    Raises:
        ValueError: If name is invalid, parent not found, or name already exists
    """
    logger.info(f"Creating team '{team_name}' under project {project_id} by {actor}")
    
    # Validate input
    validated_name = team_name.strip()
    if not validated_name:
        raise ValueError("Team name cannot be empty")
    
    # Check parent project exists and is not soft-deleted
    parent_project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not parent_project:
        raise ValueError(f"Parent project with id {project_id} not found")
    
    # Check for duplicate name within the same project (case-insensitive)
    existing = db.query(Team).filter(
        func.lower(Team.team_name) == validated_name.lower(),
        Team.project_id == project_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError(f"Team with name '{validated_name}' already exists in this project")
    
    # Create new team
    new_team = Team(
        team_name=validated_name,
        project_id=project_id,
        created_by=actor or "system"
    )
    
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    
    logger.info(f"Team created with id {new_team.team_id}: '{validated_name}'")
    
    return TeamCreateResponse(
        team_id=new_team.team_id,
        team_name=new_team.team_name,
        project_id=new_team.project_id,
        created_at=new_team.created_at,
        created_by=new_team.created_by,
        message="Team created successfully"
    )


# =============================================================================
# PROJECT DELETE (soft delete)
# =============================================================================

def get_project_dependencies(db: Session, project_id: int) -> Dict[str, int]:
    """
    Get counts of active (non-deleted) dependencies for a project.
    
    Args:
        db: Database session
        project_id: Project ID to check
        
    Returns:
        Dictionary with counts: { teams }
    """
    # Count active teams under this project
    team_count = db.query(func.count(Team.team_id)).filter(
        Team.project_id == project_id,
        Team.deleted_at.is_(None)
    ).scalar() or 0
    
    return {
        "teams": team_count
    }


def delete_project(
    db: Session,
    project_id: int,
    actor: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, int]]]:
    """
    Soft delete a project.
    
    Args:
        db: Database session
        project_id: ID of the project to delete
        actor: Username of the user performing the action (for audit)
        
    Returns:
        Tuple of (success: bool, dependencies: dict or None)
        - (True, None) if deletion succeeded
        - (False, { teams }) if dependencies exist
        
    Raises:
        ValueError: If project not found or already deleted
    """
    logger.info(f"Attempting to delete project {project_id} by {actor}")
    
    # Find project (not soft-deleted)
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise ValueError(f"Project with id {project_id} not found")
    
    # Check for dependencies
    dependencies = get_project_dependencies(db, project_id)
    total_deps = sum(dependencies.values())
    
    if total_deps > 0:
        logger.info(f"Cannot delete project {project_id}: has {total_deps} dependencies")
        return (False, dependencies)
    
    # No dependencies - soft delete
    project.deleted_at = datetime.now(timezone.utc)
    project.deleted_by = actor or "system"
    
    db.commit()
    
    logger.info(f"Project {project_id} soft deleted by {actor}")
    return (True, None)


# =============================================================================
# TEAM DEPENDENCY CHECK
# =============================================================================

def check_team_dependencies(db: Session, team_id: int) -> Dict[str, int]:
    """
    Check if a team has any dependencies (employees assigned).
    Only counts active employees (deleted_at IS NULL).
    
    Args:
        db: Database session
        team_id: ID of the team to check
        
    Returns:
        Dict with dependency counts, e.g. {"employees": 5}
    """
    employee_count = db.query(func.count(Employee.employee_id))\
        .filter(Employee.team_id == team_id)\
        .filter(Employee.deleted_at.is_(None))\
        .scalar() or 0
    
    dependencies = {}
    if employee_count > 0:
        dependencies["employees"] = employee_count
    
    return dependencies


def check_teams_dependencies_bulk(db: Session, team_ids: List[int]) -> List[Dict]:
    """
    Check if multiple teams have any dependencies (employees assigned).
    Only counts active employees (deleted_at IS NULL).
    Uses a single efficient query with GROUP BY.
    
    Args:
        db: Database session
        team_ids: List of team IDs to check
        
    Returns:
        List of blocked teams with counts, e.g. [{"team_id": 1, "employees": 5}]
    """
    if not team_ids:
        return []
    
    # Single query to get employee counts per team_id
    results = db.query(
        Employee.team_id,
        func.count(Employee.employee_id).label('employee_count')
    )\
        .filter(Employee.team_id.in_(team_ids))\
        .filter(Employee.deleted_at.is_(None))\
        .group_by(Employee.team_id)\
        .all()
    
    blocked = []
    for team_id, employee_count in results:
        if employee_count > 0:
            blocked.append({
                "team_id": team_id,
                "employees": employee_count
            })
    
    return blocked


# =============================================================================
# TEAM DELETE (soft delete)
# =============================================================================

def delete_team(
    db: Session,
    team_id: int,
    actor: Optional[str] = None
) -> bool:
    """
    Soft delete a team.
    
    Args:
        db: Database session
        team_id: ID of the team to delete
        actor: Username of the user performing the action (for audit)
        
    Returns:
        True if deletion succeeded
        
    Raises:
        ValueError: If team not found or already deleted
    """
    logger.info(f"Attempting to delete team {team_id} by {actor}")
    
    # Find team (not soft-deleted)
    team = db.query(Team).filter(
        Team.team_id == team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if not team:
        raise ValueError(f"Team with id {team_id} not found")
    
    # Soft delete (no dependency check for teams)
    team.deleted_at = datetime.now(timezone.utc)
    team.deleted_by = actor or "system"
    
    db.commit()
    
    logger.info(f"Team {team_id} soft deleted by {actor}")
    return True
