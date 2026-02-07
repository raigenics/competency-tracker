"""
RBAC Admin Service - Main facade for RBAC Admin Panel.

This service acts as a facade/orchestrator that delegates to specialized services:
- UserService: User CRUD operations
- AssignmentService: Role assignment operations
- LookupService: Dropdown/lookup data
- AuditService: Audit logging
- PasswordService: Password hashing (placeholder)
- ScopeResolver: Scope entity name resolution

This maintains backward compatibility with existing router code while providing
a clean, SRP-compliant architecture.
"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

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
from app.services.rbac_admin.user_service import UserService
from app.services.rbac_admin.assignment_service import AssignmentService
from app.services.rbac_admin.lookup_service import LookupService
from app.services.rbac_admin.password_service import PasswordService

logger = logging.getLogger(__name__)


class RbacAdminService:
    """
    Facade service for RBAC Admin Panel operations.
    
    Delegates to specialized services while maintaining backward compatibility
    with existing router code.
    """

    # ========================================================================
    # PASSWORD UTILITIES (delegated to PasswordService)
    # ========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password (delegates to PasswordService).
        
        ⚠️  SECURITY WARNING: Currently using placeholder implementation!
        """
        return PasswordService.hash_password(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password (delegates to PasswordService).
        
        ⚠️  SECURITY WARNING: Currently using placeholder implementation!
        """
        return PasswordService.verify_password(plain_password, hashed_password)

    # ========================================================================
    # USER MANAGEMENT (delegated to UserService)
    # ========================================================================

    @staticmethod
    def list_users(
        db: Session,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        scope_type_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UserListItem], int]:
        """List users with filters and pagination (delegates to UserService)."""
        return UserService.list_users(
            db=db,
            search=search,
            role_id=role_id,
            scope_type_id=scope_type_id,
            status=status,
            skip=skip,
            limit=limit
        )

    @staticmethod
    def create_user(
        db: Session,
        user_data: CreateUserRequest,
        created_by_user_id: int
    ) -> CreateUserResponse:
        """Create a new user (delegates to UserService)."""
        return UserService.create_user(
            db=db,
            user_data=user_data,
            created_by_user_id=created_by_user_id
        )

    @staticmethod
    def get_user_detail(db: Session, user_id: int) -> UserDetailResponse:
        """Get detailed user information (delegates to UserService)."""
        return UserService.get_user_detail(db=db, user_id=user_id)

    @staticmethod
    def get_user_assignments(db: Session, user_id: int) -> List[UserAssignmentDetail]:
        """Get user assignments for Manage Access modal (delegates to UserService)."""
        return UserService.get_user_assignments(db=db, user_id=user_id)

    # ========================================================================
    # ROLE ASSIGNMENT MANAGEMENT (delegated to AssignmentService)
    # ========================================================================

    @staticmethod
    def create_role_assignment(
        db: Session,
        assignment_data: CreateRoleAssignmentRequest,
        granted_by_user_id: int
    ) -> RoleAssignmentDetail:
        """Create a role assignment (delegates to AssignmentService)."""
        return AssignmentService.create_role_assignment(
            db=db,
            assignment_data=assignment_data,
            granted_by_user_id=granted_by_user_id
        )

    @staticmethod
    def revoke_role_assignment(
        db: Session,
        assignment_id: int,
        revoked_by_user_id: int,
        reason: Optional[str] = None
    ) -> None:
        """Revoke a role assignment (delegates to AssignmentService)."""
        return AssignmentService.revoke_role_assignment(
            db=db,
            assignment_id=assignment_id,
            revoked_by_user_id=revoked_by_user_id,
            reason=reason
        )

    # ========================================================================
    # LOOKUP OPERATIONS (delegated to LookupService)
    # ========================================================================

    @staticmethod
    def get_all_roles(db: Session) -> List[RoleLookupResponse]:
        """Get all roles (delegates to LookupService)."""
        return LookupService.get_all_roles(db=db)

    @staticmethod
    def get_all_scope_types(db: Session) -> List[ScopeTypeLookupResponse]:
        """Get all scope types (delegates to LookupService)."""
        return LookupService.get_all_scope_types(db=db)

    @staticmethod
    def get_scope_values(
        db: Session,
        scope_type_code: str
    ) -> List[ScopeValueLookupResponse]:
        """Get scope values (delegates to LookupService)."""
        return LookupService.get_scope_values(
            db=db,
            scope_type_code=scope_type_code
        )

    @staticmethod
    def search_employees(db: Session, search: str = "") -> List[dict]:
        """Search employees (delegates to LookupService)."""
        return LookupService.search_employees(db=db, search=search)
