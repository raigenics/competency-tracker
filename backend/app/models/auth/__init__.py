"""
Authentication and Authorization Models

RBAC (Role-Based Access Control) Schema - Phase 0: Database Structure Only

This module contains models for the RBAC system. These tables support:
- User authentication identities
- Role-based authorization
- Scoped permissions (global to employee-level)
- Audit logging

NO LOGIC IMPLEMENTED YET - Schema foundation only.
"""
from app.models.auth.user import User
from app.models.auth.user_employee_link import UserEmployeeLink
from app.models.auth.auth_role import AuthRole
from app.models.auth.auth_permission import AuthPermission
from app.models.auth.auth_role_permission import AuthRolePermission
from app.models.auth.auth_scope_type import AuthScopeType
from app.models.auth.auth_user_scope_role import AuthUserScopeRole
from app.models.auth.auth_audit_log import AuthAuditLog

__all__ = [
    "User",
    "UserEmployeeLink",
    "AuthRole",
    "AuthPermission",
    "AuthRolePermission",
    "AuthScopeType",
    "AuthUserScopeRole",
    "AuthAuditLog",
]
