"""
Pydantic schemas for RBAC Admin Panel.

These schemas support the Super Admin interface for managing users, roles, and access.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.common import PaginatedResponse


# ============================================================================
# LOOKUP SCHEMAS (for dropdowns and filters)
# ============================================================================

class RoleLookupResponse(BaseModel):
    """Role lookup for dropdown selections."""
    role_id: int = Field(description="Role ID")
    role_code: str = Field(description="Role code (e.g., 'SUPER_ADMIN')")
    role_name: str = Field(description="Role display name")
    description: Optional[str] = Field(None, description="Role description")
    
    class Config:
        from_attributes = True


class ScopeTypeLookupResponse(BaseModel):
    """Scope type lookup for dropdown selections."""
    scope_type_id: int = Field(description="Scope type ID")
    scope_type_code: str = Field(description="Scope type code (e.g., 'SEGMENT', 'PROJECT')")
    scope_name: str = Field(description="Scope display name")
    description: Optional[str] = Field(None, description="Scope type description")
    
    class Config:
        from_attributes = True


class ScopeValueLookupResponse(BaseModel):
    """Scope value lookup for specific scope type."""
    scope_id: int = Field(description="Scope entity ID (segment_id, project_id, team_id, etc.)")
    scope_name: str = Field(description="Scope entity name")
    scope_type: str = Field(description="Scope type this belongs to")
    
    class Config:
        from_attributes = True


# ============================================================================
# ROLE ASSIGNMENT SCHEMAS
# ============================================================================

class RoleAssignmentBadge(BaseModel):
    """Simplified role assignment for badge display in user table."""
    role_name: str = Field(description="Role name")
    scope_type: str = Field(description="Scope type (e.g., 'SEGMENT', 'PROJECT', 'GLOBAL')")
    scope_name: Optional[str] = Field(None, description="Scope entity name (null for GLOBAL)")
    
    class Config:
        from_attributes = True


class UserAssignmentDetail(BaseModel):
    """User assignment detail for Manage Access modal."""
    assignment_id: int = Field(description="Assignment record ID")
    role_code: str = Field(description="Role code (e.g., 'SUPER_ADMIN')")
    role_name: str = Field(description="Role display name")
    scope_type_code: str = Field(description="Scope type code (e.g., 'GLOBAL', 'PROJECT')")
    scope_id: Optional[int] = Field(None, description="Scope entity ID (null for GLOBAL)")
    scope_label: Optional[str] = Field(None, description="Scope entity display name (null for GLOBAL)")
    granted_at: datetime = Field(description="Timestamp when access was granted")
    revoked_at: Optional[datetime] = Field(None, description="Timestamp when revoked (null if active)")
    is_active: bool = Field(description="Whether assignment is currently active")
    
    class Config:
        from_attributes = True


class RoleAssignmentDetail(BaseModel):
    """Detailed role assignment information."""
    assignment_id: int = Field(description="Assignment record ID")
    role_id: int = Field(description="Role ID")
    role_name: str = Field(description="Role name")
    scope_type_id: int = Field(description="Scope type ID")
    scope_type: str = Field(description="Scope type name")
    scope_id: Optional[int] = Field(None, description="Scope entity ID (null for GLOBAL)")
    scope_name: Optional[str] = Field(None, description="Scope entity name (null for GLOBAL)")
    granted_by_user_id: int = Field(description="User ID of admin who granted access")
    granted_by_name: str = Field(description="Full name of admin who granted access")
    granted_at: datetime = Field(description="Timestamp when access was granted")
    is_active: bool = Field(description="Whether assignment is currently active")
    revoked_at: Optional[datetime] = Field(None, description="Timestamp when revoked (null if active)")
    
    class Config:
        from_attributes = True


class CreateRoleAssignmentRequest(BaseModel):
    """Request to create a new role assignment."""
    user_id: int = Field(description="User ID to assign role to")
    role_id: int = Field(description="Role ID to assign")
    scope_type_id: int = Field(description="Scope type ID")
    scope_id: Optional[int] = Field(None, description="Scope entity ID (null for GLOBAL scope)")
    
    @field_validator('scope_id')
    @classmethod
    def validate_scope_id(cls, v, info):
        """Validate that scope_id is provided for non-GLOBAL scopes."""
        # Note: This validation will be enhanced by backend service logic
        # which checks if scope_type requires scope_id
        return v


class RevokeRoleAssignmentRequest(BaseModel):
    """Request to revoke a role assignment."""
    assignment_id: int = Field(description="Assignment ID to revoke")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for revocation")


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserListItem(BaseModel):
    """User list item for User Management table."""
    user_id: int = Field(description="User ID")
    full_name: str = Field(description="User's full name")
    email: EmailStr = Field(description="User's email (used for login)")
    status: str = Field(description="Account status: 'active' or 'inactive'")
    linked_employee_zid: Optional[str] = Field(None, description="ZID of linked employee (if any)")
    linked_employee_name: Optional[str] = Field(None, description="Name of linked employee (if any)")
    role_assignments: List[RoleAssignmentBadge] = Field(
        default_factory=list,
        description="List of role assignments for badge display"
    )
    created_at: datetime = Field(description="When user account was created")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    full_name: str = Field(min_length=1, max_length=255, description="User's full name")
    email: EmailStr = Field(description="User's email (must be unique)")
    password: str = Field(min_length=8, description="Initial password (min 8 characters)")
    status: str = Field(default="active", description="Account status: 'active' or 'inactive'")
    link_to_employee_id: Optional[int] = Field(None, description="Employee ID to link (optional)")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        if v not in ['active', 'inactive']:
            raise ValueError("Status must be 'active' or 'inactive'")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password meets minimum requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Additional password strength validation can be added here
        return v


class CreateUserResponse(BaseModel):
    """Response after creating a new user."""
    user_id: int = Field(description="Created user ID")
    full_name: str = Field(description="User's full name")
    email: EmailStr = Field(description="User's email")
    status: str = Field(description="Account status")
    linked_employee_zid: Optional[str] = Field(None, description="ZID of linked employee (if any)")
    created_at: datetime = Field(description="When user was created")
    message: str = Field(default="User created successfully", description="Success message")
    
    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    """Request to update user details."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated full name")
    status: Optional[str] = Field(None, description="Updated status")
    link_to_employee_id: Optional[int] = Field(None, description="Employee ID to link/unlink")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        if v is not None and v not in ['active', 'inactive']:
            raise ValueError("Status must be 'active' or 'inactive'")
        return v


class UserDetailResponse(BaseModel):
    """Detailed user information including all role assignments."""
    user_id: int = Field(description="User ID")
    full_name: str = Field(description="User's full name")
    email: EmailStr = Field(description="User's email")
    status: str = Field(description="Account status")
    linked_employee_zid: Optional[str] = Field(None, description="ZID of linked employee")
    linked_employee_name: Optional[str] = Field(None, description="Name of linked employee")
    role_assignments: List[RoleAssignmentDetail] = Field(
        default_factory=list,
        description="All role assignments for this user"
    )
    created_at: datetime = Field(description="When user was created")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True


class UserListResponse(PaginatedResponse[UserListItem]):
    """Paginated response for user list."""
    pass


# ============================================================================
# FILTER SCHEMAS
# ============================================================================

class UserFilterParams(BaseModel):
    """Filter parameters for user list."""
    search: Optional[str] = Field(None, description="Search in name or email")
    role_id: Optional[int] = Field(None, description="Filter by role ID")
    scope_type_id: Optional[int] = Field(None, description="Filter by scope type ID")
    status: Optional[str] = Field(None, description="Filter by status")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status filter."""
        if v is not None and v not in ['active', 'inactive']:
            raise ValueError("Status must be 'active' or 'inactive'")
        return v
