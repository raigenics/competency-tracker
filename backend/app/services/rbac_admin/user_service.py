"""
User management service for RBAC Admin.

Handles user CRUD operations: create, list, get details, and update.
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.auth.user import User
from app.models.auth.user_employee_link import UserEmployeeLink
from app.models.auth.auth_user_scope_role import AuthUserScopeRole
from app.models.employee import Employee
from app.schemas.rbac_admin import (
    UserListItem,
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UserDetailResponse,
    RoleAssignmentBadge,
    RoleAssignmentDetail,
    UserAssignmentDetail,
)
from app.services.rbac_admin.errors import NotFoundError, ConflictError, ValidationError
from app.services.rbac_admin.password_service import PasswordService
from app.services.rbac_admin.audit_service import AuditService
from app.services.rbac_admin.scope_resolver import ScopeResolver

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""

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
        """
        List users with filters and pagination.
        
        Args:
            db: Database session
            search: Search in full_name or email
            role_id: Filter by role ID
            scope_type_id: Filter by scope type ID
            status: Filter by status ('active' or 'inactive')
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
        
        Returns:
            Tuple of (list of UserListItem, total_count)
        """
        # Start with base query including eager loading
        query = db.query(User).options(
            joinedload(User.employee_link).joinedload(UserEmployeeLink.employee),
            joinedload(User.scope_roles).joinedload(AuthUserScopeRole.role),
            joinedload(User.scope_roles).joinedload(AuthUserScopeRole.scope_type)
        )

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        if status:
            # Convert 'active'/'inactive' string to Boolean
            is_active = (status.lower() == 'active')
            query = query.filter(User.is_active == is_active)

        # Role and scope type filters require joining with role assignments
        if role_id or scope_type_id:
            query = query.join(User.scope_roles)
            query = query.filter(AuthUserScopeRole.is_active == True)
            
            if role_id:
                query = query.filter(AuthUserScopeRole.role_id == role_id)
            
            if scope_type_id:
                query = query.filter(AuthUserScopeRole.scope_type_id == scope_type_id)
            
            # Distinct to avoid duplicates when user has multiple assignments
            query = query.distinct()

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination and execute
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        # Transform to response schema
        user_list_items = []
        for user in users:
            # Build role assignment badges
            role_badges = []
            for assignment in user.scope_roles:
                if assignment.is_active:
                    scope_name = ScopeResolver.get_scope_entity_name(
                        db, assignment.scope_type_id, assignment.scope_id
                    )
                    role_badges.append(
                        RoleAssignmentBadge(
                            role_name=assignment.role.role_name,
                            scope_type=assignment.scope_type.scope_type_code,
                            scope_name=scope_name
                        )
                    )

            # Get linked employee info
            linked_employee_zid = None
            linked_employee_name = None
            if user.employee_link and user.employee_link.employee:
                linked_employee_zid = user.employee_link.employee.zid
                linked_employee_name = user.employee_link.employee.full_name

            user_list_items.append(
                UserListItem(
                    user_id=user.user_id,
                    full_name=user.full_name,
                    email=user.email,
                    status='active' if user.is_active else 'inactive',
                    linked_employee_zid=linked_employee_zid,
                    linked_employee_name=linked_employee_name,
                    role_assignments=role_badges,
                    created_at=user.created_at,
                    last_login_at=None  # TODO: Add last_login_at to User model
                )
            )

        return user_list_items, total_count

    @staticmethod
    def create_user(
        db: Session,
        user_data: CreateUserRequest,
        created_by_user_id: int
    ) -> CreateUserResponse:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            created_by_user_id: User ID of admin creating this user
        
        Returns:
            CreateUserResponse with created user details
        
        Raises:
            ConflictError: If email already exists or employee already linked
            NotFoundError: If linked employee not found
        """
        try:
            # Check if email already exists
            existing_user = db.query(User).filter(
                User.email == user_data.email
            ).first()
            
            if existing_user:
                raise ConflictError(
                    f"Email '{user_data.email}' is already registered"
                )

            # Validate linked employee if provided
            linked_employee = None
            if user_data.link_to_employee_id:
                linked_employee = db.query(Employee).filter(
                    Employee.employee_id == user_data.link_to_employee_id
                ).first()
                
                if not linked_employee:
                    raise NotFoundError(
                        f"Employee ID {user_data.link_to_employee_id} not found"
                    )
                
                # Check if employee is already linked to another user
                existing_link = db.query(UserEmployeeLink).filter(
                    UserEmployeeLink.employee_id == user_data.link_to_employee_id,
                    UserEmployeeLink.is_active == True
                ).first()
                
                if existing_link:
                    raise ConflictError(
                        f"Employee '{linked_employee.full_name}' is already "
                        f"linked to another user"
                    )

            # Create user
            new_user = User(
                full_name=user_data.full_name,
                email=user_data.email,
                password_hash=PasswordService.hash_password(user_data.password),
                is_active=(user_data.status == 'active')
            )
            db.add(new_user)
            db.flush()  # Get user_id without committing

            # Create employee link if provided
            if linked_employee:
                employee_link = UserEmployeeLink(
                    user_id=new_user.user_id,
                    employee_id=linked_employee.employee_id,
                    linked_at=datetime.now(timezone.utc),
                    is_active=True
                )
                db.add(employee_link)

            # Create audit log
            AuditService.create_audit_log(
                db=db,
                user_id=new_user.user_id,
                action='CREATE_USER',
                entity_type='USER',
                entity_id=new_user.user_id,
                performed_by_user_id=created_by_user_id,
                details={
                    'email': user_data.email,
                    'full_name': user_data.full_name,
                    'status': user_data.status,
                    'linked_employee_id': user_data.link_to_employee_id
                }
            )

            db.commit()
            db.refresh(new_user)

            logger.info(
                f"User created: {new_user.email} (ID: {new_user.user_id})"
            )

            return CreateUserResponse(
                user_id=new_user.user_id,
                full_name=new_user.full_name,
                email=new_user.email,
                status='active' if new_user.is_active else 'inactive',
                linked_employee_zid=linked_employee.zid if linked_employee else None,
                created_at=new_user.created_at,
                message="User created successfully"
            )
        
        except (ConflictError, NotFoundError, ValidationError):
            # Re-raise domain exceptions
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_user_detail(db: Session, user_id: int) -> UserDetailResponse:
        """
        Get detailed user information including all role assignments.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            UserDetailResponse with full user details
        
        Raises:
            NotFoundError: If user not found
        """
        # Load user with relationships
        user = db.query(User).options(
            joinedload(User.employee_link).joinedload(UserEmployeeLink.employee),
            joinedload(User.scope_roles).joinedload(AuthUserScopeRole.role),
            joinedload(User.scope_roles).joinedload(AuthUserScopeRole.scope_type)
        ).filter(User.user_id == user_id).first()

        if not user:
            raise NotFoundError(f"User ID {user_id} not found")

        # Build role assignments list
        role_assignments = []
        for assignment in user.scope_roles:
            # Get scope name
            scope_name = ScopeResolver.get_scope_entity_name(
                db, assignment.scope_type_id, assignment.scope_id
            )

            # Get granted_by user info
            granted_by_user = db.query(User).filter(
                User.user_id == assignment.granted_by
            ).first()
            granted_by_name = (
                granted_by_user.full_name if granted_by_user else "Unknown"
            )

            role_assignments.append(
                RoleAssignmentDetail(
                    assignment_id=assignment.user_scope_role_id,
                    role_id=assignment.role_id,
                    role_name=assignment.role.role_name,
                    scope_type_id=assignment.scope_type_id,
                    scope_type=assignment.scope_type.scope_type_code,
                    scope_id=assignment.scope_id,
                    scope_name=scope_name,
                    granted_by_user_id=assignment.granted_by,
                    granted_by_name=granted_by_name,
                    granted_at=assignment.granted_at,
                    is_active=assignment.is_active,
                    revoked_at=assignment.revoked_at
                )
            )

        # Get linked employee info
        linked_employee_zid = None
        linked_employee_name = None
        if user.employee_link and user.employee_link.employee:
            linked_employee_zid = user.employee_link.employee.zid
            linked_employee_name = user.employee_link.employee.full_name

        return UserDetailResponse(
            user_id=user.user_id,
            full_name=user.full_name,
            email=user.email,
            status='active' if user.is_active else 'inactive',
            linked_employee_zid=linked_employee_zid,
            linked_employee_name=linked_employee_name,
            role_assignments=role_assignments,
            created_at=user.created_at,
            last_login_at=None  # TODO: Add last_login_at to User model
        )

    @staticmethod
    def get_user_assignments(db: Session, user_id: int) -> List[UserAssignmentDetail]:
        """
        Get list of user assignments for Manage Access modal.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            List of UserAssignmentDetail with resolved scope labels
        
        Raises:
            NotFoundError: If user not found
        """
        # Verify user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundError(f"User ID {user_id} not found")

        # Load assignments with relationships
        assignments = db.query(AuthUserScopeRole).options(
            joinedload(AuthUserScopeRole.role),
            joinedload(AuthUserScopeRole.scope_type)
        ).filter(AuthUserScopeRole.user_id == user_id).all()

        # Transform to response schema
        assignment_list = []
        for assignment in assignments:
            # Resolve scope label
            scope_label = ScopeResolver.get_scope_entity_name(
                db, assignment.scope_type_id, assignment.scope_id
            )

            assignment_list.append(
                UserAssignmentDetail(
                    assignment_id=assignment.user_scope_role_id,
                    role_code=assignment.role.role_code,
                    role_name=assignment.role.role_name,
                    scope_type_code=assignment.scope_type.scope_type_code,
                    scope_id=assignment.scope_id,
                    scope_label=scope_label,
                    granted_at=assignment.granted_at,
                    revoked_at=assignment.revoked_at,
                    is_active=assignment.is_active
                )
            )

        return assignment_list
