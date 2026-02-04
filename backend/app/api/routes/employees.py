"""
API routes for employee data management and queries.

Thin controller pattern - all business logic delegated to services.
Each endpoint maps to one service module with zero cross-dependencies.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.employee import (
    EmployeeListResponse, 
    EmployeeStatsResponse,
    EmployeesByIdsRequest, EmployeesByIdsResponse,
    EmployeeSuggestion
)
from app.schemas.common import PaginationParams

# Service layer imports - isolated business logic
from app.services.employee_profile import suggest_service
from app.services.employee_profile import list_service
from app.services.employee_profile import profile_service
from app.services.employee_profile import stats_service
from app.services.employee_profile import by_ids_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/suggest", response_model=List[EmployeeSuggestion])
async def suggest_employees(
    q: str = Query(..., min_length=2, description="Search query for employee name or ZID"),
    limit: int = Query(8, ge=1, le=20, description="Maximum number of suggestions to return"),
    db: Session = Depends(get_db)
):
    """
    Get employee suggestions for autocomplete.
    
    - **q**: Search query (minimum 2 characters) - searches both name and ZID
    - **limit**: Maximum number of results (1-20, default 8)
    """
    logger.info(f"Fetching employee suggestions for query: '{q}' with limit: {limit}")
    
    try:
        suggestions = suggest_service.get_employee_suggestions(db, q, limit)
        logger.info(f"Returning {len(suggestions)} suggestions for query: '{q}'")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error fetching employee suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employee suggestions"
        )


@router.get("/", response_model=EmployeeListResponse)
async def get_employees(
    pagination: PaginationParams = Depends(),
    sub_segment_id: Optional[int] = Query(None, description="Filter by sub-segment ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    search: Optional[str] = Query(None, description="Search by name or ZID"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of employees with optional filters.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 10)
    - **sub_segment_id**: Filter by sub-segment ID
    - **project_id**: Filter by project ID
    - **team_id**: Filter by team ID
    - **role_id**: Filter by role ID
    - **search**: Search by employee name or ZID
    """
    logger.info(f"Fetching employees with filters: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}, role_id={role_id}, search={search}, page={pagination.page}, size={pagination.size}")
    
    try:
        return list_service.get_employees_paginated(
            db=db,
            pagination=pagination,
            sub_segment_id=sub_segment_id,
            project_id=project_id,
            team_id=team_id,
            role_id=role_id,
            search=search
        )
        
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employees"
        )


@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific employee including their skills.
    """
    logger.info(f"Fetching employee details for ID: {employee_id}")
    
    try:
        return profile_service.get_employee_profile(db, employee_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee {employee_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employee details"
        )


@router.get("/stats/overview", response_model=EmployeeStatsResponse)
async def get_employee_stats(db: Session = Depends(get_db)):
    """
    Get employee statistics and overview.
    """
    logger.info("Fetching employee statistics")
    
    try:
        return stats_service.get_employee_stats(db)
        
    except Exception as e:
        logger.error(f"Error fetching employee stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employee statistics"
        )


@router.post("/by-ids", response_model=EmployeesByIdsResponse)
async def get_employees_by_ids(
    request: EmployeesByIdsRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch employees by a list of employee IDs.
    Returns employee data formatted for TalentResultsTable component.
    
    Args:
        request: Contains list of employee_ids
        
    Returns:
        List of employees with top skills, formatted for frontend table
    """
    logger.info(f"Fetching {len(request.employee_ids)} employees by IDs")
    
    try:
        response = by_ids_service.get_employees_by_ids(db, request.employee_ids)
        logger.info(f"Returning {len(response.results)} employees")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching employees by IDs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees: {str(e)}"
        )
