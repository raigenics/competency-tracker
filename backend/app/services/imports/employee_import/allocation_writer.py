"""
Employee Allocation Writer - Handles project allocation persistence during import.

Single Responsibility: Parse allocation data and upsert into employee_project_allocations table.
"""
import logging
import re
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.employee_project_allocation import EmployeeProjectAllocation

logger = logging.getLogger(__name__)


def parse_allocation_pct(raw_value) -> Optional[int]:
    """
    Parse allocation percentage from raw Excel value.
    
    Accepts:
    - Empty/None → None
    - Numeric values: 50, 50.0 → 50
    - String with %: "50%", " 50 % " → 50
    - String numeric: "50", " 50 " → 50
    
    Rejects (returns None and logs warning):
    - Negative values
    - Values > 100
    - Non-numeric strings
    
    Args:
        raw_value: Raw value from Excel cell
        
    Returns:
        Integer 0-100 or None if empty/invalid
    """
    import pandas as pd
    
    # Handle empty/null
    if raw_value is None:
        return None
    if pd.isna(raw_value):
        return None
    
    # Convert to string and strip whitespace
    str_value = str(raw_value).strip()
    if str_value == '' or str_value.lower() == 'nan':
        return None
    
    # Remove % sign if present
    str_value = str_value.replace('%', '').strip()
    
    # Try to parse as number
    try:
        float_value = float(str_value)
        int_value = int(round(float_value))
        
        # Validate range
        if int_value < 0:
            logger.warning(f"Invalid allocation percentage '{raw_value}': negative value not allowed")
            return None
        if int_value > 100:
            logger.warning(f"Invalid allocation percentage '{raw_value}': value exceeds 100")
            return None
        
        return int_value
        
    except (ValueError, TypeError):
        logger.warning(f"Invalid allocation percentage '{raw_value}': cannot parse as number")
        return None


def upsert_active_project_allocation(
    db: Session,
    employee_id: int,
    project_id: int,
    allocation_pct: int,
    start_date: Optional[date] = None,
    allocation_type: str = 'BILLABLE'
) -> Optional[int]:
    """
    Insert or update an active project allocation for an employee.
    
    Idempotency rules:
    - If active allocation (end_date IS NULL) exists for (employee_id, project_id):
      → Update allocation_pct and updated_at
    - If multiple active exist (bad data): update most recent, log warning
    - If none exist: insert new row
    
    Args:
        db: SQLAlchemy session
        employee_id: FK to employees.employee_id
        project_id: FK to projects.project_id
        allocation_pct: Percentage 0-100
        start_date: Start date (defaults to today if None)
        allocation_type: One of BILLABLE, INTERNAL, BENCH, SHADOW (default: BILLABLE)
        
    Returns:
        allocation_id of inserted/updated row, or None on error
    """
    if allocation_pct is None:
        return None  # Nothing to do
    
    if start_date is None:
        start_date = date.today()
    
    try:
        # Find active allocations for this employee+project (end_date IS NULL)
        active_allocations = db.query(EmployeeProjectAllocation).filter(
            and_(
                EmployeeProjectAllocation.employee_id == employee_id,
                EmployeeProjectAllocation.project_id == project_id,
                EmployeeProjectAllocation.end_date.is_(None)
            )
        ).order_by(EmployeeProjectAllocation.created_at.desc()).all()
        
        if len(active_allocations) > 1:
            logger.warning(
                f"Found {len(active_allocations)} active allocations for "
                f"employee_id={employee_id}, project_id={project_id}. "
                f"Updating most recent."
            )
        
        if active_allocations:
            # Update existing active allocation
            allocation = active_allocations[0]
            allocation.allocation_pct = allocation_pct
            allocation.allocation_type = allocation_type
            # updated_at handled by model's onupdate
            db.add(allocation)
            db.flush()
            logger.debug(
                f"Updated allocation {allocation.allocation_id}: "
                f"employee_id={employee_id}, project_id={project_id}, pct={allocation_pct}%"
            )
            return allocation.allocation_id
        else:
            # Insert new allocation
            allocation = EmployeeProjectAllocation(
                employee_id=employee_id,
                project_id=project_id,
                allocation_pct=allocation_pct,
                allocation_type=allocation_type,
                start_date=start_date,
                end_date=None  # Active allocation
            )
            db.add(allocation)
            db.flush()
            logger.debug(
                f"Created allocation {allocation.allocation_id}: "
                f"employee_id={employee_id}, project_id={project_id}, pct={allocation_pct}%"
            )
            return allocation.allocation_id
            
    except Exception as e:
        logger.error(f"Failed to upsert allocation for employee_id={employee_id}, project_id={project_id}: {e}")
        raise
