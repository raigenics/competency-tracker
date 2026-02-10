"""
API routes for role/designation data.

Thin controller - delegates to roles_service.
Read-only endpoints for fetching roles.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dropdown import RoleDropdown
from app.services import roles_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleDropdown])
async def get_roles(db: Session = Depends(get_db)):
    """
    Get all roles for dropdown/autosuggest.
    
    Returns list of roles with role_id and role_name, sorted alphabetically.
    Used by Role/Designation field in Add Employee form.
    """
    logger.info("Fetching all roles")
    
    try:
        roles = roles_service.get_all_roles(db)
        logger.info(f"Returning {len(roles)} roles")
        return roles
        
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching roles"
        )


@router.get("/{role_id}", response_model=RoleDropdown)
async def get_role(role_id: int, db: Session = Depends(get_db)):
    """
    Get a single role by ID.
    
    Args:
        role_id: ID of the role to fetch
        
    Returns:
        Role with role_id and role_name
        
    Raises:
        404: If role not found
    """
    logger.info(f"Fetching role with ID: {role_id}")
    
    role = roles_service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return role
