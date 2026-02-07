"""
Lookup service for RBAC dropdown data.

Provides roles, scope types, scope values, and employee lookups.
"""
import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.auth.auth_role import AuthRole
from app.models.auth.auth_scope_type import AuthScopeType
from app.models.employee import Employee
from app.models.segment import Segment
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team
from app.schemas.rbac_admin import (
    RoleLookupResponse,
    ScopeTypeLookupResponse,
    ScopeValueLookupResponse,
)
from app.services.rbac_admin.errors import ValidationError

logger = logging.getLogger(__name__)


class LookupService:
    """Service for RBAC lookup operations."""

    # Mapping of scope type names to database models and field names
    SCOPE_VALUE_MAPPING = {
        'SEGMENT': (Segment, 'segment_id', 'segment_name'),
        'SUB_SEGMENT': (SubSegment, 'sub_segment_id', 'sub_segment_name'),
        'PROJECT': (Project, 'project_id', 'project_name'),
        'TEAM': (Team, 'team_id', 'team_name'),
        'EMPLOYEE': (Employee, 'employee_id', 'full_name'),
    }

    @staticmethod
    def get_all_roles(db: Session) -> List[RoleLookupResponse]:
        """
        Get all available roles for dropdown selection.
        
        Args:
            db: Database session
        
        Returns:
            List of role lookup responses
        """
        roles = db.query(AuthRole).order_by(AuthRole.role_name).all()
        return [
            RoleLookupResponse(
                role_id=role.role_id,
                role_code=role.role_code,
                role_name=role.role_name,
                description=role.description
            )
            for role in roles
        ]

    @staticmethod
    def get_all_scope_types(db: Session) -> List[ScopeTypeLookupResponse]:
        """
        Get all scope types for dropdown selection.
        
        Args:
            db: Database session
        
        Returns:
            List of scope type lookup responses
        """
        scope_types = db.query(AuthScopeType).order_by(
            AuthScopeType.scope_type_code
        ).all()
        
        return [
            ScopeTypeLookupResponse(
                scope_type_id=st.scope_type_id,
                scope_type_code=st.scope_type_code,
                scope_name=st.scope_type_code,  # Display code as name for now
                description=st.description
            )
            for st in scope_types
        ]

    @staticmethod
    def get_scope_values(
        db: Session,
        scope_type_code: str
    ) -> List[ScopeValueLookupResponse]:
        """
        Get all values for a specific scope type.
        
        Args:
            db: Database session
            scope_type_code: Scope type code (e.g., 'GLOBAL', 'SEGMENT', 'SUB_SEGMENT', 'PROJECT', 'TEAM', 'EMPLOYEE')
        
        Returns:
            List of scope value lookups (empty list for GLOBAL only)
        
        Raises:
            ValidationError: If scope type is not supported
        """
        logger.info(f"GET SCOPE VALUES - Received scope_type_code: {scope_type_code}")
        
        # GLOBAL scope has no dropdown values (applies everywhere)
        if scope_type_code == 'GLOBAL':
            logger.info("GLOBAL scope - returning empty list (no values needed)")
            return []

        # Validate scope type is supported
        if scope_type_code not in LookupService.SCOPE_VALUE_MAPPING:
            logger.warning(f"Unsupported scope type requested: {scope_type_code}")
            raise ValidationError(f"Unsupported scope type: {scope_type_code}")

        # Query the appropriate table
        model, id_field, name_field = LookupService.SCOPE_VALUE_MAPPING[scope_type_code]
        
        logger.debug(f"Querying {model.__name__} table for scope values...")
        entities = db.query(model).order_by(getattr(model, name_field)).all()
        
        logger.info(f"Found {len(entities)} {scope_type_code} scope values")

        return [
            ScopeValueLookupResponse(
                scope_id=getattr(entity, id_field),
                scope_name=getattr(entity, name_field),
                scope_type=scope_type_code
            )
            for entity in entities
        ]

    @staticmethod
    def search_employees(db: Session, search: str = "") -> List[dict]:
        """
        Search for employees (for linking to users).
        
        Args:
            db: Database session
            search: Search term for employee name or ZID
        
        Returns:
            List of employee dictionaries with employee_id, employee_name, and zid
        """
        query = db.query(Employee)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.full_name.ilike(search_term),
                    Employee.zid.ilike(search_term)
                )
            )

        employees = query.order_by(Employee.full_name).limit(100).all()

        return [
            {
                'employee_id': emp.employee_id,
                'employee_name': emp.full_name,
                'zid': emp.zid
            }
            for emp in employees
        ]
