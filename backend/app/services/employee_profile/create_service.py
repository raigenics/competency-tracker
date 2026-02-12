"""
Service for creating and updating employee basic details.

SRP: This service ONLY handles employee creation/update operations.
Does NOT handle skills - that's handled by competency services.
"""
import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.employee import Employee
from app.models.team import Team
from app.models.role import Role
from app.services.imports.employee_import.allocation_writer import upsert_active_project_allocation

logger = logging.getLogger(__name__)


def get_or_create_role(db: Session, role_name: Optional[str], created_by: str = "auto_create") -> Optional[int]:
    """
    Get role_id from role name, creating if necessary.
    
    Args:
        db: Database session
        role_name: Name of the role (can be None)
        created_by: Identifier for who/what created the role (default: 'auto_create')
        
    Returns:
        role_id or None if role_name is empty
    """
    if not role_name or not role_name.strip():
        return None
    
    role_name = role_name.strip()
    role = db.query(Role).filter(Role.role_name == role_name).first()
    
    if not role:
        role = Role(role_name=role_name, created_by=created_by)
        db.add(role)
        db.flush()  # Get the role_id
        logger.info(f"Created new role: {role_name}")
    
    return role.role_id


def validate_role_id(db: Session, role_id: int) -> Role:
    """
    Validate that role_id exists in roles table.
    
    Args:
        db: Database session
        role_id: ID to validate
        
    Returns:
        Role object if valid
        
    Raises:
        HTTPException(422): If role_id is invalid
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role_id: {role_id}. Role does not exist."
        )
    return role


def create_employee(
    db: Session,
    zid: str,
    full_name: str,
    team_id: int,
    role_id: int,
    email: str,
    start_date_of_working: Optional[date] = None,
    allocation_pct: Optional[int] = None
) -> Employee:
    """
    Create a new employee record.
    
    Args:
        db: Database session
        zid: Employee ZID (business identifier) - must be unique
        full_name: Employee's full name
        team_id: ID of the team the employee belongs to
        role_id: Role ID from roles table (required)
        email: Employee's email address (required)
        start_date_of_working: Employment start date (optional)
        allocation_pct: Project allocation percentage 0-100 (optional)
        
    Returns:
        Created Employee object
        
    Raises:
        HTTPException(404): If team_id is invalid
        HTTPException(409): If ZID already exists
        HTTPException(422): If role_id is invalid
    """
    # Validate team exists
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} not found"
        )
    
    # Validate role exists
    validate_role_id(db, role_id)
    
    # Check for duplicate ZID
    existing = db.query(Employee).filter(
        Employee.zid == zid,
        Employee.deleted_at.is_(None)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with ZID '{zid}' already exists"
        )
    
    # Create employee
    employee = Employee(
        zid=zid.strip(),
        full_name=full_name.strip(),
        team_id=team_id,
        email=email.strip() if email else None,
        role_id=role_id,
        start_date_of_working=start_date_of_working
    )
    
    try:
        db.add(employee)
        db.commit()
        db.refresh(employee)
        logger.info(f"Created employee: {zid} - {full_name}")
        
        # Post-create: Save allocation_pct to employee_project_allocations
        if allocation_pct is not None:
            project_id = employee.project_id
            if project_id:
                upsert_active_project_allocation(
                    db=db,
                    employee_id=employee.employee_id,
                    project_id=project_id,
                    allocation_pct=allocation_pct
                )
                db.commit()
                logger.info(f"Created allocation for employee {zid}: {allocation_pct}% on project {project_id}")
            else:
                logger.warning(f"Cannot create allocation for employee {zid}: no project assigned via team")
        
        return employee
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating employee {zid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with ZID '{zid}' already exists"
        )


def update_employee(
    db: Session,
    employee_id: int,
    full_name: Optional[str] = None,
    team_id: Optional[int] = None,
    email: Optional[str] = None,
    role_id: Optional[int] = None,
    start_date_of_working: Optional[date] = None,
    allocation_pct: Optional[int] = None
) -> Employee:
    """
    Update an existing employee record.
    
    Args:
        db: Database session
        employee_id: ID of employee to update
        full_name: New full name (optional)
        team_id: New team ID (optional)
        email: New email (optional)
        role_id: New role ID (optional)
        start_date_of_working: New start date (optional)
        allocation_pct: Project allocation percentage 0-100 (optional)
        
    Returns:
        Updated Employee object
        
    Raises:
        HTTPException(404): If employee_id or team_id is invalid
        HTTPException(422): If role_id is invalid
    """
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id,
        Employee.deleted_at.is_(None)
    ).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    # Update team if provided
    if team_id is not None:
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with ID {team_id} not found"
            )
        employee.team_id = team_id
    
    # Update other fields if provided
    if full_name is not None:
        employee.full_name = full_name.strip()
    
    if email is not None:
        employee.email = email.strip() if email else None
    
    if role_id is not None:
        validate_role_id(db, role_id)
        employee.role_id = role_id
    
    if start_date_of_working is not None:
        employee.start_date_of_working = start_date_of_working

    logger.info(
        "update_employee called | employee_id=%s | allocation_pct=%s",
        employee_id,
        allocation_pct
    )
    
    # Update project allocation if provided
    if allocation_pct is not None:
        # Get the project_id from the employee's team (refresh to get latest team)
        db.flush()  # Ensure team_id is updated before accessing project
        project_id = employee.project_id
        if project_id:
            upsert_active_project_allocation(
                db=db,
                employee_id=employee_id,
                project_id=project_id,
                allocation_pct=allocation_pct
            )
            logger.info(f"Updated allocation for employee {employee.zid}: {allocation_pct}% on project {project_id}")
        else:
            logger.warning(f"Cannot update allocation for employee {employee.zid}: no project assigned")
    
    db.commit()
    db.refresh(employee)
    logger.info(f"Updated employee: {employee.zid}")
    return employee
