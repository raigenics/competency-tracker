"""
Service for mapping missing teams from Employee Bulk Import.

Provides:
- GET endpoint: List teams under a project for mapping UI
- POST endpoint: Map failed row to existing team (update import job result)

Teams are matched by team_name + project_id only (no aliases).
"""
import logging
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.team import Team
from app.models.project import Project
from app.models.import_job import ImportJob
from app.utils.normalization import normalize_designation
from app.services.org_hierarchy_service import create_team


logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class TeamForMapping(BaseModel):
    """A team available for mapping."""
    team_id: int
    team_name: str
    project_id: int
    project_name: Optional[str] = None


class TeamsForMappingResponse(BaseModel):
    """Response for GET teams for mapping endpoint."""
    total_count: int
    project_id: int
    project_name: str
    teams: List[TeamForMapping]


class MapTeamRequest(BaseModel):
    """Request body for POST map team endpoint."""
    failed_row_index: int = Field(description="Index of the failed row in failed_rows array")
    target_team_id: int = Field(description="ID of the master team to map to")


class MapTeamResponse(BaseModel):
    """Response for POST map team endpoint."""
    failed_row_index: int
    mapped_team_id: int
    mapped_team_name: str
    project_id: int
    project_name: str
    message: str


class CreateTeamFromImportRequest(BaseModel):
    """Request body for POST create-team endpoint."""
    failed_row_index: int = Field(description="Index of the failed row in failed_rows array")
    team_name: str = Field(description="Name for the new team")


class CreateTeamFromImportResponse(BaseModel):
    """Response for POST create-team endpoint."""
    failed_row_index: int
    created_team_id: int
    created_team_name: str
    project_id: int
    project_name: str
    message: str


# =============================================================================
# EXCEPTIONS
# =============================================================================

class TeamMappingError(Exception):
    """Base exception for team mapping operations."""
    pass


class ImportJobNotFoundError(TeamMappingError):
    """Import job not found."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Import job '{job_id}' not found")


class ProjectNotFoundError(TeamMappingError):
    """Project not found."""
    def __init__(self, project_id: int):
        self.project_id = project_id
        super().__init__(f"Project with ID {project_id} not found")


class TeamNotFoundError(TeamMappingError):
    """Team not found."""
    def __init__(self, team_id: int):
        self.team_id = team_id
        super().__init__(f"Team with ID {team_id} not found or is deleted")


class TeamNotInProjectError(TeamMappingError):
    """Team does not belong to the expected project."""
    def __init__(self, team_id: int, expected_project_id: int, actual_project_id: int):
        self.team_id = team_id
        self.expected_project_id = expected_project_id
        self.actual_project_id = actual_project_id
        super().__init__(
            f"Team {team_id} belongs to project {actual_project_id}, "
            f"not project {expected_project_id}"
        )


class InvalidFailedRowError(TeamMappingError):
    """Invalid failed row index."""
    def __init__(self, index: int, reason: str):
        self.index = index
        self.reason = reason
        super().__init__(f"Failed row at index {index}: {reason}")


class AlreadyMappedError(TeamMappingError):
    """Row is already mapped."""
    def __init__(self, index: int):
        self.index = index
        super().__init__(f"Failed row at index {index} is already mapped")


class NotTeamErrorError(TeamMappingError):
    """Row is not a MISSING_TEAM error."""
    def __init__(self, index: int, error_code: str):
        self.index = index
        self.error_code = error_code
        super().__init__(f"Failed row at index {index} has error code '{error_code}', not MISSING_TEAM")


class MissingTeamTextError(TeamMappingError):
    """Failed row does not contain team_name."""
    def __init__(self, index: int):
        self.index = index
        super().__init__(f"Failed row at index {index} does not contain team_name")


class MissingProjectInfoError(TeamMappingError):
    """Failed row does not contain project information for team lookup."""
    def __init__(self, index: int):
        self.index = index
        super().__init__(f"Failed row at index {index} does not contain project information")


# =============================================================================
# SERVICE FUNCTIONS
# =============================================================================

def normalize_team_name(name: str) -> str:
    """
    Normalize team name for matching.
    Uses the same normalize_designation function as roles for consistency.
    """
    return normalize_designation(name)


def get_project_by_name(db: Session, project_name: str, sub_segment_id: Optional[int] = None) -> Optional[Project]:
    """
    Find a project by name, optionally scoped to a sub-segment.
    
    Args:
        db: Database session
        project_name: The project name to search for
        sub_segment_id: Optional sub-segment to scope the search
        
    Returns:
        Project if found, None otherwise
    """
    query = db.query(Project).filter(
        func.lower(Project.project_name) == project_name.lower().strip()
    )
    
    if sub_segment_id:
        query = query.filter(Project.sub_segment_id == sub_segment_id)
    
    return query.first()


def get_teams_for_mapping(
    db: Session,
    project_id: int,
    search_query: Optional[str] = None
) -> TeamsForMappingResponse:
    """
    Get all active teams for a specific project for the mapping UI.
    
    Args:
        db: Database session
        project_id: The project ID to get teams for
        search_query: Optional search string to filter teams by name (case-insensitive)
        
    Returns:
        TeamsForMappingResponse with list of teams
        
    Raises:
        ProjectNotFoundError: If project not found
    """
    # Validate project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise ProjectNotFoundError(project_id)
    
    query = db.query(Team).filter(
        Team.deleted_at.is_(None),
        Team.project_id == project_id
    )
    
    # Apply search filter if provided (only by team_name)
    if search_query:
        search_term = f"%{search_query.lower()}%"
        query = query.filter(func.lower(Team.team_name).like(search_term))
    
    # Order alphabetically
    query = query.order_by(Team.team_name)
    
    teams = query.all()
    
    return TeamsForMappingResponse(
        total_count=len(teams),
        project_id=project_id,
        project_name=project.project_name,
        teams=[
            TeamForMapping(
                team_id=team.team_id,
                team_name=team.team_name,
                project_id=team.project_id,
                project_name=project.project_name
            )
            for team in teams
        ]
    )


def map_team_to_failed_row(
    db: Session,
    import_run_id: str,
    failed_row_index: int,
    target_team_id: int,
    mapped_by: Optional[str] = None
) -> MapTeamResponse:
    """
    Map a MISSING_TEAM failed row to an existing master team.
    
    This:
    1. Validates the team belongs to the expected project
    2. Updates the ImportJob.result to mark the row as resolved.
    
    Args:
        db: Database session
        import_run_id: The import job UUID
        failed_row_index: Index of the failed row in failed_rows array
        target_team_id: ID of the master team to map to
        mapped_by: User who performed the mapping (optional)
        
    Returns:
        MapTeamResponse with mapping details
        
    Raises:
        ImportJobNotFoundError: If import job not found
        TeamNotFoundError: If target team not found or deleted
        TeamNotInProjectError: If team doesn't belong to the expected project
        InvalidFailedRowError: If failed row index is invalid
        AlreadyMappedError: If row is already mapped
        NotTeamErrorError: If row is not a MISSING_TEAM error
        MissingTeamTextError: If failed row doesn't contain team_name
        MissingProjectInfoError: If failed row doesn't contain project info
    """
    logger.info(
        f"Team mapping request received: import_run_id={import_run_id}, "
        f"failed_row_index={failed_row_index}, target_team_id={target_team_id}"
    )
    
    # 1. Find the import job
    import_job = db.query(ImportJob).filter(
        ImportJob.job_id == import_run_id
    ).first()
    
    if not import_job:
        raise ImportJobNotFoundError(import_run_id)
    
    # 2. Get the result and validate failed row exists
    result = import_job.result
    if not result or 'failed_rows' not in result:
        raise InvalidFailedRowError(failed_row_index, "Import job has no failed rows")
    
    failed_rows = result.get('failed_rows', [])
    
    if failed_row_index < 0 or failed_row_index >= len(failed_rows):
        raise InvalidFailedRowError(
            failed_row_index, 
            f"Index out of range (0-{len(failed_rows) - 1})"
        )
    
    failed_row = failed_rows[failed_row_index]
    
    # 3. Validate it's a MISSING_TEAM error
    error_code = failed_row.get('error_code', '')
    if error_code != 'MISSING_TEAM':
        raise NotTeamErrorError(failed_row_index, error_code)
    
    # 4. Check if already mapped
    if failed_row.get('resolved') is True:
        raise AlreadyMappedError(failed_row_index)
    
    # 5. Get the team text and project info from the failed row
    team_text = failed_row.get('team_name', '').strip()
    if not team_text:
        raise MissingTeamTextError(failed_row_index)
    
    project_name = failed_row.get('project_name', '').strip()
    project_id = failed_row.get('project_id')
    
    if not project_name and not project_id:
        raise MissingProjectInfoError(failed_row_index)
    
    # 6. Resolve project_id if we only have project_name
    if not project_id and project_name:
        project = get_project_by_name(db, project_name)
        if not project:
            raise InvalidFailedRowError(
                failed_row_index, 
                f"Project '{project_name}' not found in database"
            )
        project_id = project.project_id
    
    # 7. Validate target team exists and is not deleted
    team = db.query(Team).filter(
        Team.team_id == target_team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if not team:
        raise TeamNotFoundError(target_team_id)
    
    # 8. Validate team belongs to the expected project
    if team.project_id != project_id:
        raise TeamNotInProjectError(target_team_id, project_id, team.project_id)
    
    # Get project info for response
    project = db.query(Project).filter(Project.project_id == project_id).first()
    project_name = project.project_name if project else "Unknown"
    
    logger.info(f"Mapping team_text='{team_text}' to team_id={target_team_id} in project '{project_name}'")
    
    # 9. Update the failed row to mark as resolved
    failed_row['resolved'] = True
    failed_row['mapped_team_id'] = target_team_id
    failed_row['mapped_team_name'] = team.team_name
    failed_row['mapped_by'] = mapped_by
    
    # 10. Update the import job result (need to replace the entire JSON)
    # SQLAlchemy JSON column requires explicit assignment to detect changes
    import_job.result = {**result, 'failed_rows': failed_rows}
    
    # 11. Commit the changes
    db.commit()
    
    logger.info(
        f"Mapped MISSING_TEAM row {failed_row_index} in job {import_run_id} "
        f"to team '{team.team_name}' (ID: {target_team_id})"
    )
    
    return MapTeamResponse(
        failed_row_index=failed_row_index,
        mapped_team_id=target_team_id,
        mapped_team_name=team.team_name,
        project_id=project_id,
        project_name=project_name,
        message=f"Successfully mapped to team '{team.team_name}'"
    )


def create_team_for_failed_row(
    db: Session,
    import_run_id: str,
    failed_row_index: int,
    team_name: str,
    created_by: Optional[str] = None
) -> CreateTeamFromImportResponse:
    """
    Create a new team for a MISSING_TEAM failed row.
    
    This:
    1. Validates the failed row is a MISSING_TEAM error and not already resolved
    2. Gets the project_id from the failed row
    3. Creates a new team using the shared create_team() service
    4. Updates the ImportJob.result to mark the row as resolved
    
    Args:
        db: Database session
        import_run_id: The import job UUID
        failed_row_index: Index of the failed row in failed_rows array
        team_name: Name for the new team
        created_by: User who is creating the team (optional)
        
    Returns:
        CreateTeamFromImportResponse with created team details
        
    Raises:
        ImportJobNotFoundError: If import job not found
        InvalidFailedRowError: If failed row index is invalid or project not found
        AlreadyMappedError: If row is already mapped
        NotTeamErrorError: If row is not a MISSING_TEAM error
        MissingProjectInfoError: If failed row doesn't contain project info
        ValueError: If team name is invalid or already exists (from create_team)
    """
    logger.info(
        f"Create team request received: import_run_id={import_run_id}, "
        f"failed_row_index={failed_row_index}, team_name='{team_name}'"
    )
    
    # 1. Find the import job
    import_job = db.query(ImportJob).filter(
        ImportJob.job_id == import_run_id
    ).first()
    
    if not import_job:
        raise ImportJobNotFoundError(import_run_id)
    
    # 2. Get the result and validate failed row exists
    result = import_job.result
    if not result or 'failed_rows' not in result:
        raise InvalidFailedRowError(failed_row_index, "Import job has no failed rows")
    
    failed_rows = result.get('failed_rows', [])
    
    if failed_row_index < 0 or failed_row_index >= len(failed_rows):
        raise InvalidFailedRowError(
            failed_row_index, 
            f"Index out of range (0-{len(failed_rows) - 1})"
        )
    
    failed_row = failed_rows[failed_row_index]
    
    # 3. Validate it's a MISSING_TEAM error
    error_code = failed_row.get('error_code', '')
    if error_code != 'MISSING_TEAM':
        raise NotTeamErrorError(failed_row_index, error_code)
    
    # 4. Check if already resolved
    if failed_row.get('resolved') is True:
        raise AlreadyMappedError(failed_row_index)
    
    # 5. Get the project info from the failed row
    project_name = failed_row.get('project_name', '').strip()
    project_id = failed_row.get('project_id')
    
    if not project_name and not project_id:
        raise MissingProjectInfoError(failed_row_index)
    
    # 6. Resolve project_id if we only have project_name
    if not project_id and project_name:
        project = get_project_by_name(db, project_name)
        if not project:
            raise InvalidFailedRowError(
                failed_row_index, 
                f"Project '{project_name}' not found in database"
            )
        project_id = project.project_id
    
    # Get project for response
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise InvalidFailedRowError(
            failed_row_index, 
            f"Project with ID {project_id} not found in database"
        )
    
    logger.info(f"Creating team '{team_name}' under project '{project.project_name}' (ID: {project_id})")
    
    # 7. Create the team using the shared service
    # This will raise ValueError if name is invalid, duplicate, or project not found
    team_response = create_team(
        db=db,
        project_id=project_id,
        team_name=team_name,
        actor=created_by
    )
    
    # 8. Update the failed row to mark as resolved
    failed_row['resolved'] = True
    failed_row['created_team_id'] = team_response.team_id
    failed_row['created_team_name'] = team_response.team_name
    failed_row['created_by'] = created_by
    
    # 9. Update the import job result (need to replace the entire JSON)
    import_job.result = {**result, 'failed_rows': failed_rows}
    
    # 10. Commit the changes
    db.commit()
    
    logger.info(
        f"Created team '{team_response.team_name}' (ID: {team_response.team_id}) "
        f"for MISSING_TEAM row {failed_row_index} in job {import_run_id}"
    )
    
    return CreateTeamFromImportResponse(
        failed_row_index=failed_row_index,
        created_team_id=team_response.team_id,
        created_team_name=team_response.team_name,
        project_id=project_id,
        project_name=project.project_name,
        message=f"Successfully created team '{team_response.team_name}'"
    )
