"""
Skills service for Capability Finder.

Handles fetching all distinct skill names for typeahead/autocomplete.
Isolated from other capability finder use cases.
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.skill import Skill


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
