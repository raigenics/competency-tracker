"""
Roles service for Capability Finder.

Handles fetching all distinct role names for typeahead/autocomplete.
Isolated from other capability finder use cases.
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.role import Role


def get_all_roles(db: Session) -> List[str]:
    """
    Get all distinct role names sorted alphabetically.
    
    This is a pure read-only operation with no business logic.
    Roles are fetched from the roles table and sorted A-Z.
    
    Args:
        db: Database session
        
    Returns:
        List of role names sorted alphabetically (A-Z)
        
    Example:
        >>> roles = get_all_roles(db)
        >>> # ['Analyst', 'Developer', 'Manager', 'Tester', ...]
    """
    return _query_all_roles(db)


def _query_all_roles(db: Session) -> List[str]:
    """
    Query database for all distinct role names.
    
    DB-only helper - no business logic.
    
    Args:
        db: Database session
        
    Returns:
        List of role names sorted A-Z
    """
    roles = db.query(Role.role_name)\
        .distinct()\
        .order_by(Role.role_name)\
        .all()
    
    return [role[0] for role in roles]
