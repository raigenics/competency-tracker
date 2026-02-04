"""
Profile Service - GET /employees/{employee_id}

Handles employee profile detail with all skills.
Zero dependencies on other services.
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models import Employee, EmployeeSkill

logger = logging.getLogger(__name__)


def get_employee_profile(db: Session, employee_id: int) -> Dict[str, Any]:
    """
    Get detailed employee profile including all skills.
    
    Args:
        db: Database session
        employee_id: The employee ID to fetch
    
    Returns:
        Dict with employee details and skills list
        
    Raises:
        ValueError: If employee not found
    """
    logger.info(f"Fetching employee profile for ID: {employee_id}")
    
    # Query employee with all relationships
    employee = _query_employee_by_id(db, employee_id)
    
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} not found")
    
    # Build profile response
    profile = _build_profile_response(employee)
    
    logger.info(f"Returning profile for '{employee.full_name}' with {len(profile['skills'])} skills")
    return profile


# === DATABASE QUERIES ===

def _query_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
    """
    Query employee by ID with all relationships eager loaded.
    Returns None if not found.
    """
    return db.query(Employee).options(
        joinedload(Employee.sub_segment),
        joinedload(Employee.project),
        joinedload(Employee.team),
        joinedload(Employee.role),
        joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
        joinedload(Employee.employee_skills).joinedload(EmployeeSkill.proficiency_level)
    ).filter(Employee.employee_id == employee_id).first()


# === RESPONSE BUILDING ===

def _build_profile_response(employee: Employee) -> Dict[str, Any]:
    """
    Build complete profile response from employee model.
    Pure function - no DB access.
    """
    skills = _build_skills_list(employee)
    
    return {
        "employee_id": employee.employee_id,
        "zid": employee.zid,
        "full_name": employee.full_name,
        "role": employee.role,
        "start_date_of_working": _format_date(employee.start_date_of_working),
        "organization": _build_organization_dict(employee),
        "skills_count": len(skills),
        "skills": skills
    }


def _build_skills_list(employee: Employee) -> List[Dict[str, Any]]:
    """
    Build skills list from employee_skills relationship.
    Pure function - no DB access.
    """
    skills = []
    
    for emp_skill in employee.employee_skills:
        skill_data = {
            "emp_skill_id": emp_skill.emp_skill_id,
            "employee_id": emp_skill.employee_id,
            "employee_name": employee.full_name,
            "skill_id": emp_skill.skill_id,
            "skill_name": emp_skill.skill.skill_name,
            "proficiency": _build_proficiency_dict(emp_skill.proficiency_level),
            "years_experience": emp_skill.years_experience,
            "last_used": emp_skill.last_used,
            "interest_level": emp_skill.interest_level,
            "last_updated": emp_skill.last_updated
        }
        skills.append(skill_data)
    
    return skills


def _build_organization_dict(employee: Employee) -> Dict[str, str]:
    """
    Build organization dict from employee relationships.
    Pure function - no DB access.
    """
    return {
        "sub_segment": employee.sub_segment.sub_segment_name,
        "project": employee.project.project_name,
        "team": employee.team.team_name
    }


def _build_proficiency_dict(proficiency_level) -> Dict[str, Any]:
    """
    Build proficiency dict from proficiency level model.
    Pure function - no DB access.
    """
    return {
        "proficiency_level_id": proficiency_level.proficiency_level_id,
        "level_name": proficiency_level.level_name,
        "level_description": proficiency_level.level_description
    }


def _format_date(date) -> Optional[str]:
    """
    Format date to ISO string.
    Pure function.
    """
    return date.isoformat() if date else None
