"""
API routes for RBAC Admin Panel.

Provides endpoints for Super Admin to manage users, role assignments, and access control.
All operations are logged in the audit log for compliance tracking.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.rbac_admin import (
    RbacAdminService,
    ValidationError,
    NotFoundError,
    ConflictError,
)
from app.schemas.rbac_admin import (
    UserListItem,
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UserDetailResponse,
    UserAssignmentDetail,
    RoleAssignmentDetail,
    CreateRoleAssignmentRequest,
    RevokeRoleAssignmentRequest,
    RoleLookupResponse,
    ScopeTypeLookupResponse,
    ScopeValueLookupResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rbac-admin", tags=["rbac-admin"])


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users", response_model=List[UserListItem])
async def list_users(
    search: Optional[str] = Query(None, description="Search in name or email"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    scope_type_id: Optional[int] = Query(None, description="Filter by scope type ID"),
    user_status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filters.
    
    Returns users with their role assignments for display in the User Management table.
    Supports search, filtering by role/scope/status, and pagination.
    """
    try:
        logger.info(
            f"Listing users: search={search}, role_id={role_id}, "
            f"scope_type_id={scope_type_id}, status={user_status}"
        )
        
        users, total_count = RbacAdminService.list_users(
            db=db,
            search=search,
            role_id=role_id,
            scope_type_id=scope_type_id,
            status=user_status,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"Found {total_count} users, returning {len(users)} records")
        
        return users
        
    except ValidationError as e:
        logger.warning(f"Validation error listing users: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new user account.
    
    Creates user with login credentials and optionally links to an existing employee record.
    Role assignments should be done separately via the assignments endpoint.
    
    Note: Currently uses placeholder admin user ID (1). 
    TODO: Replace with actual authenticated admin user ID from JWT token.
    """
    try:
        # TODO: Get actual admin user ID from authentication context
        admin_user_id = 1
        
        logger.info(f"Creating new user: {user_data.email}")
        
        created_user = RbacAdminService.create_user(
            db=db,
            user_data=user_data,
            created_by_user_id=admin_user_id
        )
        
        logger.info(
            f"User created successfully: {created_user.email} "
            f"(ID: {created_user.user_id})"
        )
        
        return created_user
        
    except ValidationError as e:
        logger.warning(f"Validation error creating user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        logger.warning(f"Resource not found creating user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        logger.warning(f"Conflict creating user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific user.
    
    Returns full user details including all role assignments (both active and revoked).
    Used by the "Manage Access" modal to display current assignments.
    """
    try:
        logger.info(f"Fetching user detail for user ID: {user_id}")
        
        user_detail = RbacAdminService.get_user_detail(db=db, user_id=user_id)
        
        return user_detail
        
    except NotFoundError as e:
        logger.warning(f"User not found: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching user detail: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )


@router.get("/users/{user_id}/assignments", response_model=List[UserAssignmentDetail])
async def get_user_assignments(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user assignments for Manage Access modal.
    
    Returns list of role assignments with resolved scope labels.
    Used by Manage Access modal to display current assignments.
    """
    try:
        logger.info(f"Fetching assignments for user ID: {user_id}")
        
        assignments = RbacAdminService.get_user_assignments(db=db, user_id=user_id)
        
        logger.info(f"Found {len(assignments)} assignments for user {user_id}")
        
        return assignments
        
    except NotFoundError as e:
        logger.warning(f"User not found: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching user assignments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user assignments"
        )


# ============================================================================
# ROLE ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/users/{user_id}/assignments", response_model=RoleAssignmentDetail, status_code=status.HTTP_201_CREATED)
async def create_role_assignment(
    user_id: int,
    assignment_data: CreateRoleAssignmentRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new role assignment for a user.
    
    Assigns a role with specific scope to the user. Creates audit log entry.
    Validates that role, scope type, and scope entity exist before creating.
    Prevents duplicate assignments.
    
    Note: Currently uses placeholder admin user ID (1).
    TODO: Replace with actual authenticated admin user ID from JWT token.
    """
    try:
        # Validate user_id matches path and body
        if assignment_data.user_id != user_id:
            raise ValidationError(
                f"User ID mismatch: path={user_id}, body={assignment_data.user_id}"
            )
        
        # TODO: Get actual admin user ID from authentication context
        admin_user_id = 1
        
        logger.info(
            f"Creating role assignment for user {user_id}: "
            f"role_id={assignment_data.role_id}, "
            f"scope_type_id={assignment_data.scope_type_id}"
        )
        
        created_assignment = RbacAdminService.create_role_assignment(
            db=db,
            assignment_data=assignment_data,
            granted_by_user_id=admin_user_id
        )
        
        logger.info(
            f"Role assignment created successfully: "
            f"ID {created_assignment.assignment_id}"
        )
        
        return created_assignment
        
    except ValidationError as e:
        logger.warning(f"Validation error creating assignment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        logger.warning(f"Resource not found creating assignment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        logger.warning(f"Conflict creating assignment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating role assignment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role assignment"
        )


@router.delete("/users/{user_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role_assignment(
    user_id: int,
    assignment_id: int,
    reason: Optional[str] = Body(None, embed=True, description="Optional reason for revocation"),
    db: Session = Depends(get_db)
):
    """
    Revoke (soft delete) a role assignment.
    
    Marks the assignment as inactive and sets revoked_at timestamp.
    Creates audit log entry with revocation details.
    The assignment record is preserved for historical tracking.
    
    Note: Currently uses placeholder admin user ID (1).
    TODO: Replace with actual authenticated admin user ID from JWT token.
    """
    try:
        # TODO: Get actual admin user ID from authentication context
        admin_user_id = 1
        
        logger.info(
            f"Revoking assignment {assignment_id} for user {user_id} "
            f"by admin {admin_user_id}"
        )
        
        RbacAdminService.revoke_role_assignment(
            db=db,
            assignment_id=assignment_id,
            revoked_by_user_id=admin_user_id,
            reason=reason
        )
        
        logger.info(f"Assignment {assignment_id} revoked successfully")
        logger.info(f"Assignment {assignment_id} revoked successfully")
        
        return None
        
    except ValidationError as e:
        logger.warning(f"Validation error revoking assignment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        logger.warning(f"Assignment not found: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        logger.warning(f"Conflict revoking assignment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error revoking role assignment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke role assignment"
        )


# ============================================================================
# LOOKUP ENDPOINTS
# ============================================================================

@router.get("/lookups/roles", response_model=List[RoleLookupResponse])
async def get_roles(db: Session = Depends(get_db)):
    """
    Get all available roles for dropdown selection.
    
    Returns all roles in the system (SUPER_ADMIN, SEGMENT_HEAD, etc.).
    Used by the role selection dropdown in the Manage Access modal.
    """
    try:
        logger.info("Fetching all roles for lookup")
        
        roles = RbacAdminService.get_all_roles(db=db)
        
        return roles
        
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles"
        )


@router.get("/lookups/scope-types", response_model=List[ScopeTypeLookupResponse])
async def get_scope_types(db: Session = Depends(get_db)):
    """
    Get all available scope types for dropdown selection.
    
    Returns all scope types (GLOBAL, SEGMENT, PROJECT, TEAM, EMPLOYEE).
    Used by filters and scope type selection.
    """
    try:
        logger.info("Fetching all scope types for lookup")
        
        scope_types = RbacAdminService.get_all_scope_types(db=db)
        
        return scope_types
        
    except Exception as e:
        logger.error(f"Error fetching scope types: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scope types"
        )


@router.get("/lookups/scope-values/{scope_type_code}", response_model=List[ScopeValueLookupResponse])
async def get_scope_values(
    scope_type_code: str,
    db: Session = Depends(get_db)
):
    """
    Get all available values for a specific scope type.
    
    Returns list of entities for the specified scope type:
    - GLOBAL: Empty list (no values needed)
    - SEGMENT: Empty list (no Segment model exists yet)
    - SUB_SEGMENT: All sub-segments
    - PROJECT: All projects
    - TEAM: All teams
    - EMPLOYEE: All employees
    
    Used to populate the scope value dropdown after role/scope type selection.
    """
    try:
        logger.info(f"Fetching scope values for scope type: {scope_type_code}")
        
        scope_values = RbacAdminService.get_scope_values(
            db=db,
            scope_type_code=scope_type_code
        )
        
        logger.info(
            f"Found {len(scope_values)} values for scope type {scope_type_code}"
        )
        
        return scope_values
        
    except ValidationError as e:
        logger.warning(f"Invalid scope type: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching scope values: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scope values"
        )

