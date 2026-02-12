"""
Edit Bootstrap Service - GET /employees/{employee_id}/edit-bootstrap

Returns all data needed to render the Edit Employee form in ONE call:
- Employee data with org hierarchy IDs
- All dropdown options (segments, sub-segments, projects, teams, roles)
- Employee skills with proficiency IDs

Eliminates frontend waterfall calls for dropdown cascades.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models import Employee, EmployeeSkill
from app.models.team import Team
from app.models.project import Project
from app.models.sub_segment import SubSegment
from app.models.segment import Segment
from app.models.role import Role
from app.models.employee_project_allocation import EmployeeProjectAllocation

logger = logging.getLogger(__name__)


def get_edit_bootstrap(db: Session, employee_id: int) -> Dict[str, Any]:
    """
    Get all data needed to render the Edit Employee form.
    
    Performs optimized queries to fetch:
    1. Employee with org hierarchy (team -> project -> sub_segment -> segment)
    2. All dropdown options in parallel
    3. Employee skills with proficiency levels
    
    Args:
        db: Database session
        employee_id: The employee ID to fetch
        
    Returns:
        Dict with employee, options, skills, and meta
        
    Raises:
        ValueError: If employee not found
    """
    logger.info(f"[EDIT-BOOTSTRAP] START employee_id={employee_id}")
    
    # Query employee with all relationships
    employee = _query_employee_with_relationships(db, employee_id)
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} not found")
    
    # Build response components
    employee_data = _build_employee_data(employee)
    options = _build_all_dropdown_options(db)
    skills = _build_skills_list(employee)
    
    logger.info(f"[EDIT-BOOTSTRAP] END employee_id={employee_id} skills={len(skills)}")
    
    return {
        "employee": employee_data,
        "options": options,
        "skills": skills,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }


# === DATABASE QUERIES ===

def _query_employee_with_relationships(db: Session, employee_id: int) -> Optional[Employee]:
    """
    Query employee by ID with all relationships eager loaded.
    Single query with joins for employee + org hierarchy + skills.
    """
    return db.query(Employee).options(
        # Canonical chain: team -> project -> sub_segment -> segment
        joinedload(Employee.team)
            .joinedload(Team.project)
            .joinedload(Project.sub_segment)
            .joinedload(SubSegment.segment),
        joinedload(Employee.role),
        joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
        joinedload(Employee.employee_skills).joinedload(EmployeeSkill.proficiency_level),
        joinedload(Employee.project_allocations)
    ).filter(
        Employee.employee_id == employee_id,
        Employee.deleted_at.is_(None)
    ).first()


def _build_all_dropdown_options(db: Session) -> Dict[str, List[Dict]]:
    """
    Fetch all dropdown options in minimal queries.
    Returns all segments, sub_segments, projects, teams, and roles.
    """
    # Query all dimension tables (5 simple queries, can run in parallel if needed)
    segments = db.query(Segment).order_by(Segment.segment_name).all()
    sub_segments = db.query(SubSegment).order_by(SubSegment.sub_segment_name).all()
    projects = db.query(Project).order_by(Project.project_name).all()
    teams = db.query(Team).order_by(Team.team_name).all()
    roles = db.query(Role).order_by(Role.role_name).all()
    
    return {
        "segments": [
            {"segment_id": s.segment_id, "segment_name": s.segment_name}
            for s in segments
        ],
        "sub_segments": [
            {
                "sub_segment_id": ss.sub_segment_id,
                "sub_segment_name": ss.sub_segment_name,
                "segment_id": ss.segment_id
            }
            for ss in sub_segments
        ],
        "projects": [
            {
                "project_id": p.project_id,
                "project_name": p.project_name,
                "sub_segment_id": p.sub_segment_id
            }
            for p in projects
        ],
        "teams": [
            {
                "team_id": t.team_id,
                "team_name": t.team_name,
                "project_id": t.project_id
            }
            for t in teams
        ],
        "roles": [
            {"role_id": r.role_id, "role_name": r.role_name}
            for r in roles
        ]
    }


# === RESPONSE BUILDING ===

def _build_employee_data(employee: Employee) -> Dict[str, Any]:
    """
    Build employee data dict from employee model.
    Extracts org IDs via relationship chain.
    """
    # Extract org hierarchy IDs
    team = employee.team
    project = team.project if team else None
    sub_segment = project.sub_segment if project else None
    segment = sub_segment.segment if sub_segment else None
    
    return {
        "employee_id": employee.employee_id,
        "zid": employee.zid,
        "full_name": employee.full_name,
        "email": employee.email,
        "role_id": employee.role_id,
        "team_id": employee.team_id,
        "project_id": project.project_id if project else None,
        "sub_segment_id": sub_segment.sub_segment_id if sub_segment else None,
        "segment_id": segment.segment_id if segment else None,
        "start_date_of_working": (
            employee.start_date_of_working.isoformat() 
            if employee.start_date_of_working else None
        ),
        "allocation": _get_current_allocation(employee, project)
    }


def _get_current_allocation(employee: Employee, project: Optional[Project]) -> Optional[int]:
    """
    Get the current project allocation percentage.
    
    Finds the active allocation (end_date IS NULL) for the employee's current project.
    Returns None if no active allocation exists.
    """
    if not employee.project_allocations or not project:
        return None
    
    current_project_id = project.project_id
    
    # Find the active allocation for current project
    for allocation in employee.project_allocations:
        if allocation.project_id == current_project_id and allocation.end_date is None:
            return allocation.allocation_pct
    
    return None


# Mapping from database proficiency name to frontend enum
PROFICIENCY_NAME_TO_ENUM = {
    'Novice': 'NOVICE',
    'Advanced Beginner': 'ADVANCED_BEGINNER',
    'Competent': 'COMPETENT',
    'Proficient': 'PROFICIENT',
    'Expert': 'EXPERT'
}


def _build_skills_list(employee: Employee) -> List[Dict[str, Any]]:
    """
    Build skills list from employee_skills relationship.
    Returns all fields needed by frontend Skills tab.
    """
    logger.info(f"[BUILD_SKILLS_LIST] Called for employee with {len(employee.employee_skills)} skills")
    skills = []
    
    for emp_skill in employee.employee_skills:
        proficiency = emp_skill.proficiency_level
        proficiency_name = proficiency.level_name if proficiency else None
        proficiency_enum = PROFICIENCY_NAME_TO_ENUM.get(proficiency_name, '') if proficiency_name else ''
        
        # Parse last_used date into month/year components
        last_used_month = ''
        last_used_year = ''
        if emp_skill.last_used:
            last_used_month = f"{emp_skill.last_used.month:02d}"
            last_used_year = str(emp_skill.last_used.year)
        
        # Format started_learning_from as ISO date string (YYYY-MM-DD)
        started_from = ''
        if emp_skill.started_learning_from:
            started_from = emp_skill.started_learning_from.isoformat()
        
        skills.append({
            "emp_skill_id": emp_skill.emp_skill_id,
            "skill_id": emp_skill.skill_id,
            "skill_name": emp_skill.skill.skill_name,
            "proficiency_level_id": proficiency.proficiency_level_id if proficiency else None,
            "proficiency_level_name": proficiency_name,
            "proficiency_enum": proficiency_enum,
            "years_experience": emp_skill.years_experience,
            "last_used_month": last_used_month,
            "last_used_year": last_used_year,
            "started_from": started_from,
            "certification": emp_skill.certification or ''
        })
    
    return skills
