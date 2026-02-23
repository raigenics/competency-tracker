"""
Service for mapping missing roles from Employee Bulk Import.

Provides:
- GET endpoint: List all active roles for mapping UI
- POST endpoint: Map failed row to existing role (update import job result)
"""
import logging
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.role import Role
from app.models.import_job import ImportJob
from app.utils.normalization import normalize_designation


logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class RoleForMapping(BaseModel):
    """A role available for mapping."""
    role_id: int
    role_name: str
    role_alias: Optional[str] = None
    role_description: Optional[str] = None


class RolesForMappingResponse(BaseModel):
    """Response for GET roles for mapping endpoint."""
    total_count: int
    roles: List[RoleForMapping]


class MapRoleRequest(BaseModel):
    """Request body for POST map role endpoint."""
    failed_row_index: int = Field(description="Index of the failed row in failed_rows array")
    target_role_id: int = Field(description="ID of the master role to map to")


class MapRoleResponse(BaseModel):
    """Response for POST map role endpoint."""
    failed_row_index: int
    mapped_role_id: int
    mapped_role_name: str
    message: str
    alias_persisted: bool = False  # Whether a new alias was added to the role


# =============================================================================
# EXCEPTIONS
# =============================================================================

class RoleMappingError(Exception):
    """Base exception for role mapping operations."""
    pass


class ImportJobNotFoundError(RoleMappingError):
    """Import job not found."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Import job '{job_id}' not found")


class RoleNotFoundError(RoleMappingError):
    """Role not found."""
    def __init__(self, role_id: int):
        self.role_id = role_id
        super().__init__(f"Role with ID {role_id} not found or is deleted")


class InvalidFailedRowError(RoleMappingError):
    """Invalid failed row index."""
    def __init__(self, index: int, reason: str):
        self.index = index
        self.reason = reason
        super().__init__(f"Failed row at index {index}: {reason}")


class AlreadyMappedError(RoleMappingError):
    """Row is already mapped."""
    def __init__(self, index: int):
        self.index = index
        super().__init__(f"Failed row at index {index} is already mapped")


class NotRoleErrorError(RoleMappingError):
    """Row is not a MISSING_ROLE error."""
    def __init__(self, index: int, error_code: str):
        self.index = index
        self.error_code = error_code
        super().__init__(f"Failed row at index {index} has error code '{error_code}', not MISSING_ROLE")


class AliasConflictError(RoleMappingError):
    """Alias already mapped to a different role."""
    def __init__(self, alias_text: str, existing_role_name: str):
        self.alias_text = alias_text
        self.existing_role_name = existing_role_name
        super().__init__(
            f"Alias '{alias_text}' is already mapped to role '{existing_role_name}'. "
            "Contact admin to resolve this conflict."
        )


class MissingAliasTextError(RoleMappingError):
    """Failed row does not contain role_name for alias mapping."""
    def __init__(self, index: int):
        self.index = index
        super().__init__(f"Failed row at index {index} does not contain role_name for alias mapping")


# =============================================================================
# SERVICE FUNCTIONS
# =============================================================================

def find_role_by_alias(db: Session, alias_text: str) -> Optional[Role]:
    """
    Find a role that contains the given alias text in its role_alias column.
    
    Uses normalize_designation() for matching to handle whitespace/case variations.
    
    Args:
        db: Database session
        alias_text: The alias text to search for
        
    Returns:
        Role if found, None otherwise
    """
    normalized_alias = normalize_designation(alias_text)
    if not normalized_alias:
        return None
    
    # Get all active roles with aliases
    roles_with_aliases = db.query(Role).filter(
        Role.deleted_at.is_(None),
        Role.role_alias.isnot(None),
        Role.role_alias != ''
    ).all()
    
    for role in roles_with_aliases:
        # Check each comma-separated alias token
        for token in role.role_alias.split(','):
            if normalize_designation(token) == normalized_alias:
                return role
    
    # Also check if it matches a role_name directly
    roles = db.query(Role).filter(Role.deleted_at.is_(None)).all()
    for role in roles:
        if normalize_designation(role.role_name) == normalized_alias:
            return role
    
    return None


def add_alias_to_role(db: Session, role: Role, alias_text: str) -> bool:
    """
    Add an alias to a role's role_alias column.
    
    Args:
        db: Database session
        role: Role to add alias to
        alias_text: The alias text to add (will be trimmed)
        
    Returns:
        True if alias was added, False if it already exists on this role
    """
    alias_text = alias_text.strip()
    if not alias_text:
        return False
    
    normalized_new_alias = normalize_designation(alias_text)
    
    # Check if alias already exists on this role
    if role.role_alias:
        existing_aliases = [token.strip() for token in role.role_alias.split(',')]
        for existing in existing_aliases:
            if normalize_designation(existing) == normalized_new_alias:
                # Alias already exists on this role (idempotent)
                return False
        # Append new alias
        role.role_alias = f"{role.role_alias},{alias_text}"
    else:
        # First alias for this role
        role.role_alias = alias_text
    
    return True


def get_roles_for_mapping(
    db: Session,
    search_query: Optional[str] = None
) -> RolesForMappingResponse:
    """
    Get all active roles for the mapping UI.
    
    Args:
        db: Database session
        search_query: Optional search string to filter roles (case-insensitive)
        
    Returns:
        RolesForMappingResponse with list of roles
    """
    query = db.query(Role).filter(Role.deleted_at.is_(None))
    
    # Apply search filter if provided
    if search_query:
        search_term = f"%{search_query.lower()}%"
        query = query.filter(
            (func.lower(Role.role_name).like(search_term)) |
            (func.lower(Role.role_alias).like(search_term))
        )
    
    # Order alphabetically
    query = query.order_by(Role.role_name)
    
    roles = query.all()
    
    return RolesForMappingResponse(
        total_count=len(roles),
        roles=[
            RoleForMapping(
                role_id=role.role_id,
                role_name=role.role_name,
                role_alias=role.role_alias,
                role_description=role.role_description
            )
            for role in roles
        ]
    )


def map_role_to_failed_row(
    db: Session,
    import_run_id: str,
    failed_row_index: int,
    target_role_id: int,
    mapped_by: Optional[str] = None
) -> MapRoleResponse:
    """
    Map a MISSING_ROLE failed row to an existing master role.
    
    This:
    1. Updates the ImportJob.result to mark the row as resolved.
    2. Persists the alias mapping to the Role.role_alias column so future
       imports will resolve the missing role text automatically.
    
    Args:
        db: Database session
        import_run_id: The import job UUID
        failed_row_index: Index of the failed row in failed_rows array
        target_role_id: ID of the master role to map to
        mapped_by: User who performed the mapping (optional)
        
    Returns:
        MapRoleResponse with mapping details
        
    Raises:
        ImportJobNotFoundError: If import job not found
        RoleNotFoundError: If target role not found or deleted
        InvalidFailedRowError: If failed row index is invalid
        AlreadyMappedError: If row is already mapped
        NotRoleErrorError: If row is not a MISSING_ROLE error
        AliasConflictError: If alias is already mapped to a different role
        MissingAliasTextError: If failed row doesn't contain role_name
    """
    logger.info(
        f"Role mapping request received: import_run_id={import_run_id}, "
        f"failed_row_index={failed_row_index}, target_role_id={target_role_id}"
    )
    
    # 1. Find the import job
    import_job = db.query(ImportJob).filter(
        ImportJob.job_id == import_run_id
    ).first()
    
    if not import_job:
        raise ImportJobNotFoundError(import_run_id)
    
    # 2. Validate target role exists and is not deleted
    role = db.query(Role).filter(
        Role.role_id == target_role_id,
        Role.deleted_at.is_(None)
    ).first()
    
    if not role:
        raise RoleNotFoundError(target_role_id)
    
    # 3. Get the result and validate failed row exists
    result = import_job.result
    if not result or 'failed_rows' not in result:
        raise InvalidFailedRowError(failed_row_index, "Import job has no failed rows")
    
    failed_rows = result.get('failed_rows', [])
    
    if failed_row_index < 0 or failed_row_index >= len(failed_rows):
        raise InvalidFailedRowError(
            failed_row_index, 
            f"Index out of range (0-{len(failed_rows) - 1})"
        )
    
    failed_row = failed_rows[failed_row_index]
    
    # 4. Validate it's a MISSING_ROLE error
    error_code = failed_row.get('error_code', '')
    if error_code != 'MISSING_ROLE':
        raise NotRoleErrorError(failed_row_index, error_code)
    
    # 5. Check if already mapped
    if failed_row.get('resolved') is True:
        raise AlreadyMappedError(failed_row_index)
    
    # 6. Get the alias text from the failed row (the missing role text)
    alias_text = failed_row.get('role_name', '').strip()
    if not alias_text:
        raise MissingAliasTextError(failed_row_index)
    
    logger.info(f"Mapping alias_text='{alias_text}' to role_id={target_role_id}")
    
    # 7. Check if this alias already exists on a different role
    existing_role = find_role_by_alias(db, alias_text)
    if existing_role:
        if existing_role.role_id != target_role_id:
            # Alias exists on different role - conflict!
            raise AliasConflictError(alias_text, existing_role.role_name)
        # Alias already exists on target role - idempotent, don't add again
        alias_persisted = False
        logger.info(
            f"Alias '{alias_text}' already exists on target role '{role.role_name}' "
            f"(ID: {target_role_id}) - idempotent success"
        )
    else:
        # 8. Persist the alias to the Role's role_alias column
        alias_persisted = add_alias_to_role(db, role, alias_text)
        if alias_persisted:
            logger.info(
                f"Alias '{alias_text}' persisted to role '{role.role_name}' "
                f"(ID: {target_role_id}). New role_alias: '{role.role_alias}'"
            )
    
    # 9. Update the failed row to mark as resolved
    failed_row['resolved'] = True
    failed_row['mapped_role_id'] = target_role_id
    failed_row['mapped_role_name'] = role.role_name
    failed_row['mapped_by'] = mapped_by
    
    # 10. Update the import job result (need to replace the entire JSON)
    # SQLAlchemy JSON column requires explicit assignment to detect changes
    import_job.result = {**result, 'failed_rows': failed_rows}
    
    # 11. Commit the changes (both alias and import job result)
    db.commit()
    
    logger.info(
        f"Mapped MISSING_ROLE row {failed_row_index} in job {import_run_id} "
        f"to role '{role.role_name}' (ID: {target_role_id}), alias_persisted={alias_persisted}"
    )
    
    return MapRoleResponse(
        failed_row_index=failed_row_index,
        mapped_role_id=target_role_id,
        mapped_role_name=role.role_name,
        message=f"Successfully mapped to role '{role.role_name}'",
        alias_persisted=alias_persisted
    )
