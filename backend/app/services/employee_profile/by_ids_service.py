"""
Service for fetching employees by a list of IDs.

Handles: POST /employees/by-ids
Returns employee data formatted for TalentResultsTable component.

Architecture:
- Public method: get_employees_by_ids(db, employee_ids)
- Query function: _query_employees_by_ids() - fetches employees with organization
- Query function: _query_top_skills() - fetches top skills for single employee
- Pure function: _build_talent_result_items() - transforms to TalentResultItem list
- Pure function: _build_skill_info_list() - transforms skills to SkillInfo list
- Pure function: _build_organization_values() - extracts organization strings

NO dependencies on other services.
100% backward compatible with original implementation.
"""

from typing import List, Tuple
from sqlalchemy.orm import Session, joinedload
from app.models import Employee, EmployeeSkill, Skill, ProficiencyLevel
from app.schemas.employee import EmployeesByIdsResponse, TalentResultItem, SkillInfo


def get_employees_by_ids(
    db: Session,
    employee_ids: List[int]
) -> EmployeesByIdsResponse:
    """
    Fetch employees by list of IDs with top skills.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs to fetch
        
    Returns:
        EmployeesByIdsResponse with list of TalentResultItem
        
    Example:
        response = get_employees_by_ids(db, [1, 2, 3])
        # Returns employees with top 10 skills each
    """
    if not employee_ids:
        return EmployeesByIdsResponse(results=[])
    
    employees = _query_employees_by_ids(db, employee_ids)
    results = _build_talent_result_items(db, employees)
    
    return EmployeesByIdsResponse(results=results)


def _query_employees_by_ids(
    db: Session,
    employee_ids: List[int]
) -> List[Employee]:
    """
    Query employees by list of IDs with organization relationships.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs
        
    Returns:
        List of Employee objects with eager-loaded relationships
        
    NORMALIZED SCHEMA: sub_segment/project derived via team relationship chain.
    """
    from app.models.team import Team
    from app.models.project import Project
    
    return db.query(Employee)\
        .options(
            # Canonical chain: team -> project -> sub_segment
            joinedload(Employee.team)
                .joinedload(Team.project)
                .joinedload(Project.sub_segment),
            joinedload(Employee.role)
        )\
        .filter(Employee.employee_id.in_(employee_ids))\
        .all()


def _query_top_skills(
    db: Session,
    employee_id: int,
    limit: int = 10
) -> List[Tuple[str, int]]:
    """
    Query top skills for a single employee.
    
    Args:
        db: Database session
        employee_id: Employee ID
        limit: Maximum number of skills to return (default 10)
        
    Returns:
        List of tuples: [(skill_name, proficiency_level_id), ...]
        Ordered by proficiency desc, then skill name asc
        
    Example:
        skills = _query_top_skills(db, 123)
        # [("Python", 5), ("SQL", 4), ("JavaScript", 3), ...]
    """
    return db.query(
        Skill.skill_name,
        ProficiencyLevel.proficiency_level_id
    )\
        .join(EmployeeSkill, EmployeeSkill.skill_id == Skill.skill_id)\
        .join(ProficiencyLevel, EmployeeSkill.proficiency_level_id == ProficiencyLevel.proficiency_level_id)\
        .filter(EmployeeSkill.employee_id == employee_id)\
        .order_by(ProficiencyLevel.proficiency_level_id.desc(), Skill.skill_name.asc())\
        .limit(limit)\
        .all()


def _build_talent_result_items(
    db: Session,
    employees: List[Employee]
) -> List[TalentResultItem]:
    """
    Transform Employee objects to TalentResultItem list.
    
    Args:
        db: Database session (needed for querying skills)
        employees: List of Employee objects
        
    Returns:
        List of TalentResultItem with top skills
        
    Note:
        This function queries the database for skills (not pure),
        but transforms the employee data to match frontend expectations.
    """
    results = []
    
    for employee in employees:
        # Fetch top skills for this employee
        top_skills_data = _query_top_skills(db, employee.employee_id)
        top_skills = _build_skill_info_list(top_skills_data)
        
        # Extract organization info
        sub_segment, team, role = _build_organization_values(employee)
        
        results.append(TalentResultItem(
            id=employee.employee_id,
            name=employee.full_name,
            subSegment=sub_segment,
            team=team,
            role=role,
            skills=top_skills
        ))
    
    return results


def _build_skill_info_list(
    skills_data: List[Tuple[str, int]]
) -> List[SkillInfo]:
    """
    Transform skill query results to SkillInfo list.
    
    Args:
        skills_data: List of (skill_name, proficiency_level_id) tuples
        
    Returns:
        List of SkillInfo objects
        
    Example:
        skills = _build_skill_info_list([("Python", 5), ("SQL", 4)])
        # [SkillInfo(name="Python", proficiency=5), SkillInfo(name="SQL", proficiency=4)]
    """
    return [
        SkillInfo(name=skill_name, proficiency=proficiency)
        for skill_name, proficiency in skills_data
    ]


def _build_organization_values(employee: Employee) -> Tuple[str, str, str]:
    """
    Extract organization values from employee relationships.
    
    Args:
        employee: Employee object with loaded relationships
        
    Returns:
        Tuple of (sub_segment_name, team_name, role_name)
        Empty strings if relationship not loaded
        
    Example:
        sub, team, role = _build_organization_values(employee)
        # ("Engineering", "Backend Team", "Developer")
    """
    sub_segment_name = employee.sub_segment.sub_segment_name if employee.sub_segment else ""
    team_name = employee.team.team_name if employee.team else ""
    role_name = employee.role.role_name if employee.role else ""
    
    return sub_segment_name, team_name, role_name
