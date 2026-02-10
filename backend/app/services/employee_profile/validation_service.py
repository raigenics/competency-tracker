"""
Employee Uniqueness Validation Service

SRP: Responsible solely for checking ZID and email uniqueness.
Does NOT handle employee creation/update - only validation queries.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.employee import Employee

logger = logging.getLogger(__name__)


def check_zid_exists(
    db: Session,
    zid: str,
    exclude_employee_id: Optional[int] = None
) -> bool:
    """
    Check if a ZID already exists in the database.
    
    Args:
        db: Database session
        zid: ZID to check
        exclude_employee_id: If provided, exclude this employee from the check
                            (useful for edit mode where own ZID shouldn't trigger error)
    
    Returns:
        True if ZID exists (and belongs to another employee), False otherwise
    """
    if not zid or not zid.strip():
        return False
    
    query = db.query(Employee).filter(
        and_(
            func.lower(Employee.zid) == func.lower(zid.strip()),
            Employee.deleted_at.is_(None)  # Only check active employees
        )
    )
    
    if exclude_employee_id is not None:
        query = query.filter(Employee.employee_id != exclude_employee_id)
    
    return query.first() is not None


def check_email_exists(
    db: Session,
    email: str,
    exclude_employee_id: Optional[int] = None
) -> bool:
    """
    Check if an email already exists in the database.
    
    Args:
        db: Database session
        email: Email to check
        exclude_employee_id: If provided, exclude this employee from the check
                            (useful for edit mode where own email shouldn't trigger error)
    
    Returns:
        True if email exists (and belongs to another employee), False otherwise
    """
    if not email or not email.strip():
        return False
    
    query = db.query(Employee).filter(
        and_(
            func.lower(Employee.email) == func.lower(email.strip()),
            Employee.deleted_at.is_(None)  # Only check active employees
        )
    )
    
    if exclude_employee_id is not None:
        query = query.filter(Employee.employee_id != exclude_employee_id)
    
    return query.first() is not None


def validate_unique(
    db: Session,
    zid: Optional[str] = None,
    email: Optional[str] = None,
    exclude_employee_id: Optional[int] = None
) -> dict:
    """
    Validate ZID and email uniqueness.
    
    Args:
        db: Database session
        zid: ZID to check (optional)
        email: Email to check (optional)
        exclude_employee_id: Employee ID to exclude from checks (for edit mode)
    
    Returns:
        dict with zid_exists and email_exists booleans
    """
    result = {
        "zid_exists": False,
        "email_exists": False
    }
    
    if zid:
        result["zid_exists"] = check_zid_exists(db, zid, exclude_employee_id)
        if result["zid_exists"]:
            logger.info(f"ZID '{zid}' already exists in database")
    
    if email:
        result["email_exists"] = check_email_exists(db, email, exclude_employee_id)
        if result["email_exists"]:
            logger.info(f"Email '{email}' already exists in database")
    
    return result
