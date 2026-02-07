"""
RBAC Admin Services Module

Modular, SRP-compliant services for RBAC administration.

Main facade:
    - RbacAdminService: Main entry point (delegates to specialized services)

Specialized services:
    - UserService: User CRUD operations
    - AssignmentService: Role assignment operations
    - LookupService: Dropdown/lookup data
    - AuditService: Audit logging
    - PasswordService: Password hashing (placeholder)
    - ScopeResolver: Scope entity name resolution

Custom exceptions:
    - ValidationError: Invalid input (HTTP 400)
    - NotFoundError: Resource not found (HTTP 404)
    - ConflictError: Resource conflict (HTTP 409)
"""
from app.services.rbac_admin.rbac_admin_service import RbacAdminService
from app.services.rbac_admin.errors import (
    RbacAdminError,
    ValidationError,
    NotFoundError,
    ConflictError,
)

__all__ = [
    'RbacAdminService',
    'RbacAdminError',
    'ValidationError',
    'NotFoundError',
    'ConflictError',
]
