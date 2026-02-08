"""
Search service for Capability Finder.

Handles searching for employees matching specified skill and organizational criteria.
Uses AND logic for required skills (employee must have ALL specified skills).

Isolated from export service - no shared helpers to ensure changes in search
cannot break export functionality.

PHASE 1 BEHAVIORAL NORMALIZATION:
- Organizational filters now use join-based derivation (team_id is canonical)
- No longer filters directly on Employee.sub_segment_id
- Canonical: employee.team_id -> team.project_id -> project.sub_segment_id
- API contracts unchanged (returns same schema objects)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func, and_

from app.models.skill import Skill
from app.models.role import Role
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill
from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo
from app.services.utils.org_query_helpers import apply_org_filters


def search_matching_talent(
    db: Session,
    skills: List[str],
    sub_segment_id: Optional[int] = None,
    team_id: Optional[int] = None,
    role: Optional[str] = None,
    min_proficiency: int = 0,
    min_experience_years: int = 0
) -> List[EmployeeSearchResult]:
    """
    Search for employees matching specified criteria.
    
    Skills filter uses AND logic - employees must have ALL specified skills
    at or above the minimum proficiency and experience levels.
    
    Args:
        db: Database session
        skills: List of required skill names (AND logic - must have ALL)
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        role: Optional role name filter
        min_proficiency: Minimum proficiency level (0-5, applies to required skills)
        min_experience_years: Minimum years of experience (applies to required skills)
        
    Returns:
        List of matching employees with their top 3 skills
        
    Example:
        >>> results = search_matching_talent(
        ...     db=db,
        ...     skills=['Python', 'AWS'],
        ...     min_proficiency=3,
        ...     team_id=5
        ... )
        >>> # Returns employees who have BOTH Python AND AWS with proficiency >= 3
    """
    # Query employees matching filters
    employees = _query_matching_employees(
        db=db,
        skills=skills,
        sub_segment_id=sub_segment_id,
        team_id=team_id,
        role=role,
        min_proficiency=min_proficiency,
        min_experience_years=min_experience_years
    )
    
    # Build results with top 3 skills for each employee
    results = []
    for employee in employees:
        top_skills = _query_employee_top_skills(db, employee.employee_id)
        employee_result = _build_employee_result(employee, top_skills)
        results.append(employee_result)
    
    return results


def _query_matching_employees(
    db: Session,
    skills: List[str],
    sub_segment_id: Optional[int],
    team_id: Optional[int],
    role: Optional[str],
    min_proficiency: int,
    min_experience_years: int
) -> List[Employee]:
    """
    Query employees matching all specified filters.
    
    DB-only helper - constructs and executes the employee query.
    
    Args:
        db: Database session
        skills: Required skill names (AND logic)
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        role: Optional role name filter
        min_proficiency: Minimum proficiency level
        min_experience_years: Minimum years of experience
        
    Returns:
        List of Employee objects matching all filters
    """
    # Build base query
    query = db.query(Employee).join(EmployeeSkill).join(Skill)
    
    # Build filters list
    filters = []
    
    # Skills filter with AND logic
    if skills and len(skills) > 0:
        skill_ids = _query_skill_ids(db, skills)
        
        if skill_ids:
            # Subquery to find employees who have ALL required skills
            # with minimum proficiency and experience
            skill_subquery = db.query(EmployeeSkill.employee_id)\
                .filter(
                    EmployeeSkill.skill_id.in_(skill_ids),
                    EmployeeSkill.proficiency_level_id >= min_proficiency,
                    EmployeeSkill.years_experience >= min_experience_years
                )\
                .group_by(EmployeeSkill.employee_id)\
                .having(func.count(distinct(EmployeeSkill.skill_id)) == len(skill_ids))
            
            filters.append(Employee.employee_id.in_(skill_subquery))
    
    # Organization filters
    # PHASE 1 NORMALIZATION: Use centralized join-based filtering
    # OLD: Direct filters on Employee.sub_segment_id, Employee.team_id
    # NEW: Join-based derivation through canonical helper
    # Note: team_id still direct (it's the canonical FK), sub_segment_id via joins
    if sub_segment_id or team_id:
        # Need to apply org filters to the base Employee query
        # But we already joined Employee, so we filter on the existing query
        if team_id:
            filters.append(Employee.team_id == team_id)
        elif sub_segment_id:
            # PHASE 1 NORMALIZATION: Derive sub_segment via Team->Project join
            # OLD: Employee.sub_segment_id == sub_segment_id (direct redundant column)
            # NEW: Must join through Team -> Project to derive sub_segment membership
            # Import locally to avoid these models being loaded too early
            from app.models.team import Team
            from app.models.project import Project
            # Base query only joins Employee->EmployeeSkill->Skill, so safe to join Team/Project
            query = query.join(Team, Employee.team_id == Team.team_id)
            query = query.join(Project, Team.project_id == Project.project_id)
            filters.append(Project.sub_segment_id == sub_segment_id)
    
    if role:
        query = query.join(Role, Employee.role_id == Role.role_id)
        filters.append(Role.role_name == role)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Get distinct employees
    return query.distinct().all()


def _query_skill_ids(db: Session, skill_names: List[str]) -> List[int]:
    """
    Query skill IDs for given skill names.
    
    DB-only helper - no business logic.
    
    Args:
        db: Database session
        skill_names: List of skill names
        
    Returns:
        List of skill IDs
    """
    skill_ids = db.query(Skill.skill_id)\
        .filter(Skill.skill_name.in_(skill_names))\
        .all()
    
    return [s[0] for s in skill_ids]


def _query_employee_top_skills(db: Session, employee_id: int) -> List[tuple]:
    """
    Query top 3 skills for an employee.
    
    Skills are ordered by:
    1. Proficiency level (DESC)
    2. Last used date (DESC)
    3. Skill name (ASC)
    
    DB-only helper - no business logic.
    
    Args:
        db: Database session
        employee_id: Employee ID
        
    Returns:
        List of tuples (skill_name, proficiency_level_id)
    """
    top_skills_query = db.query(
        Skill.skill_name,
        EmployeeSkill.proficiency_level_id
    )\
        .join(EmployeeSkill, EmployeeSkill.skill_id == Skill.skill_id)\
        .filter(EmployeeSkill.employee_id == employee_id)\
        .order_by(
            EmployeeSkill.proficiency_level_id.desc(),
            EmployeeSkill.last_used.desc(),
            Skill.skill_name.asc()
        )\
        .limit(3)\
        .all()
    
    return top_skills_query


def _build_employee_result(
    employee: Employee,
    top_skills: List[tuple]
) -> EmployeeSearchResult:
    """
    Build EmployeeSearchResult from employee and top skills data.
    
    Pure transformation helper - no DB access, no side effects.
    
    Args:
        employee: Employee model instance
        top_skills: List of tuples (skill_name, proficiency_level_id)
        
    Returns:
        EmployeeSearchResult schema object
    """
    # Transform top skills to SkillInfo objects
    skills_info = [
        SkillInfo(name=skill_name, proficiency=proficiency)
        for skill_name, proficiency in top_skills
    ]
    
    # Extract organization info
    sub_segment_name = employee.sub_segment.sub_segment_name if employee.sub_segment else ""
    team_name = employee.team.team_name if employee.team else ""
    role_name = employee.role.role_name if employee.role else ""
    
    # Build result object
    return EmployeeSearchResult(
        employee_id=employee.employee_id,
        employee_name=employee.full_name,
        sub_segment=sub_segment_name,
        team=team_name,
        role=role_name,
        top_skills=skills_info
    )
