"""
Service for soft-deleting employees.

SRP: This service ONLY handles employee soft-delete operations.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.employee import Employee

logger = logging.getLogger(__name__)


def soft_delete_employee(db: Session, employee_id: int) -> Employee:
    """
    Soft-delete an employee by setting deleted_at timestamp.
    
    Args:
        db: Database session
        employee_id: ID of the employee to delete
        
    Returns:
        The soft-deleted Employee object
        
    Raises:
        HTTPException(404): If employee not found
        HTTPException(400): If employee is already deleted
    """
    # Find the employee
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    
    if not employee:
        logger.warning(f"Employee not found for deletion: {employee_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    # Check if already soft-deleted
    if employee.deleted_at is not None:
        logger.warning(f"Employee {employee_id} is already deleted")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with ID {employee_id} is already deleted"
        )
    
    # Perform soft delete
    employee.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(employee)
    
    logger.info(f"Soft-deleted employee: {employee_id} ({employee.full_name})")
    
    return employee
