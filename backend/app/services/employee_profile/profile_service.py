"""
Profile Service - GET /employees/{employee_id}

Handles employee profile detail with all skills.
Zero dependencies on other services.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models import Employee, EmployeeSkill
from app.models.employee_project_allocation import EmployeeProjectAllocation

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
    start_time = time.time()
    logger.info(f"[PERF] get_employee_profile START | employee_id={employee_id}")
    
    # Query employee with all relationships
    query_start = time.time()
    employee = _query_employee_by_id(db, employee_id)
    query_time = time.time() - query_start
    logger.info(f"[PERF] get_employee_profile QUERY | employee_id={employee_id} | query_time={query_time*1000:.1f}ms")
    
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} not found")
    
    # Build profile response
    build_start = time.time()
    profile = _build_profile_response(employee)
    build_time = time.time() - build_start
    
    total_time = time.time() - start_time
    logger.info(f"[PERF] get_employee_profile END | employee_id={employee_id} | query={query_time*1000:.1f}ms | build={build_time*1000:.1f}ms | total={total_time*1000:.1f}ms | skills_count={len(profile['skills'])}")
    return profile


# === DATABASE QUERIES ===

def _query_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
    """
    Query employee by ID with all relationships eager loaded.
    Returns None if not found.
    
    NORMALIZED SCHEMA: sub_segment/project derived via team relationship chain.
    """
    from app.models.team import Team
    from app.models.project import Project
    from app.models.sub_segment import SubSegment
    
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
    ).filter(Employee.employee_id == employee_id).first()


# === RESPONSE BUILDING ===

def _build_profile_response(employee: Employee) -> Dict[str, Any]:
    """
    Build complete profile response from employee model.
    Pure function - no DB access.
    """
    skills = _build_skills_list(employee)
    org_ids = _extract_org_ids(employee)
    
    return {
        "employee_id": employee.employee_id,
        "zid": employee.zid,
        "full_name": employee.full_name,
        "email": employee.email,
        "role": _build_role_dict(employee.role),
        "start_date_of_working": _format_date(employee.start_date_of_working),
        "organization": _build_organization_dict(employee),
        # Org IDs for edit form dropdown preselection
        "team_id": org_ids["team_id"],
        "project_id": org_ids["project_id"],
        "sub_segment_id": org_ids["sub_segment_id"],
        "segment_id": org_ids["segment_id"],
        "skills_count": len(skills),
        "skills": skills,
        # Project allocation percentage for current project
        "allocation": _get_current_allocation(employee)
    }


def _extract_org_ids(employee: Employee) -> Dict[str, Optional[int]]:
    """
    Extract all org hierarchy IDs from employee via relationship chain.
    Returns dict with team_id, project_id, sub_segment_id, segment_id.
    """
    team = employee.team
    project = team.project if team else None
    sub_segment = project.sub_segment if project else None
    segment = sub_segment.segment if sub_segment else None
    
    return {
        "team_id": employee.team_id,
        "project_id": project.project_id if project else None,
        "sub_segment_id": sub_segment.sub_segment_id if sub_segment else None,
        "segment_id": segment.segment_id if segment else None
    }


def _build_role_dict(role) -> Optional[Dict[str, Any]]:
    """
    Build role dict from role model.
    Returns None if no role assigned.
    """
    if not role:
        return None
    return {
        "role_id": role.role_id,
        "role_name": role.role_name
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
            "started_learning_from": emp_skill.started_learning_from,
            "certification": emp_skill.certification,
            "interest_level": emp_skill.interest_level,
            "last_updated": emp_skill.last_updated
        }
        skills.append(skill_data)
    
    return skills


def _build_organization_dict(employee: Employee) -> Dict[str, str]:
    """
    Build organization dict from employee relationships.
    Pure function - no DB access.
    
    NORMALIZED SCHEMA: Derives sub_segment/project via team relationship.
    Returns empty strings for missing relationships to preserve API contract.
    """
    team = employee.team
    project = team.project if team else None
    sub_segment = project.sub_segment if project else None
    
    return {
        "sub_segment": sub_segment.sub_segment_name if sub_segment else "",
        "project": project.project_name if project else "",
        "team": team.team_name if team else ""
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


def _get_current_allocation(employee: Employee) -> Optional[int]:
    """
    Get the current project allocation percentage for the employee.
    
    Finds the active allocation (end_date IS NULL) for the employee's current project.
    Returns None if no active allocation exists.
    """
    if not employee.project_allocations:
        return None
    
    current_project_id = employee.project_id
    if not current_project_id:
        return None
    
    # Find the active allocation for current project
    for allocation in employee.project_allocations:
        if allocation.project_id == current_project_id and allocation.end_date is None:
            return allocation.allocation_pct
    
    return None
