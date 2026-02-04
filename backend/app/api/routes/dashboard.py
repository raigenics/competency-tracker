"""
API routes for dashboard metrics and analytics.

This file contains ONLY route definitions. All business logic is delegated to
isolated service classes to ensure changes in one dashboard section don't break others.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.services.dashboard.top_skills_service import get_top_skills as get_top_skills_service
from app.services.dashboard.skill_momentum_service import get_skill_momentum as get_skill_momentum_service
from app.services.dashboard.skill_update_activity_service import (
    get_skill_update_activity as get_skill_update_activity_service,
    InvalidDaysParameterError
)
from app.schemas.dashboard import OrgSkillCoverageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/employee-scope")
async def get_employee_scope(
    sub_segment_id: Optional[int] = Query(None, description="Filter by sub-segment ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    db: Session = Depends(get_db)
):
    """
    Get employee count and scope information based on filters.
    Returns the count of employees within the selected scope.
    """
    try:
        logger.info(f"Fetching employee scope: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}")
        count, scope_level, scope_name = DashboardService.get_employee_scope_count(
            db, sub_segment_id, project_id, team_id
        )
        return {
            "total_employees": count,
            "scope_level": scope_level.lower(),
            "scope_name": scope_name
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching employee scope: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employee scope data"
        )


@router.get("/top-skills")
async def get_top_skills(
    sub_segment_id: Optional[int] = Query(None, description="Filter by sub-segment ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    limit: int = Query(10, description="Number of top skills to return"),
    db: Session = Depends(get_db)
):
    """
    Get top skills by employee count within the selected scope.
    Returns skills ranked by number of employees who have them.
    """
    try:
        logger.info(f"Fetching top skills: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}")
        skills = get_top_skills_service(db, sub_segment_id, project_id, team_id, limit)
        return skills
    except Exception as e:
        logger.error(f"Error fetching top skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top skills data"
        )


@router.get("/skill-momentum")
async def get_skill_momentum(
    sub_segment_id: Optional[int] = Query(None, description="Filter by sub-segment ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    db: Session = Depends(get_db)
):
    """
    Get skill progress momentum - counts of skill updates in different time periods.
    """
    try:
        logger.info(f"Fetching skill momentum: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}")
        momentum_data = get_skill_momentum_service(db, sub_segment_id, project_id, team_id)
        return momentum_data
    except Exception as e:
        logger.error(f"Error fetching skill momentum: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill momentum data"
        )


@router.get("/org-skill-coverage", response_model=OrgSkillCoverageResponse)
async def get_org_skill_coverage(db: Session = Depends(get_db)):
    """
    Get organization-wide skill coverage by sub-segment and role.
    
    This endpoint returns comprehensive skill coverage data across all sub-segments,
    showing employee counts by role category and certification percentages.
    Data is always organization-wide and ignores any dashboard filters.
    
    Returns:
        OrgSkillCoverageResponse: Contains sub-segment breakdown and organization totals
    """
    try:
        logger.info("Fetching organization-wide skill coverage data")
        coverage_data = DashboardService.get_org_skill_coverage(db)
        logger.info(f"Successfully retrieved skill coverage data for {len(coverage_data.get('sub_segments', []))} sub-segments")
        return coverage_data
    except Exception as e:
        logger.error(f"Error fetching organization skill coverage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization skill coverage data"
        )


@router.get("/skill-update-activity")
async def get_skill_update_activity(
    days: int = Query(90, description="Time window in days for activity analysis"),
    sub_segment_id: Optional[int] = Query(None, description="Filter by sub-segment ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    db: Session = Depends(get_db)
):
    """
    Get skill update activity metrics based on employee skill update timestamps.
    
    Returns:
        - total_updates: DISTINCT employees with >= 1 update in last N days
        - active_learners: DISTINCT employees with >= 2 updates in last N days
        - low_activity: DISTINCT employees with 0-1 updates in last N days
        - stagnant_180_days: DISTINCT employees with no updates in last 180 days
    """
    try:
        logger.info(f"Fetching skill update activity: days={days}, sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}")
        activity_data = get_skill_update_activity_service(db, days, sub_segment_id, project_id, team_id)
        return activity_data
    except InvalidDaysParameterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skill update activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill update activity data"
        )