"""
API routes for employee data management and queries.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db.session import get_db
from app.models import Employee, EmployeeSkill, SubSegment, Project, Team, Role, Skill, ProficiencyLevel
from app.schemas.employee import (
    EmployeeResponse, EmployeeListResponse, 
    EmployeeStatsResponse, OrganizationInfo,
    EmployeesByIdsRequest, EmployeesByIdsResponse, TalentResultItem, SkillInfo,
    EmployeeSuggestion
)
from app.schemas.common import PaginationParams

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
        # Search for employees by full name OR ZID (case-insensitive partial match)
        search_term = f"%{q}%"
        query = db.query(Employee).options(
            joinedload(Employee.sub_segment),
            joinedload(Employee.project),
            joinedload(Employee.team)
        ).filter(
            (Employee.full_name.ilike(search_term)) | 
            (Employee.zid.ilike(search_term))
        ).limit(limit)
        
        employees = query.all()
        
        # Build response
        suggestions = []
        for employee in employees:
            suggestion = EmployeeSuggestion(
                employee_id=employee.employee_id,
                zid=employee.zid,
                full_name=employee.full_name,
                sub_segment=employee.sub_segment.sub_segment_name if employee.sub_segment else None,
                project=employee.project.project_name if employee.project else None,
                team=employee.team.team_name if employee.team else None
            )
            suggestions.append(suggestion)
        
        logger.info(f"Returning {len(suggestions)} suggestions for query: '{q}'")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error fetching employee suggestions: {str(e)}")
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
    logger.info(f"Fetching employees with filters: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}, search={search}, page={pagination.page}, size={pagination.size}")
    
    try:
        # Build query with joins for organization info
        query = db.query(Employee).options(
            joinedload(Employee.sub_segment),
            joinedload(Employee.project),
            joinedload(Employee.team),
            joinedload(Employee.role)
        )
        
        # Apply filters by ID (more efficient than name-based filtering)
        if sub_segment_id:
            query = query.filter(Employee.sub_segment_id == sub_segment_id)
        
        if project_id:
            query = query.filter(Employee.project_id == project_id)
        
        if team_id:
            query = query.filter(Employee.team_id == team_id)
        
        if role_id:
            query = query.filter(Employee.role_id == role_id)
        
        # Search by name or ZID
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Employee.full_name.ilike(search_term)) |
                (Employee.zid.ilike(search_term))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        employees = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Build response data
        response_items = []
        for employee in employees:            # Count skills for this employee
            skills_count = db.query(func.count(EmployeeSkill.emp_skill_id)).filter(
                EmployeeSkill.employee_id == employee.employee_id
            ).scalar()
            
            employee_data = EmployeeResponse(
                employee_id=employee.employee_id,
                zid=employee.zid,
                full_name=employee.full_name,
                role=employee.role,
                start_date_of_working=employee.start_date_of_working,
                organization=OrganizationInfo(
                    sub_segment=employee.sub_segment.sub_segment_name,
                    project=employee.project.project_name,
                    team=employee.team.team_name
                ),
                skills_count=skills_count
            )
            response_items.append(employee_data)
        
        return EmployeeListResponse.create(response_items, total, pagination)
        
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
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
        employee = db.query(Employee).options(
            joinedload(Employee.sub_segment),
            joinedload(Employee.project),
            joinedload(Employee.team),
            joinedload(Employee.role),
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.proficiency_level)
        ).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found"
            )
        
        # Build skills list
        from app.schemas.competency import EmployeeSkillResponse, ProficiencyLevelResponse
        skills = []
        for emp_skill in employee.employee_skills:
            skill_data = {
                "emp_skill_id": emp_skill.emp_skill_id,
                "employee_id": emp_skill.employee_id,
                "employee_name": employee.full_name,
                "skill_id": emp_skill.skill_id,
                "skill_name": emp_skill.skill.skill_name,
                "proficiency": {
                    "proficiency_level_id": emp_skill.proficiency_level.proficiency_level_id,
                    "level_name": emp_skill.proficiency_level.level_name,
                    "level_description": emp_skill.proficiency_level.level_description
                },
                "years_experience": emp_skill.years_experience,
                "last_used": emp_skill.last_used,
                "interest_level": emp_skill.interest_level,
                "last_updated": emp_skill.last_updated
            }
            skills.append(skill_data)
        
        return {
            "employee_id": employee.employee_id,
            "zid": employee.zid,
            "full_name": employee.full_name,
            "role": employee.role,
            "start_date_of_working": employee.start_date_of_working.isoformat() if employee.start_date_of_working else None,
            "organization": {
                "sub_segment": employee.sub_segment.sub_segment_name,
                "project": employee.project.project_name,
                "team": employee.team.team_name
            },
            "skills_count": len(skills),
            "skills": skills
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee {employee_id}: {str(e)}")
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
        # Total employees
        total_employees = db.query(func.count(Employee.employee_id)).scalar()
        
        # Count by sub-segment
        by_sub_segment = dict(
            db.query(SubSegment.sub_segment_name, func.count(Employee.employee_id))
            .join(Employee)
            .group_by(SubSegment.sub_segment_name)
            .all()
        )
        
        # Count by project
        by_project = dict(
            db.query(Project.project_name, func.count(Employee.employee_id))
            .join(Employee)
            .group_by(Project.project_name)
            .all()
        )
        
        # Count by team
        by_team = dict(
            db.query(Team.team_name, func.count(Employee.employee_id))
            .join(Employee)
            .group_by(Team.team_name)
            .all()
        )
        
        # Average skills per employee
        avg_skills = db.query(func.avg(
            db.query(func.count(EmployeeSkill.emp_skill_id))
            .filter(EmployeeSkill.employee_id == Employee.employee_id)
            .scalar_subquery()
        )).scalar()
        
        return EmployeeStatsResponse(
            total_employees=total_employees,
            by_sub_segment=by_sub_segment,
            by_project=by_project,
            by_team=by_team,
            avg_skills_per_employee=round(avg_skills or 0, 2)
        )
        
    except Exception as e:
        logger.error(f"Error fetching employee stats: {str(e)}")
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
        if not request.employee_ids:
            return EmployeesByIdsResponse(results=[])
        
        # Fetch employees with organization info
        employees = db.query(Employee)\
            .options(
                joinedload(Employee.sub_segment),
                joinedload(Employee.project),
                joinedload(Employee.team),
                joinedload(Employee.role)
            )\
            .filter(Employee.employee_id.in_(request.employee_ids))\
            .all()
        
        results = []
        
        for employee in employees:
            # Fetch top skills for this employee (ordered by proficiency desc)
            top_skills_query = db.query(
                Skill.skill_name,
                ProficiencyLevel.proficiency_level_id
            )\
                .join(EmployeeSkill, EmployeeSkill.skill_id == Skill.skill_id)\
                .join(ProficiencyLevel, EmployeeSkill.proficiency_level_id == ProficiencyLevel.proficiency_level_id)\
                .filter(EmployeeSkill.employee_id == employee.employee_id)\
                .order_by(ProficiencyLevel.proficiency_level_id.desc(), Skill.skill_name.asc())\
                .limit(10)\
                .all()
            
            top_skills = [
                SkillInfo(name=skill_name, proficiency=proficiency)
                for skill_name, proficiency in top_skills_query
            ]
            
            # Get organization info
            sub_segment_name = employee.sub_segment.sub_segment_name if employee.sub_segment else ""
            team_name = employee.team.team_name if employee.team else ""
            role_name = employee.role.role_name if employee.role else ""
            
            results.append(TalentResultItem(
                id=employee.employee_id,
                name=employee.full_name,
                subSegment=sub_segment_name,
                team=team_name,
                role=role_name,
                skills=top_skills
            ))
        
        logger.info(f"Returning {len(results)} employees")
        return EmployeesByIdsResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error fetching employees by IDs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees: {str(e)}"
        )
