"""
Roles service for role CRUD operations.

SRP: Handles all role-related operations.
Supports soft delete pattern (deleted_at, deleted_by).
"""
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.role import Role
from app.models.employee import Employee

logger = logging.getLogger(__name__)


def _check_role_name_duplicate(
    db: Session, 
    role_name: str, 
    exclude_role_id: Optional[int] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if role_name conflicts with existing role names or alias tokens.
    
    Args:
        db: Database session
        role_name: Name to check
        exclude_role_id: Role ID to exclude from check (for updates)
        
    Returns:
        Tuple of (is_duplicate, conflict_message, conflict_role_name)
        - (False, None, None) if no conflict
        - (True, message, conflict_role_name) if conflict found
    """
    normalized_name = role_name.strip().lower()
    if not normalized_name:
        return (False, None, None)
    
    # Build base query for active roles
    query = db.query(Role).filter(Role.deleted_at.is_(None))
    
    if exclude_role_id is not None:
        query = query.filter(Role.role_id != exclude_role_id)
    
    # Check 1: role_name matches existing role_name (case-insensitive)
    existing_by_name = query.filter(
        func.lower(func.trim(Role.role_name)) == normalized_name
    ).first()
    
    if existing_by_name:
        return (True, f"Role '{role_name}' already exists", existing_by_name.role_name)
    
    # Check 2: role_name matches any alias token
    # Fetch roles that have non-null aliases and check in Python
    # This is efficient because we only fetch rows with aliases
    roles_with_aliases = query.filter(
        Role.role_alias.isnot(None),
        Role.role_alias != ''
    ).all()
    
    for role in roles_with_aliases:
        if role.role_alias:
            # Split by comma and check each token
            alias_tokens = [t.strip().lower() for t in role.role_alias.split(',') if t.strip()]
            if normalized_name in alias_tokens:
                return (True, f"'{role_name}' conflicts with the existing role '{role.role_name}'", role.role_name)
    
    return (False, None, None)


def get_all_roles(db: Session) -> List[dict]:
    """
    Get all active roles with id, name, and description, sorted alphabetically.
    Filters out soft-deleted roles (deleted_at IS NOT NULL).
    
    Returns list of role objects.
    Used by Role management table and dropdowns.
    
    Args:
        db: Database session
        
    Returns:
        List of dicts with role_id, role_name, role_description
    """
    roles = db.query(Role)\
        .filter(Role.deleted_at.is_(None))\
        .order_by(Role.role_name)\
        .all()
    
    return [
        {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "role_alias": role.role_alias,
            "role_description": role.role_description
        }
        for role in roles
    ]


def get_role_by_id(db: Session, role_id: int) -> dict | None:
    """
    Get a single active role by ID.
    Returns None if not found or soft-deleted.
    
    Args:
        db: Database session
        role_id: ID of the role to fetch
        
    Returns:
        Role dict or None if not found
    """
    role = db.query(Role)\
        .filter(Role.role_id == role_id)\
        .filter(Role.deleted_at.is_(None))\
        .first()
    
    if not role:
        return None
    
    return {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "role_alias": role.role_alias,
        "role_description": role.role_description
    }


def create_role(db: Session, role_name: str, role_alias: Optional[str] = None, role_description: Optional[str] = None, created_by: str = "system") -> dict:
    """
    Create a new role.
    
    Args:
        db: Database session
        role_name: Name of the role
        role_alias: Optional comma-separated alias names
        role_description: Optional description
        created_by: User creating the role
        
    Returns:
        Created role dict
        
    Raises:
        ValueError: If role_name conflicts with existing role name or alias
    """
    # Validate name
    validated_name = role_name.strip()
    if not validated_name:
        raise ValueError("Role name cannot be empty")
    
    # Check for duplicates
    is_duplicate, conflict_msg, _ = _check_role_name_duplicate(db, validated_name)
    if is_duplicate:
        raise ValueError(conflict_msg)
    
    new_role = Role(
        role_name=validated_name,
        role_alias=role_alias.strip() if role_alias else None,
        role_description=role_description.strip() if role_description else None,
        created_at=datetime.now(timezone.utc),
        created_by=created_by
    )
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return {
        "role_id": new_role.role_id,
        "role_name": new_role.role_name,
        "role_alias": new_role.role_alias,
        "role_description": new_role.role_description
    }


def update_role(db: Session, role_id: int, role_name: str, role_alias: Optional[str] = None, role_description: Optional[str] = None) -> dict | None:
    """
    Update an existing role.
    
    Args:
        db: Database session
        role_id: ID of the role to update
        role_name: New name for the role
        role_alias: New alias (optional, comma-separated)
        role_description: New description (optional)
        
    Returns:
        Updated role dict or None if not found
        
    Raises:
        ValueError: If role_name conflicts with existing role name or alias
    """
    role = db.query(Role)\
        .filter(Role.role_id == role_id)\
        .filter(Role.deleted_at.is_(None))\
        .first()
    
    if not role:
        return None
    
    # Validate name
    validated_name = role_name.strip()
    if not validated_name:
        raise ValueError("Role name cannot be empty")
    
    # Check for duplicates (excluding self)
    is_duplicate, conflict_msg, _ = _check_role_name_duplicate(db, validated_name, exclude_role_id=role_id)
    if is_duplicate:
        raise ValueError(conflict_msg)
    
    role.role_name = validated_name
    role.role_alias = role_alias.strip() if role_alias else None
    role.role_description = role_description.strip() if role_description else None
    
    db.commit()
    db.refresh(role)
    
    return {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "role_alias": role.role_alias,
        "role_description": role.role_description
    }


def delete_role(db: Session, role_id: int, deleted_by: str = "system") -> bool:
    """
    Soft delete a role by setting deleted_at and deleted_by.
    
    Args:
        db: Database session
        role_id: ID of the role to delete
        deleted_by: User deleting the role
        
    Returns:
        True if deleted, False if not found
    """
    role = db.query(Role)\
        .filter(Role.role_id == role_id)\
        .filter(Role.deleted_at.is_(None))\
        .first()
    
    if not role:
        return False
    
    role.deleted_at = datetime.now(timezone.utc)
    role.deleted_by = deleted_by
    
    db.commit()
    return True


def delete_roles_bulk(db: Session, role_ids: List[int], deleted_by: str = "system") -> int:
    """
    Soft delete multiple roles at once.
    
    Args:
        db: Database session
        role_ids: List of role IDs to delete
        deleted_by: User deleting the roles
        
    Returns:
        Number of roles deleted
    """
    now = datetime.now(timezone.utc)
    
    updated_count = db.query(Role)\
        .filter(Role.role_id.in_(role_ids))\
        .filter(Role.deleted_at.is_(None))\
        .update(
            {"deleted_at": now, "deleted_by": deleted_by},
            synchronize_session=False
        )
    
    db.commit()
    return updated_count


def check_role_dependencies(db: Session, role_id: int) -> Dict[str, int]:
    """
    Check if a role has any dependencies (employees assigned).
    Only counts active employees (deleted_at IS NULL).
    
    Args:
        db: Database session
        role_id: ID of the role to check
        
    Returns:
        Dict with dependency counts, e.g. {"employees": 5}
    """
    employee_count = db.query(func.count(Employee.employee_id))\
        .filter(Employee.role_id == role_id)\
        .filter(Employee.deleted_at.is_(None))\
        .scalar() or 0
    
    dependencies = {}
    if employee_count > 0:
        dependencies["employees"] = employee_count
    
    return dependencies


def check_roles_dependencies_bulk(db: Session, role_ids: List[int]) -> List[Dict]:
    """
    Check if multiple roles have any dependencies (employees assigned).
    Only counts active employees (deleted_at IS NULL).
    Uses a single efficient query with GROUP BY.
    
    Args:
        db: Database session
        role_ids: List of role IDs to check
        
    Returns:
        List of blocked roles with counts, e.g. [{"role_id": 1, "employees": 5}]
    """
    # Single query to get employee counts per role_id
    results = db.query(
        Employee.role_id,
        func.count(Employee.employee_id).label('employee_count')
    )\
        .filter(Employee.role_id.in_(role_ids))\
        .filter(Employee.deleted_at.is_(None))\
        .group_by(Employee.role_id)\
        .all()
    
    blocked = []
    for role_id, employee_count in results:
        if employee_count > 0:
            blocked.append({
                "role_id": role_id,
                "employees": employee_count
            })
    
    return blocked
