"""
API routes for dashboard metrics and analytics.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import OrgSkillCoverageResponse
from app.models import Employee, EmployeeSkill, Skill, SubSegment, Project, Team, EmployeeSkillHistory

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
          # Build base query
        query = db.query(
            Skill.skill_name,
            func.count(func.distinct(EmployeeSkill.employee_id)).label('total'),
            func.sum(case((EmployeeSkill.proficiency_level_id >= 4, 1), else_=0)).label('expert'),
            func.sum(case((EmployeeSkill.proficiency_level_id == 3, 1), else_=0)).label('proficient')
        ).join(EmployeeSkill, Skill.skill_id == EmployeeSkill.skill_id
        ).join(Employee, EmployeeSkill.employee_id == Employee.employee_id)
        
        # Apply filters
        if team_id:
            query = query.filter(Employee.team_id == team_id)
        elif project_id:
            query = query.filter(Employee.project_id == project_id)
        elif sub_segment_id:
            query = query.filter(Employee.sub_segment_id == sub_segment_id)
        
        # Group and order
        results = query.group_by(Skill.skill_id, Skill.skill_name
        ).order_by(desc('total')
        ).limit(limit).all()
        
        skills = [
            {
                "skill": row.skill_name,
                "total": row.total,
                "expert": row.expert or 0,
                "proficient": row.proficient or 0
            }
            for row in results
        ]
        
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
    from datetime import datetime, timedelta
    
    try:
        logger.info(f"Fetching skill momentum: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}")
        
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        six_months_ago = now - timedelta(days=180)
        
        # Build base query for employees in scope
        employee_filter = db.query(Employee.employee_id)
        if team_id:
            employee_filter = employee_filter.filter(Employee.team_id == team_id)
        elif project_id:
            employee_filter = employee_filter.filter(Employee.project_id == project_id)
        elif sub_segment_id:
            employee_filter = employee_filter.filter(Employee.sub_segment_id == sub_segment_id)
        
        employee_ids = [e[0] for e in employee_filter.all()]
        
        if not employee_ids:
            return {
                "updated_last_3_months": 0,
                "updated_last_6_months": 0,
                "not_updated_6_months": 0
            }
        
        # Count skills updated in last 3 months
        updated_3m = db.query(func.count(func.distinct(EmployeeSkill.emp_skill_id))).filter(
            EmployeeSkill.employee_id.in_(employee_ids),
            EmployeeSkill.last_updated >= three_months_ago
        ).scalar() or 0
        
        # Count skills updated between 3-6 months ago
        updated_6m = db.query(func.count(func.distinct(EmployeeSkill.emp_skill_id))).filter(
            EmployeeSkill.employee_id.in_(employee_ids),
            EmployeeSkill.last_updated >= six_months_ago,
            EmployeeSkill.last_updated < three_months_ago
        ).scalar() or 0
        
        # Count skills not updated in 6 months
        not_updated = db.query(func.count(func.distinct(EmployeeSkill.emp_skill_id))).filter(
            EmployeeSkill.employee_id.in_(employee_ids),
            EmployeeSkill.last_updated < six_months_ago
        ).scalar() or 0
        
        return {
            "updated_last_3_months": updated_3m,
            "updated_last_6_months": updated_6m,
            "not_updated_6_months": not_updated
        }
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
    from datetime import datetime, timedelta
    
    try:
        logger.info(f"Fetching skill update activity: days={days}, sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}")
        
        # Validate days parameter
        if days <= 0 or days > 365:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Days must be between 1 and 365")
        
        now = datetime.utcnow()
        cutoff_date = now - timedelta(days=days)
        stagnant_cutoff = now - timedelta(days=180)
          # Build base query for employees in scope
        employee_filter = db.query(Employee.employee_id)
        if team_id:
            employee_filter = employee_filter.filter(Employee.team_id == team_id)
        elif project_id:
            employee_filter = employee_filter.filter(Employee.project_id == project_id)
        elif sub_segment_id:
            employee_filter = employee_filter.filter(Employee.sub_segment_id == sub_segment_id)
        
        employee_ids = [e[0] for e in employee_filter.all()]
        
        if not employee_ids:
            return {
                "days": days,
                "total_updates": 0,
                "active_learners": 0,
                "low_activity": 0,
                "stagnant_180_days": 0
            }
        
        # Count updates per employee in last N days
        updates_per_employee = db.query(
            EmployeeSkill.employee_id,
            func.count(EmployeeSkill.emp_skill_id).label('update_count')
        ).filter(
            EmployeeSkill.employee_id.in_(employee_ids),
            EmployeeSkill.last_updated >= cutoff_date
        ).group_by(EmployeeSkill.employee_id).all()
        
        update_counts_dict = {emp_id: count for emp_id, count in updates_per_employee}
        
        # DISTINCT employees with >= 1 update in last N days
        total_updates = len([emp_id for emp_id, count in update_counts_dict.items() if count >= 1])
        
        # Active learners: DISTINCT employees with >= 2 updates in last N days
        active_learners = sum(1 for count in update_counts_dict.values() if count >= 2)
        
        # Low activity: DISTINCT employees with 0-1 updates in last N days (from employees in scope)
        low_activity = len(employee_ids) - active_learners
        
        # Stagnant: DISTINCT employees with no updates in last 180 days
        employees_with_recent_updates = db.query(func.distinct(EmployeeSkill.employee_id)).filter(
            EmployeeSkill.employee_id.in_(employee_ids),
            EmployeeSkill.last_updated >= stagnant_cutoff
        ).all()
        
        employees_with_recent_updates_set = {e[0] for e in employees_with_recent_updates}
        stagnant_180_days = len(employee_ids) - len(employees_with_recent_updates_set)
        
        return {
            "days": days,
            "total_updates": total_updates,
            "active_learners": active_learners,
            "low_activity": low_activity,
            "stagnant_180_days": stagnant_180_days
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skill update activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill update activity data"
        )