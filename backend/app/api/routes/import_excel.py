"""
FastAPI routes for Excel import functionality.
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.import_service import ImportService, ImportServiceError
from app.services.import_job_service import ImportJobService, JobStatusDBError
from app.services.imports.unresolved_skills_service import (
    get_unresolved_skills,
    get_single_skill_suggestions,
    resolve_skill,
    UnresolvedSkillsResponse,
    SingleSkillSuggestionsResponse,
    ResolveSkillRequest,
    ResolveSkillResponse,
    ImportJobNotFoundError,
    RawSkillNotFoundError,
    SkillNotFoundError,
    AlreadyResolvedError,
    AliasAlreadyExistsError
)
from app.services.imports.role_mapping_service import (
    get_roles_for_mapping,
    map_role_to_failed_row,
    RolesForMappingResponse,
    MapRoleRequest,
    MapRoleResponse,
    ImportJobNotFoundError as RoleImportJobNotFoundError,
    RoleNotFoundError,
    InvalidFailedRowError,
    AlreadyMappedError,
    NotRoleErrorError,
    AliasConflictError,
    MissingAliasTextError
)
from app.services.imports.team_mapping_service import (
    get_teams_for_mapping,
    map_team_to_failed_row,
    create_team_for_failed_row,
    TeamsForMappingResponse,
    MapTeamRequest,
    MapTeamResponse,
    CreateTeamFromImportRequest,
    CreateTeamFromImportResponse,
    ImportJobNotFoundError as TeamImportJobNotFoundError,
    ProjectNotFoundError,
    TeamNotFoundError,
    TeamNotInProjectError,
    InvalidFailedRowError as TeamInvalidFailedRowError,
    AlreadyMappedError as TeamAlreadyMappedError,
    NotTeamErrorError,
    MissingTeamTextError,
    MissingProjectInfoError
)
from app.db.session import get_db

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/import", tags=["import"])

# Thread pool for background import processing
# Test
executor = ThreadPoolExecutor(max_workers=2)


@router.post("/excel", response_model=Dict[str, Any])
async def import_excel_file(
    file: UploadFile = File(..., description="Excel file containing employee and skills data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import employee and skills data from Excel file with progress tracking.
    
    Returns immediately with a job_id. Use GET /import/status/{job_id} to poll progress.
    
    Expected Excel format:
    - Sheet 1: employees (employee_id, first_name, last_name, sub_segment, project, team, role)
    - Sheet 2: skills (employee_id, skill_name, category, subcategory, proficiency_level, 
               years_experience, last_used_year, interest_level)
    
    Returns:
        Dict with job_id for polling status
    
    Raises:
        HTTPException: If file validation fails
    """
    logger.info(f"Received Excel import request for file: {file.filename}")
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    # Validate file size (limit to 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file.size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )
      # Save uploaded file to temporary location
    try:
        temp_file_path = await _save_upload_file(file)
        logger.info(f"Saved uploaded file to: {temp_file_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Create import job in database
    try:
        job_service = ImportJobService(db)
        job_id = job_service.create_job(
            job_type="employee_import",
            message="Import starting..."
        )
        logger.info(f"✅ Created DB-backed import job {job_id} for file: {file.filename}")
    except Exception as e:
        logger.error(f"❌ Failed to create import job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create import job: {str(e)}"
        )
    
    # Start async import in background
    asyncio.create_task(_process_import_async(job_id, temp_file_path))
    
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "job_id": job_id,
            "status": "pending",
            "message": "Import job created. Poll /import/status/{job_id} for progress."
        }
    )


async def _process_import_async(job_id: str, file_path: str):
    """Process import in background thread with DB-backed progress tracking."""
    def _run_import():
        db = None
        import_service = None
        job_service = None
        try:
            logger.info(f"🔵 Starting background import for job {job_id}")
            logger.info(f"🔵 Creating new database session for background thread...")
            
            # Create NEW database session for background thread
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            logger.info(f"🔵 Database session created successfully")
            
            # Create job service for progress updates
            job_service = ImportJobService(db)
            
            # Create import service with job_id
            logger.info(f"🔵 Creating ImportService for file: {file_path}")
            import_service = ImportService(db_session=db, job_id=job_id)
            
            logger.info(f"🔵 Starting Excel import...")
            result = import_service.import_excel(file_path)
            
            logger.info(f"🔵 Import completed, updating job status...")
            
            # Mark job as complete in database
            job_service.complete_job(job_id, result)
            
            logger.info(f"✅ Import job {job_id} completed successfully")
            
        except Exception as e:
            # Mark job as failed in database
            logger.error(f"❌ Import job {job_id} failed: {type(e).__name__}", exc_info=True)
            
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            if job_service:
                job_service.fail_job(job_id, error_msg)
            else:
                # Fallback: create new session to update job status
                try:
                    from app.db.session import SessionLocal
                    fallback_db = SessionLocal()
                    fallback_service = ImportJobService(fallback_db)
                    fallback_service.fail_job(job_id, error_msg)
                    fallback_db.close()
                except Exception as fallback_err:
                    logger.error(f"❌ Failed to update job status on error: {fallback_err}")
            
            logger.error(f"❌ Job {job_id} marked as failed with error: {error_msg}")
            
        finally:
            # Close database session
            if db:
                try:
                    db.close()
                    logger.info(f"🔵 Database session closed for job {job_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to close database session: {str(e)}")
            
            # Clean up temporary file
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.info(f"🧹 Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clean up temporary file {file_path}: {str(e)}")
      # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _run_import)


async def _save_upload_file(upload_file: UploadFile) -> str:
    """
    Save uploaded file to a temporary location.
    
    Args:
        upload_file: The uploaded file
        
    Returns:
        str: Path to the saved temporary file
        
    Raises:
        Exception: If file saving fails
    """
    try:
        # Create temporary file
        suffix = Path(upload_file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            
            # Read and write file contents
            content = await upload_file.read()
            temp_file.write(content)
            temp_file.flush()
            
        logger.info(f"Saved {len(content)} bytes to temporary file: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise Exception(f"Failed to save uploaded file: {str(e)}")


@router.get("/status/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get the current status of an import job from database.
    
    Args:
        job_id: The job identifier returned from POST /import/excel
        db: Database session
        
    Returns:
        Dict with job status, progress, and results
        
    Raises:
        HTTPException: 
            - 404 if job truly not found (confirmed DB query returned no results)
            - 503 if database temporarily unavailable (transient error)
    """
    job_service = ImportJobService(db)
    
    try:
        job_status = job_service.get_job_status(job_id)
    except JobStatusDBError as e:
        # Transient DB error - return 503 so frontend keeps polling
        logger.warning(f"Transient DB error for job {job_id}: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "message": "Database temporarily busy. Import is still running, please retry.",
                "job_id": job_id
            }
        )
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found"
        )
    
    # Ensure backward compatibility with frontend
    # Frontend expects 'percent_complete' field
    if 'percent_complete' not in job_status:
        job_status['percent_complete'] = job_status.get('percent', 0)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=job_status
    )


# =============================================================================
# UNRESOLVED SKILLS ENDPOINTS
# =============================================================================

@router.get("/{import_run_id}/unresolved-skills", response_model=UnresolvedSkillsResponse)
async def get_import_unresolved_skills(
    import_run_id: str,
    include_suggestions: bool = True,
    max_suggestions: int = 5,
    db: Session = Depends(get_db)
) -> UnresolvedSkillsResponse:
    """
    Get all unresolved skills for an import run with optional suggestions.
    
    Args:
        import_run_id: The import job UUID
        include_suggestions: Whether to include skill match suggestions (default: true)
        max_suggestions: Maximum number of suggestions per skill (default: 5)
        db: Database session
        
    Returns:
        UnresolvedSkillsResponse with list of unresolved skills and suggestions
        
    Raises:
        HTTPException 404: If import job not found
    """
    try:
        result = get_unresolved_skills(
            db=db,
            import_run_id=import_run_id,
            include_suggestions=include_suggestions,
            max_suggestions=max_suggestions
        )
        return result
    except ImportJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{import_run_id}/unresolved-skills/resolve", response_model=ResolveSkillResponse)
async def resolve_import_skill(
    import_run_id: str,
    request: ResolveSkillRequest,
    db: Session = Depends(get_db)
) -> ResolveSkillResponse:
    """
    Map an unresolved skill to an existing master skill and create alias.
    
    This endpoint:
    1. Validates the import job and raw skill exist
    2. Creates an alias mapping the raw text to the target skill
    3. Marks the raw_skill_input as RESOLVED
    
    Args:
        import_run_id: The import job UUID
        request: ResolveSkillRequest with raw_skill_id and target_skill_id
        db: Database session
        
    Returns:
        ResolveSkillResponse with resolution details
        
    Raises:
        HTTPException 404: If import job, raw skill, or target skill not found
        HTTPException 400: If raw skill is already resolved
        HTTPException 409: If alias already exists for a different skill
    """
    try:
        result = resolve_skill(
            db=db,
            import_run_id=import_run_id,
            raw_skill_id=request.raw_skill_id,
            target_skill_id=request.target_skill_id,
            resolved_by=None  # TODO: Get from auth context
        )
        return result
    except ImportJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RawSkillNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SkillNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AlreadyResolvedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AliasAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(e),
                "existing_skill_id": e.existing_skill_id,
                "existing_skill_name": e.existing_skill_name,
                "alias_text": e.alias_text
            }
        )


@router.get(
    "/{import_run_id}/unresolved-skills/{raw_skill_id}/suggestions",
    response_model=SingleSkillSuggestionsResponse
)
async def get_single_skill_suggestions_endpoint(
    import_run_id: str,
    raw_skill_id: int,
    max_suggestions: int = 10,
    include_embeddings: bool = True,
    db: Session = Depends(get_db)
) -> SingleSkillSuggestionsResponse:
    """
    Get suggestions for a single unresolved skill by raw_skill_id.
    
    This endpoint is optimized for the skill mapping modal - it fetches
    suggestions for only ONE skill instead of computing suggestions for
    all unresolved skills (which can be very slow with 500+ skills).
    
    Args:
        import_run_id: The import job UUID
        raw_skill_id: ID of the specific raw_skill_input to get suggestions for
        max_suggestions: Maximum number of suggestions to return (default: 10)
        include_embeddings: Include embedding-based suggestions (default: true)
        db: Database session
        
    Returns:
        SingleSkillSuggestionsResponse with suggestions for this one skill
        
    Raises:
        HTTPException 404: If import job or raw skill not found
    """
    try:
        result = get_single_skill_suggestions(
            db=db,
            import_run_id=import_run_id,
            raw_skill_id=raw_skill_id,
            max_suggestions=max_suggestions,
            include_embeddings=include_embeddings
        )
        return result
    except ImportJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RawSkillNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# =============================================================================
# ROLE MAPPING ENDPOINTS
# =============================================================================

@router.get("/{import_run_id}/roles-for-mapping", response_model=RolesForMappingResponse)
async def get_roles_for_mapping_endpoint(
    import_run_id: str,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
) -> RolesForMappingResponse:
    """
    Get all active roles for the role mapping UI.
    
    Args:
        import_run_id: The import job UUID (for validation)
        q: Optional search query to filter roles (case-insensitive)
        db: Database session
        
    Returns:
        RolesForMappingResponse with list of roles
        
    Raises:
        HTTPException 404: If import job not found
    """
    # Validate import job exists
    from app.models.import_job import ImportJob
    import_job = db.query(ImportJob).filter(ImportJob.job_id == import_run_id).first()
    if not import_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{import_run_id}' not found"
        )
    
    return get_roles_for_mapping(db=db, search_query=q)


@router.post("/{import_run_id}/map-role", response_model=MapRoleResponse)
async def map_role_to_import_row(
    import_run_id: str,
    request: MapRoleRequest,
    db: Session = Depends(get_db)
) -> MapRoleResponse:
    """
    Map a MISSING_ROLE failed row to an existing master role.
    
    This endpoint updates the import job result to mark the row as resolved.
    
    Args:
        import_run_id: The import job UUID
        request: MapRoleRequest with failed_row_index and target_role_id
        db: Database session
        
    Returns:
        MapRoleResponse with mapping details
        
    Raises:
        HTTPException 404: If import job or role not found
        HTTPException 400: If row is already mapped or not a MISSING_ROLE error
    """
    try:
        result = map_role_to_failed_row(
            db=db,
            import_run_id=import_run_id,
            failed_row_index=request.failed_row_index,
            target_role_id=request.target_role_id,
            mapped_by=None  # TODO: Get from auth context
        )
        return result
    except RoleImportJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidFailedRowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AlreadyMappedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotRoleErrorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AliasConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except MissingAliasTextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =============================================================================
# TEAM MAPPING ENDPOINTS
# =============================================================================

@router.get("/{import_run_id}/teams-for-mapping", response_model=TeamsForMappingResponse)
async def get_teams_for_mapping_endpoint(
    import_run_id: str,
    project_id: int,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
) -> TeamsForMappingResponse:
    """
    Get all active teams for a specific project for the team mapping UI.
    
    Args:
        import_run_id: The import job UUID (for validation)
        project_id: The project ID to get teams for
        q: Optional search query to filter teams (case-insensitive)
        db: Database session
        
    Returns:
        TeamsForMappingResponse with list of teams
        
    Raises:
        HTTPException 404: If import job or project not found
    """
    # Validate import job exists
    from app.models.import_job import ImportJob
    import_job = db.query(ImportJob).filter(ImportJob.job_id == import_run_id).first()
    if not import_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{import_run_id}' not found"
        )
    
    try:
        return get_teams_for_mapping(db=db, project_id=project_id, search_query=q)
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{import_run_id}/map-team", response_model=MapTeamResponse)
async def map_team_to_import_row(
    import_run_id: str,
    request: MapTeamRequest,
    db: Session = Depends(get_db)
) -> MapTeamResponse:
    """
    Map a MISSING_TEAM failed row to an existing master team.
    
    This endpoint:
    1. Validates the team belongs to the expected project
    2. Updates the import job result to mark the row as resolved
    
    Args:
        import_run_id: The import job UUID
        request: MapTeamRequest with failed_row_index and target_team_id
        db: Database session
        
    Returns:
        MapTeamResponse with mapping details
        
    Raises:
        HTTPException 404: If import job, project, or team not found
        HTTPException 400: If row is already mapped, not a MISSING_TEAM error,
                          or team doesn't belong to the expected project
    """
    try:
        result = map_team_to_failed_row(
            db=db,
            import_run_id=import_run_id,
            failed_row_index=request.failed_row_index,
            target_team_id=request.target_team_id,
            mapped_by=None  # TODO: Get from auth context
        )
        return result
    except TeamImportJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TeamNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TeamNotInProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TeamInvalidFailedRowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TeamAlreadyMappedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotTeamErrorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MissingTeamTextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MissingProjectInfoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{import_run_id}/create-team", response_model=CreateTeamFromImportResponse)
async def create_team_for_import_row(
    import_run_id: str,
    request: CreateTeamFromImportRequest,
    db: Session = Depends(get_db)
) -> CreateTeamFromImportResponse:
    """
    Create a new team for a MISSING_TEAM failed row.
    
    This endpoint allows users to create a new team directly from the import
    error resolution dialog, instead of only mapping to existing teams.
    
    The team is created under the same project as specified in the failed row,
    and the row is marked as resolved.
    
    Args:
        import_run_id: The import job UUID
        request: CreateTeamFromImportRequest with failed_row_index and team_name
        db: Database session
        
    Returns:
        CreateTeamFromImportResponse with created team details
        
    Raises:
        HTTPException 404: If import job not found
        HTTPException 400: If row is already mapped, not a MISSING_TEAM error,
                          team name is invalid, or team already exists
    """
    try:
        result = create_team_for_failed_row(
            db=db,
            import_run_id=import_run_id,
            failed_row_index=request.failed_row_index,
            team_name=request.team_name,
            created_by=None  # TODO: Get from auth context
        )
        return result
    except TeamImportJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TeamInvalidFailedRowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TeamAlreadyMappedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotTeamErrorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MissingProjectInfoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        # From create_team: invalid name, duplicate team, or parent not found
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )