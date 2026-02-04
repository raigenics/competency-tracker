"""
Dashboard Section: Top Skills by Employee Count

PUBLIC ENTRYPOINT:
- get_top_skills(db, sub_segment_id, project_id, team_id, limit) -> List[Dict[str, Any]]

HELPERS:
- _build_base_query() - DB query construction
- _apply_scope_filters() - Apply hierarchical filters
- _execute_and_format() - Execute query and format results

OUTPUT CONTRACT (MUST NOT CHANGE):
- Returns list of dicts with keys: skill, total, expert, proficient
- Ordered by total (descending)
- Limited by limit parameter

QUERY LOGIC:
- Joins: Skill -> EmployeeSkill -> Employee
- Aggregates: COUNT DISTINCT employees, SUM CASE for proficiency levels
- Proficiency levels: expert (>=4), proficient (=3)

ISOLATION:
- This file is self-contained and does NOT import from other dashboard sections.
- Changes here must NOT affect other dashboard sections.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.models import Employee, EmployeeSkill, Skill


def get_top_skills(
    db: Session,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get top skills by employee count within the selected scope.
    
    Returns skills ranked by number of employees who have them,
    with breakdown by proficiency level.
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
        limit: Maximum number of skills to return
    
    Returns:
        List of dicts with keys:
        - skill: Skill name
        - total: Total count of distinct employees
        - expert: Count of employees with proficiency_level_id >= 4
        - proficient: Count of employees with proficiency_level_id == 3
    """
    # Build base query
    query = _build_base_query(db)
    
    # Apply scope filters
    query = _apply_scope_filters(query, sub_segment_id, project_id, team_id)
    
    # Execute and format results
    return _execute_and_format(query, limit)


def _build_base_query(db: Session):
    """
    Build base query for top skills aggregation.
    
    Joins Skill -> EmployeeSkill -> Employee and aggregates by skill.
    Calculates total employee count and counts by proficiency level.
    
    Args:
        db: Database session
    
    Returns:
        SQLAlchemy query object (not yet executed)
    """
    query = db.query(
        Skill.skill_name,
        func.count(func.distinct(EmployeeSkill.employee_id)).label('total'),
        func.sum(case((EmployeeSkill.proficiency_level_id >= 4, 1), else_=0)).label('expert'),
        func.sum(case((EmployeeSkill.proficiency_level_id == 3, 1), else_=0)).label('proficient')
    ).join(EmployeeSkill, Skill.skill_id == EmployeeSkill.skill_id
    ).join(Employee, EmployeeSkill.employee_id == Employee.employee_id)
    
    return query


def _apply_scope_filters(query, sub_segment_id, project_id, team_id):
    """
    Apply hierarchical scope filters to query.
    
    Filter hierarchy: Team > Project > Sub-Segment > Organization
    Most specific filter wins.
    
    Args:
        query: Base SQLAlchemy query
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        Filtered query object
    """
    if team_id:
        query = query.filter(Employee.team_id == team_id)
    elif project_id:
        query = query.filter(Employee.project_id == project_id)
    elif sub_segment_id:
        query = query.filter(Employee.sub_segment_id == sub_segment_id)
    
    return query


def _execute_and_format(query, limit: int) -> List[Dict[str, Any]]:
    """
    Execute query, group, order, limit, and format results.
    
    Pure data transformation after query execution.
    
    Args:
        query: SQLAlchemy query ready for execution
        limit: Maximum number of results
    
    Returns:
        List of formatted skill dicts
    """
    # Group by skill and order by total count descending
    results = query.group_by(Skill.skill_id, Skill.skill_name
    ).order_by(desc('total')
    ).limit(limit).all()
    
    # Format results
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
