"""
API routes for Org Hierarchy.

Provides endpoints for retrieving and managing the organizational hierarchy.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.org_hierarchy import (
    OrgHierarchyResponse,
    SegmentCreateRequest,
    SegmentCreateResponse,
    SubSegmentCreateRequest,
    SubSegmentCreateResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    TeamCreateRequest,
    TeamCreateResponse,
    SegmentUpdateRequest,
    SegmentUpdateResponse,
    SubSegmentUpdateRequest,
    SubSegmentUpdateResponse,
    ProjectUpdateRequest,
    ProjectUpdateResponse,
    TeamUpdateRequest,
    TeamUpdateResponse,
    DependencyConflictResponse,
)
from app.services.org_hierarchy_service import (
    get_org_hierarchy,
    create_segment,
    create_sub_segment,
    create_project,
    create_team,
    update_segment,
    update_sub_segment,
    update_project,
    update_team,
    delete_segment,
    delete_sub_segment,
    delete_project,
    delete_team,
    get_segment_dependencies,
    get_sub_segment_dependencies,
    get_project_dependencies,
    check_team_dependencies,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/org-hierarchy",
    tags=["org-hierarchy"]
)


@router.get(
    "",
    response_model=OrgHierarchyResponse,
    summary="Get full organizational hierarchy",
    description="Returns the complete org hierarchy: Segments → Sub-segments → Projects → Teams. "
                "Excludes soft-deleted records. Results sorted alphabetically by name at each level."
)
def read_org_hierarchy(db: Session = Depends(get_db)) -> OrgHierarchyResponse:
    """
    Retrieve the full organizational hierarchy.
    
    Returns a nested structure with:
    - Segments at the top level
    - Sub-segments nested within their parent segment
    - Projects nested within their parent sub-segment
    - Teams nested within their parent project
    
    Also includes total counts for each level.
    """
    return get_org_hierarchy(db)


# =============================================================================
# POST ENDPOINTS - Create Segment
# =============================================================================

@router.post(
    "/segments",
    response_model=SegmentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new segment",
    responses={
        409: {"description": "Segment name already exists"},
        422: {"description": "Validation error"},
    }
)
def create_segment_endpoint(
    request: SegmentCreateRequest,
    db: Session = Depends(get_db)
) -> SegmentCreateResponse:
    """
    Create a new segment.
    
    Args:
    - **name**: Name for the segment (must be unique, case-insensitive)
    """
    logger.info(f"POST /org-hierarchy/segments - name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return create_segment(
            db=db,
            segment_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to create segment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create segment"
        )


# =============================================================================
# POST ENDPOINTS - Create Sub-Segment
# =============================================================================

@router.post(
    "/sub-segments",
    response_model=SubSegmentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sub-segment",
    responses={
        404: {"description": "Parent segment not found"},
        409: {"description": "Sub-segment name already exists"},
        422: {"description": "Validation error"},
    }
)
def create_sub_segment_endpoint(
    request: SubSegmentCreateRequest,
    db: Session = Depends(get_db)
) -> SubSegmentCreateResponse:
    """
    Create a new sub-segment under a segment.
    
    Args:
    - **segment_id**: Parent segment ID
    - **name**: Name for the sub-segment (must be unique, case-insensitive)
    """
    logger.info(f"POST /org-hierarchy/sub-segments - segment_id={request.segment_id}, name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return create_sub_segment(
            db=db,
            segment_id=request.segment_id,
            sub_segment_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to create sub-segment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sub-segment"
        )


# =============================================================================
# POST ENDPOINTS - Create Project
# =============================================================================

@router.post(
    "/projects",
    response_model=ProjectCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    responses={
        404: {"description": "Parent sub-segment not found"},
        409: {"description": "Project name already exists in this sub-segment"},
        422: {"description": "Validation error"},
    }
)
def create_project_endpoint(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db)
) -> ProjectCreateResponse:
    """
    Create a new project under a sub-segment.
    
    Args:
    - **sub_segment_id**: Parent sub-segment ID
    - **name**: Name for the project (must be unique within sub-segment)
    - **description**: Optional description
    """
    logger.info(f"POST /org-hierarchy/projects - sub_segment_id={request.sub_segment_id}, name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return create_project(
            db=db,
            sub_segment_id=request.sub_segment_id,
            project_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


# =============================================================================
# POST ENDPOINTS - Create Team
# =============================================================================

@router.post(
    "/teams",
    response_model=TeamCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new team",
    responses={
        404: {"description": "Parent project not found"},
        409: {"description": "Team name already exists in this project"},
        422: {"description": "Validation error"},
    }
)
def create_team_endpoint(
    request: TeamCreateRequest,
    db: Session = Depends(get_db)
) -> TeamCreateResponse:
    """
    Create a new team under a project.
    
    Args:
    - **project_id**: Parent project ID
    - **name**: Name for the team (must be unique within project)
    - **description**: Optional description
    """
    logger.info(f"POST /org-hierarchy/teams - project_id={request.project_id}, name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return create_team(
            db=db,
            project_id=request.project_id,
            team_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to create team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )


# =============================================================================
# PUT ENDPOINTS - Update Segment
# =============================================================================

@router.put(
    "/segments/{segment_id}",
    response_model=SegmentUpdateResponse,
    summary="Update a segment's name",
    responses={
        404: {"description": "Segment not found"},
        409: {"description": "Segment name already exists"},
        422: {"description": "Validation error"},
    }
)
def update_segment_endpoint(
    segment_id: int,
    request: SegmentUpdateRequest,
    db: Session = Depends(get_db)
) -> SegmentUpdateResponse:
    """
    Update a segment's name.
    
    Args:
    - **segment_id**: Segment ID to update
    - **name**: New name for the segment (must be unique, case-insensitive)
    """
    logger.info(f"PUT /org-hierarchy/segments/{segment_id} - name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return update_segment(
            db=db,
            segment_id=segment_id,
            segment_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to update segment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update segment"
        )


# =============================================================================
# PUT ENDPOINTS - Update Sub-Segment
# =============================================================================

@router.put(
    "/sub-segments/{sub_segment_id}",
    response_model=SubSegmentUpdateResponse,
    summary="Update a sub-segment's name",
    responses={
        404: {"description": "Sub-segment not found"},
        409: {"description": "Sub-segment name already exists"},
        422: {"description": "Validation error"},
    }
)
def update_sub_segment_endpoint(
    sub_segment_id: int,
    request: SubSegmentUpdateRequest,
    db: Session = Depends(get_db)
) -> SubSegmentUpdateResponse:
    """
    Update a sub-segment's name.
    
    Args:
    - **sub_segment_id**: Sub-segment ID to update
    - **name**: New name for the sub-segment (must be unique, case-insensitive)
    """
    logger.info(f"PUT /org-hierarchy/sub-segments/{sub_segment_id} - name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return update_sub_segment(
            db=db,
            sub_segment_id=sub_segment_id,
            sub_segment_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to update sub-segment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sub-segment"
        )


# =============================================================================
# PUT ENDPOINTS - Update Project
# =============================================================================

@router.put(
    "/projects/{project_id}",
    response_model=ProjectUpdateResponse,
    summary="Update a project's name",
    responses={
        404: {"description": "Project not found"},
        409: {"description": "Project name already exists"},
        422: {"description": "Validation error"},
    }
)
def update_project_endpoint(
    project_id: int,
    request: ProjectUpdateRequest,
    db: Session = Depends(get_db)
) -> ProjectUpdateResponse:
    """
    Update a project's name.
    
    Args:
    - **project_id**: Project ID to update
    - **name**: New name for the project (must be unique, case-insensitive)
    """
    logger.info(f"PUT /org-hierarchy/projects/{project_id} - name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return update_project(
            db=db,
            project_id=project_id,
            project_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


# =============================================================================
# PUT ENDPOINTS - Update Team
# =============================================================================

@router.put(
    "/teams/{team_id}",
    response_model=TeamUpdateResponse,
    summary="Update a team's name",
    responses={
        404: {"description": "Team not found"},
        409: {"description": "Team name already exists"},
        422: {"description": "Validation error"},
    }
)
def update_team_endpoint(
    team_id: int,
    request: TeamUpdateRequest,
    db: Session = Depends(get_db)
) -> TeamUpdateResponse:
    """
    Update a team's name.
    
    Args:
    - **team_id**: Team ID to update
    - **name**: New name for the team (must be unique, case-insensitive)
    """
    logger.info(f"PUT /org-hierarchy/teams/{team_id} - name='{request.name}'")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return update_team(
            db=db,
            team_id=team_id,
            team_name=request.name,
            actor=actor
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to update team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team"
        )


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Segment
# =============================================================================

@router.delete(
    "/segments/{segment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a segment",
    responses={
        200: {"description": "Dry run: No dependencies, can delete"},
        204: {"description": "Segment deleted successfully"},
        404: {"description": "Segment not found"},
        409: {
            "description": "Segment has dependencies and cannot be deleted",
            "model": DependencyConflictResponse
        },
    }
)
def delete_segment_endpoint(
    segment_id: int,
    dry_run: bool = Query(False, description="If true, only check dependencies without deleting"),
    db: Session = Depends(get_db)
):
    """
    Soft delete a segment.
    
    The segment will be marked as deleted (deleted_at timestamp set) but not
    physically removed from the database.
    
    **Dependency Check:**
    Before deletion, the API checks for active (non-deleted) dependencies:
    - Sub-segments under this segment
    - Projects under those sub-segments
    - Teams under those projects
    
    If any dependencies exist, returns 409 with dependency counts.
    
    **Dry Run Mode:**
    When dry_run=true, only checks dependencies and returns:
    - 409 if dependencies exist
    - 200 if no dependencies (does NOT delete)
    
    Args:
    - **segment_id**: Segment ID to delete
    - **dry_run**: If true, only check dependencies without deleting
    """
    logger.info(f"DELETE /org-hierarchy/segments/{segment_id} dry_run={dry_run}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        # Check dependencies first
        from app.models.segment import Segment
        segment = db.query(Segment).filter(
            Segment.segment_id == segment_id,
            Segment.deleted_at.is_(None)
        ).first()
        
        if not segment:
            raise ValueError(f"Segment with id {segment_id} not found")
        
        dependencies = get_segment_dependencies(db, segment_id)
        total_deps = sum(dependencies.values())
        
        if total_deps > 0:
            # Has dependencies - return 409 with counts
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies": dependencies
                }
            )
        
        # No dependencies
        if dry_run:
            # Dry run - just return 200 OK (can delete)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "No dependencies, can delete", "can_delete": True}
            )
        
        # Actually delete
        success, _ = delete_segment(
            db=db,
            segment_id=segment_id,
            actor=actor
        )
        
        # Success - return 204 No Content
        return None
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to delete segment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete segment"
        )


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Sub-Segment
# =============================================================================

@router.delete(
    "/sub-segments/{sub_segment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a sub-segment",
    responses={
        200: {"description": "Dry run: No dependencies, can delete"},
        204: {"description": "Sub-segment deleted successfully"},
        404: {"description": "Sub-segment not found"},
        409: {
            "description": "Sub-segment has dependencies and cannot be deleted",
            "model": DependencyConflictResponse
        },
    }
)
def delete_sub_segment_endpoint(
    sub_segment_id: int,
    dry_run: bool = Query(False, description="If true, only check dependencies without deleting"),
    db: Session = Depends(get_db)
):
    """
    Soft delete a sub-segment.
    
    The sub-segment will be marked as deleted (deleted_at timestamp set) but not
    physically removed from the database.
    
    **Dependency Check:**
    Before deletion, the API checks for active (non-deleted) dependencies:
    - Projects under this sub-segment
    - Teams under those projects
    
    If any dependencies exist, returns 409 with dependency counts.
    
    **Dry Run Mode:**
    When dry_run=true, only checks dependencies and returns:
    - 409 if dependencies exist
    - 200 if no dependencies (does NOT delete)
    
    Args:
    - **sub_segment_id**: Sub-segment ID to delete
    - **dry_run**: If true, only check dependencies without deleting
    """
    logger.info(f"DELETE /org-hierarchy/sub-segments/{sub_segment_id} dry_run={dry_run}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        # Check dependencies first
        from app.models.sub_segment import SubSegment
        sub_segment = db.query(SubSegment).filter(
            SubSegment.sub_segment_id == sub_segment_id,
            SubSegment.deleted_at.is_(None)
        ).first()
        
        if not sub_segment:
            raise ValueError(f"Sub-segment with id {sub_segment_id} not found")
        
        dependencies = get_sub_segment_dependencies(db, sub_segment_id)
        total_deps = sum(dependencies.values())
        
        if total_deps > 0:
            # Has dependencies - return 409 with counts
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies": dependencies
                }
            )
        
        # No dependencies
        if dry_run:
            # Dry run - just return 200 OK (can delete)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "No dependencies, can delete", "can_delete": True}
            )
        
        # Actually delete
        success, _ = delete_sub_segment(
            db=db,
            sub_segment_id=sub_segment_id,
            actor=actor
        )
        
        # Success - return 204 No Content
        return None
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to delete sub-segment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sub-segment"
        )


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Project
# =============================================================================

@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a project",
    responses={
        200: {"description": "Dry run: No dependencies, can delete"},
        204: {"description": "Project deleted successfully"},
        404: {"description": "Project not found"},
        409: {
            "description": "Project has dependencies and cannot be deleted",
            "model": DependencyConflictResponse
        },
    }
)
def delete_project_endpoint(
    project_id: int,
    dry_run: bool = Query(False, description="If true, only check dependencies without deleting"),
    db: Session = Depends(get_db)
):
    """
    Soft delete a project.
    
    The project will be marked as deleted (deleted_at timestamp set) but not
    physically removed from the database.
    
    **Dependency Check:**
    Before deletion, the API checks for active (non-deleted) dependencies:
    - Teams under this project
    
    If any dependencies exist, returns 409 with dependency counts.
    
    **Dry Run Mode:**
    When dry_run=true, only checks dependencies and returns:
    - 409 if dependencies exist
    - 200 if no dependencies (does NOT delete)
    
    Args:
    - **project_id**: Project ID to delete
    - **dry_run**: If true, only check dependencies without deleting
    """
    logger.info(f"DELETE /org-hierarchy/projects/{project_id} dry_run={dry_run}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        # Check dependencies first
        from app.models.project import Project
        project = db.query(Project).filter(
            Project.project_id == project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        
        dependencies = get_project_dependencies(db, project_id)
        total_deps = sum(dependencies.values())
        
        if total_deps > 0:
            # Has dependencies - return 409 with counts
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies": dependencies
                }
            )
        
        # No dependencies
        if dry_run:
            # Dry run - just return 200 OK (can delete)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "No dependencies, can delete", "can_delete": True}
            )
        
        # Actually delete
        success, _ = delete_project(
            db=db,
            project_id=project_id,
            actor=actor
        )
        
        # Success - return 204 No Content
        return None
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Team
# =============================================================================

@router.delete(
    "/teams/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a team",
    responses={
        204: {"description": "Team deleted successfully"},
        404: {"description": "Team not found"},
        409: {"description": "Team has dependencies (employees assigned)"},
    }
)
def delete_team_endpoint(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a team.
    
    The team will be marked as deleted (deleted_at timestamp set) but not
    physically removed from the database.
    
    Args:
    - **team_id**: Team ID to delete
    
    Raises:
        404: If team not found or already deleted
        409: If team has dependencies (employees assigned to team)
    """
    logger.info(f"DELETE /org-hierarchy/teams/{team_id}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        # Check for dependencies first
        dependencies = check_team_dependencies(db, team_id)
        if dependencies:
            logger.warning(f"Team {team_id} has dependencies: {dependencies}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies": dependencies
                }
            )
        
        delete_team(
            db=db,
            team_id=team_id,
            actor=actor
        )
        
        # Success - return 204 No Content
        return None
    
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Failed to delete team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete team"
        )
