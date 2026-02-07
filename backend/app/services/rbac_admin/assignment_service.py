"""
Role assignment service for RBAC Admin.

Handles role assignment operations: create, revoke, and list assignments.
"""
import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.auth.user import User
from app.models.auth.auth_role import AuthRole
from app.models.auth.auth_scope_type import AuthScopeType
from app.models.auth.auth_user_scope_role import AuthUserScopeRole
from app.schemas.rbac_admin import (
    CreateRoleAssignmentRequest,
    RoleAssignmentDetail,
)
from app.services.rbac_admin.errors import NotFoundError, ConflictError, ValidationError
from app.services.rbac_admin.audit_service import AuditService
from app.services.rbac_admin.scope_resolver import ScopeResolver

logger = logging.getLogger(__name__)


class AssignmentService:
    """Service for role assignment operations."""

    @staticmethod
    def create_role_assignment(
        db: Session,
        assignment_data: CreateRoleAssignmentRequest,
        granted_by_user_id: int
    ) -> RoleAssignmentDetail:
        """
        Create a new role assignment for a user.
        
        Args:
            db: Database session
            assignment_data: Role assignment data
            granted_by_user_id: User ID of admin granting this role
        
        Returns:
            RoleAssignmentDetail with created assignment
        
        Raises:
            NotFoundError: If user, role, scope type, or scope entity not found
            ConflictError: If duplicate active assignment exists
            ValidationError: If scope_id validation fails
        """
        try:
            # Validate user exists
            user = db.query(User).filter(
                User.user_id == assignment_data.user_id
            ).first()
            
            if not user:
                raise NotFoundError(f"User ID {assignment_data.user_id} not found")

            # Validate role exists
            role = db.query(AuthRole).filter(
                AuthRole.role_id == assignment_data.role_id
            ).first()
            
            if not role:
                raise NotFoundError(f"Role ID {assignment_data.role_id} not found")

            # Validate scope type exists
            scope_type = db.query(AuthScopeType).filter(
                AuthScopeType.scope_type_id == assignment_data.scope_type_id
            ).first()
            
            if not scope_type:
                raise NotFoundError(
                    f"Scope type ID {assignment_data.scope_type_id} not found"
                )

            # Validate scope entity exists if scope_id provided
            scope_name = None
            if assignment_data.scope_id:
                scope_name = ScopeResolver.get_scope_entity_name(
                    db, assignment_data.scope_type_id, assignment_data.scope_id
                )
                if not scope_name:
                    raise NotFoundError(
                        f"Scope entity ID {assignment_data.scope_id} not found "
                        f"for scope type '{scope_type.scope_type_code}'"
                    )
            else:
                # GLOBAL scope
                scope_name = "All Systems"

            # Check for duplicate active assignment
            existing = db.query(AuthUserScopeRole).filter(
                and_(
                    AuthUserScopeRole.user_id == assignment_data.user_id,
                    AuthUserScopeRole.role_id == assignment_data.role_id,
                    AuthUserScopeRole.scope_type_id == assignment_data.scope_type_id,
                    AuthUserScopeRole.scope_id == assignment_data.scope_id,
                    AuthUserScopeRole.is_active == True
                )
            ).first()

            if existing:
                raise ConflictError(
                    f"User already has active {role.role_name} role for this scope"
                )

            # Create new assignment
            new_assignment = AuthUserScopeRole(
                user_id=assignment_data.user_id,
                role_id=assignment_data.role_id,
                scope_type_id=assignment_data.scope_type_id,
                scope_id=assignment_data.scope_id,
                granted_by=granted_by_user_id,
                granted_at=datetime.now(timezone.utc),
                is_active=True,
                revoked_at=None
            )
            db.add(new_assignment)
            db.flush()

            # Create audit log
            AuditService.create_audit_log(
                db=db,
                user_id=assignment_data.user_id,
                action='ASSIGN_ROLE',
                entity_type='ROLE_ASSIGNMENT',
                entity_id=new_assignment.user_scope_role_id,
                performed_by_user_id=granted_by_user_id,
                details={
                    'role_name': role.role_name,
                    'scope_type': scope_type.scope_type_code,
                    'scope_name': scope_name
                }
            )

            db.commit()
            db.refresh(new_assignment)

            logger.info(
                f"Role assigned: {role.role_name} to user {assignment_data.user_id} "
                f"for scope {scope_type.scope_type_code}:{scope_name}"
            )

            # Get granted_by user info
            granted_by_user = db.query(User).filter(
                User.user_id == granted_by_user_id
            ).first()
            granted_by_name = (
                granted_by_user.full_name if granted_by_user else "Unknown"
            )

            return RoleAssignmentDetail(
                assignment_id=new_assignment.user_scope_role_id,
                role_id=new_assignment.role_id,
                role_name=role.role_name,
                scope_type_id=new_assignment.scope_type_id,
                scope_type=scope_type.scope_type_code,
                scope_id=new_assignment.scope_id,
                scope_name=scope_name,
                granted_by_user_id=granted_by_user_id,
                granted_by_name=granted_by_name,
                granted_at=new_assignment.granted_at,
                is_active=True,
                revoked_at=None
            )
        
        except (NotFoundError, ConflictError, ValidationError):
            # Re-raise domain exceptions
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating role assignment: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def revoke_role_assignment(
        db: Session,
        assignment_id: int,
        revoked_by_user_id: int,
        reason: Optional[str] = None
    ) -> None:
        """
        Revoke (soft delete) a role assignment.
        
        Args:
            db: Database session
            assignment_id: Assignment ID to revoke
            revoked_by_user_id: User ID of admin revoking this assignment
            reason: Optional reason for revocation
        
        Raises:
            NotFoundError: If assignment not found
            ConflictError: If assignment already revoked
        """
        try:
            assignment = db.query(AuthUserScopeRole).filter(
                AuthUserScopeRole.user_scope_role_id == assignment_id
            ).first()

            if not assignment:
                raise NotFoundError(f"Assignment ID {assignment_id} not found")

            if not assignment.is_active:
                raise ConflictError(
                    f"Assignment ID {assignment_id} is already revoked"
                )

            # Soft delete
            assignment.is_active = False
            assignment.revoked_at = datetime.now(timezone.utc)

            # Create audit log
            AuditService.create_audit_log(
                db=db,
                user_id=assignment.user_id,
                action='REVOKE_ROLE',
                entity_type='ROLE_ASSIGNMENT',
                entity_id=assignment_id,
                performed_by_user_id=revoked_by_user_id,
                details={
                    'reason': reason,
                    'revoked_at': assignment.revoked_at.isoformat()
                }
            )

            db.commit()

            logger.info(
                f"Role assignment {assignment_id} revoked by user "
                f"{revoked_by_user_id}"
            )
        
        except (NotFoundError, ConflictError):
            # Re-raise domain exceptions
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                f"Error revoking role assignment: {str(e)}",
                exc_info=True
            )
            raise
