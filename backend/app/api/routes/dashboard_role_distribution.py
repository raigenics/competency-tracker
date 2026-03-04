"""
API route for Dashboard Role Distribution section.

Provides a single endpoint to get role distribution data with dynamic
title, subtitle, and breakdown rows based on filter context.

ENDPOINT:
- GET /api/dashboard/role-distribution

QUERY PARAMS:
- segment_id: int (required)
- sub_segment_id: int | null
- project_id: int | null
- team_id: int | null
- top_n: int (default 3)
- max_roles: int (default 10)
- include_empty: bool (default true)
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.role_distribution import RoleDistributionResponse
from app.services.dashboard.role_distribution_service import (
    get_role_distribution,
    result_to_dict,
    EntityNotFoundError,
    InvalidHierarchyError
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/role-distribution",
    response_model=RoleDistributionResponse,
    responses={
        200: {"description": "Role distribution data retrieved successfully"},
        400: {"description": "Invalid parameters or hierarchy"},
        404: {"description": "Entity not found"},
        500: {"description": "Internal server error"}
    },
    summary="Get Role Distribution",
    description="""
    Get role distribution data for the dashboard section.
    
    **Context Resolution:**
    - No sub_segment_id → SEGMENT context (breakdown = sub-segments)
    - sub_segment_id only → SUB_SEGMENT context (breakdown = projects)
    - sub_segment_id + project_id → PROJECT context (breakdown = teams)
    - All provided → TEAM context (single team row)
    
    **Response includes:**
    - Dynamic title/subtitle based on context
    - Breakdown rows with total employees and role counts
    - Top N roles for inline display (chips)
    - All roles (up to max_roles) for expanded panel
    - more_roles_count for "+X more" indicator
    """
)
async def get_role_distribution_endpoint(
    segment_id: int = Query(
        ..., 
        description="Segment ID (required for all contexts)",
        ge=1
    ),
    sub_segment_id: Optional[int] = Query(
        None, 
        description="Filter by sub-segment ID",
        ge=1
    ),
    project_id: Optional[int] = Query(
        None, 
        description="Filter by project ID (requires sub_segment_id)",
        ge=1
    ),
    team_id: Optional[int] = Query(
        None, 
        description="Filter by team ID (requires project_id)",
        ge=1
    ),
    top_n: int = Query(
        3, 
        description="Number of top roles for inline chips",
        ge=1,
        le=10
    ),
    max_roles: int = Query(
        10, 
        description="Maximum roles to return in all_roles",
        ge=1,
        le=50
    ),
    include_empty: bool = Query(
        True, 
        description="Include breakdown items with zero employees"
    ),
    db: Session = Depends(get_db)
):
    """
    Get role distribution data for the dashboard Role Distribution section.
    
    Returns breakdown rows with role counts based on the current filter context.
    Each row includes top roles for inline chips and all roles for the
    expandable panel.
    """
    try:
        logger.info(
            f"Fetching role distribution: segment_id={segment_id}, "
            f"sub_segment_id={sub_segment_id}, project_id={project_id}, "
            f"team_id={team_id}, top_n={top_n}, max_roles={max_roles}, "
            f"include_empty={include_empty}"
        )
        
        # Call service to get role distribution data
        result = get_role_distribution(
            db=db,
            segment_id=segment_id,
            sub_segment_id=sub_segment_id,
            project_id=project_id,
            team_id=team_id,
            top_n=top_n,
            max_roles=max_roles,
            include_empty=include_empty
        )
        
        # Convert to response dict
        response_data = result_to_dict(result, top_n=top_n)
        
        logger.info(
            f"Role distribution retrieved: context_level={result.context_level}, "
            f"rows_count={len(result.rows)}"
        )
        
        return response_data
        
    except EntityNotFoundError as e:
        logger.warning(f"Entity not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except InvalidHierarchyError as e:
        logger.warning(f"Invalid hierarchy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error fetching role distribution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve role distribution data"
        )
