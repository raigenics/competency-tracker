"""
API routes for role/designation CRUD operations.

Thin controller - delegates to roles_service.
Supports Create, Read, Update, and Soft Delete operations.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.schemas.dropdown import RoleDropdown
from app.schemas.role import RoleCreate, RoleResponse
from app.services import roles_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])


class BulkDeleteRequest(BaseModel):
    """Request body for bulk delete operation."""
    role_ids: List[int] = Field(..., min_length=1, description="List of role IDs to delete")


class BulkDeleteResponse(BaseModel):
    """Response for bulk delete operation."""
    deleted_count: int = Field(description="Number of roles deleted")


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


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    """
    Create a new role.
    
    Args:
        role_data: Role name and optional description
        
    Returns:
        Created role with role_id, role_name, role_description
    """
    logger.info(f"Creating new role: {role_data.role_name}")
    
    try:
        # TODO: Get actual user from auth when available
        created_by = "system"
        
        role = roles_service.create_role(
            db=db,
            role_name=role_data.role_name,
            role_description=role_data.role_description,
            created_by=created_by
        )
        
        logger.info(f"Created role with ID: {role['role_id']}")
        return role
        
    except Exception as e:
        logger.error(f"Error creating role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating role"
        )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role_data: RoleCreate, db: Session = Depends(get_db)):
    """
    Update an existing role.
    
    Args:
        role_id: ID of the role to update
        role_data: New role name and optional description
        
    Returns:
        Updated role with role_id, role_name, role_description
        
    Raises:
        404: If role not found or already deleted
    """
    logger.info(f"Updating role with ID: {role_id}")
    
    try:
        role = roles_service.update_role(
            db=db,
            role_id=role_id,
            role_name=role_data.role_name,
            role_description=role_data.role_description
        )
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        logger.info(f"Updated role with ID: {role_id}")
        return role
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating role"
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    """
    Soft delete a role by ID.
    Sets deleted_at and deleted_by instead of removing from database.
    
    Args:
        role_id: ID of the role to delete
        
    Raises:
        404: If role not found or already deleted
        409: If role has dependencies (employees assigned)
    """
    logger.info(f"Deleting role with ID: {role_id}")
    
    try:
        # Check for dependencies first
        dependencies = roles_service.check_role_dependencies(db, role_id)
        if dependencies:
            logger.warning(f"Role {role_id} has dependencies: {dependencies}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies": dependencies
                }
            )
        
        # TODO: Get actual user from auth when available
        deleted_by = "system"
        
        success = roles_service.delete_role(db, role_id, deleted_by)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        logger.info(f"Soft-deleted role with ID: {role_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting role"
        )


@router.delete("/", response_model=BulkDeleteResponse)
async def delete_roles_bulk(request: BulkDeleteRequest, db: Session = Depends(get_db)):
    """
    Soft delete multiple roles at once.
    
    Args:
        request: Object containing list of role_ids to delete
        
    Returns:
        Number of roles deleted
        
    Raises:
        409: If any roles have dependencies (employees assigned)
    """
    logger.info(f"Bulk deleting {len(request.role_ids)} roles")
    
    try:
        # Check for dependencies first
        blocked = roles_service.check_roles_dependencies_bulk(db, request.role_ids)
        if blocked:
            total_employees = sum(item["employees"] for item in blocked)
            logger.warning(f"Bulk delete blocked: {len(blocked)} roles have dependencies")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies_found": True,
                    "blocked": blocked,
                    "total_employees": total_employees
                }
            )
        
        # TODO: Get actual user from auth when available
        deleted_by = "system"
        
        deleted_count = roles_service.delete_roles_bulk(db, request.role_ids, deleted_by)
        
        logger.info(f"Soft-deleted {deleted_count} roles")
        return {"deleted_count": deleted_count}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting roles"
        )
