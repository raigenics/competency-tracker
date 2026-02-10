"""
Roles service for fetching role data.

SRP: Handles all role-related read operations.
Read-only service - does not create or modify roles.
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.role import Role


def get_all_roles(db: Session) -> List[dict]:
    """
    Get all roles with id and name, sorted alphabetically.
    
    Returns list of role objects with role_id and role_name.
    Used by Role/Designation dropdown in Add Employee form.
    
    Args:
        db: Database session
        
    Returns:
        List of dicts with role_id and role_name
    """
    roles = db.query(Role)\
        .order_by(Role.role_name)\
        .all()
    
    return [
        {
            "role_id": role.role_id,
            "role_name": role.role_name
        }
        for role in roles
    ]


def get_role_by_id(db: Session, role_id: int) -> dict | None:
    """
    Get a single role by ID.
    
    Args:
        db: Database session
        role_id: ID of the role to fetch
        
    Returns:
        Role dict or None if not found
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    
    if not role:
        return None
    
    return {
        "role_id": role.role_id,
        "role_name": role.role_name
    }
