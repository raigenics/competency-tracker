"""
Custom exceptions for RBAC Admin operations.

These exceptions map to specific HTTP status codes in the router layer:
- ValidationError -> 400 Bad Request
- NotFoundError -> 404 Not Found
- ConflictError -> 409 Conflict
"""


class RbacAdminError(Exception):
    """Base exception for RBAC Admin operations."""
    pass


class ValidationError(RbacAdminError):
    """Raised when input validation fails (maps to HTTP 400)."""
    pass


class NotFoundError(RbacAdminError):
    """Raised when a requested resource is not found (maps to HTTP 404)."""
    pass


class ConflictError(RbacAdminError):
    """Raised when a resource conflict occurs, e.g., duplicate email (maps to HTTP 409)."""
    pass
