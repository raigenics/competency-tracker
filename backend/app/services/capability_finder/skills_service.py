"""
Skills service for Capability Finder.

Handles fetching all distinct skill names for typeahead/autocomplete.
Isolated from other capability finder use cases.
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import exists

from app.models.skill import Skill
from app.models.employee_skill import EmployeeSkill


def get_all_skills(db: Session) -> List[str]:
    """
    Get all distinct skill names sorted alphabetically.
    
    This is a pure read-only operation with no business logic.
    Skills are fetched from the skills table and sorted A-Z.
    
    Args:
        db: Database session
        
    Returns:
        List of skill names sorted alphabetically (A-Z)
        
    Example:
        >>> skills = get_all_skills(db)
        >>> # ['AWS', 'Azure', 'Docker', 'Kubernetes', 'Python', 'React', ...]
    """
    return _query_all_skills(db)


def get_skill_suggestions(db: Session, query: str = None) -> List[Dict]:
    """
    Get skill suggestions with employee availability metadata.
    
    Returns all master skills with flags indicating:
    - Whether any employees currently have the skill
    - Whether the skill can be selected for search
    
    Skills with employees are ranked first, master-only skills appear after.
    
    Args:
        db: Database session
        query: Optional search query to filter skills
        
    Returns:
        List of skill suggestion dicts with keys:
        - skill_id: int
        - skill_name: str
        - is_employee_available: bool
        - is_selectable: bool
        
    Example:
        >>> suggestions = get_skill_suggestions(db, query="python")
        >>> # [
        >>> #   {'skill_id': 10, 'skill_name': 'Python', 'is_employee_available': True, 'is_selectable': True},
        >>> #   {'skill_id': 42, 'skill_name': 'Python Django', 'is_employee_available': False, 'is_selectable': False}
        >>> # ]
    """
    # Query all skills from master table
    skills_query = db.query(
        Skill.skill_id,
        Skill.skill_name,
        exists().where(
            EmployeeSkill.skill_id == Skill.skill_id
        ).label('has_employees')
    )
    
    # Apply search filter if query provided
    if query and query.strip():
        skills_query = skills_query.filter(
            Skill.skill_name.ilike(f'%{query}%')
        )
    
    # Order by: employee-available first, then alphabetically
    skills_query = skills_query.order_by(
        exists().where(EmployeeSkill.skill_id == Skill.skill_id).desc(),
        Skill.skill_name
    )
    
    results = skills_query.all()
    
    # Transform to dict format
    suggestions = []
    for skill_id, skill_name, has_employees in results:
        suggestions.append({
            'skill_id': skill_id,
            'skill_name': skill_name,
            'is_employee_available': bool(has_employees),
            'is_selectable': bool(has_employees)  # Only selectable if employees exist
        })
    
    return suggestions


def _query_all_skills(db: Session) -> List[str]:
    """
    Query database for all distinct skill names.
    
    DB-only helper - no business logic.
    
    Args:
        db: Database session
        
    Returns:
        List of skill names sorted A-Z
    """
    skills = db.query(Skill.skill_name)\
        .distinct()\
        .order_by(Skill.skill_name)\
        .all()
    
    return [skill[0] for skill in skills]
