"""
Dashboard Section: Data Freshness KPI

PURPOSE:
Calculates the percentage of employees in scope who have at least one skill update
within a configurable time window (default: 90 days).

PUBLIC ENTRYPOINT:
- get_data_freshness(db, days, sub_segment_id, project_id, team_id) -> DataFreshnessResponse

OUTPUT CONTRACT:
{
    "window_days": 90,
    "employees_in_scope": <int>,
    "employees_with_update": <int>,
    "freshness_percent": <float>  # 0-100, rounded to 1 decimal
}

BUSINESS LOGIC:
- employees_in_scope: Count of active employees matching filters
- employees_with_update: Distinct employees with >= 1 skill update in last N days
- freshness_percent = (employees_with_update / employees_in_scope) * 100
- If employees_in_scope = 0, freshness_percent = 0.0

FILTER APPLICATION:
- Uses same filter logic as Skill Update Activity
- Hierarchical: Team > Project > Sub-Segment > Organization
- Filters applied via apply_org_filters_to_employee_ids helper

ISOLATION:
- This file is self-contained
- Reuses query helpers but does NOT import from other dashboard sections
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Employee, EmployeeSkill
from app.services.utils.org_query_helpers import apply_org_filters_to_employee_ids


class InvalidDaysParameterError(ValueError):
    """Raised when days parameter is out of valid range."""
    pass


def get_data_freshness(
    db: Session,
    days: int = 90,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate data freshness percentage for employees in scope.
    
    Data freshness = % of employees with at least one skill update in last N days.
    
    Args:
        db: Database session
        days: Time window in days (1-365, default 90)
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        Dict with:
        - window_days: Time window used
        - employees_in_scope: Total employees matching filters
        - employees_with_update: Employees with >= 1 update in window
        - freshness_percent: Percentage (0-100, 1 decimal)
    
    Raises:
        InvalidDaysParameterError: If days is not between 1 and 365
    """
    # Validate input
    _validate_days_parameter(days)
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get employee IDs in scope (same filter logic as Skill Update Activity)
    employee_ids = _get_employee_ids_in_scope(
        db, sub_segment_id, project_id, team_id
    )
    
    employees_in_scope = len(employee_ids)
    
    # Handle empty scope
    if employees_in_scope == 0:
        return _build_response(days, 0, 0, 0.0)
    
    # Count distinct employees with at least 1 update in window
    employees_with_update = _count_employees_with_updates(
        db, employee_ids, cutoff_date
    )
    
    # Calculate freshness percentage
    freshness_percent = round((employees_with_update / employees_in_scope) * 100, 1)
    
    return _build_response(days, employees_in_scope, employees_with_update, freshness_percent)


def _validate_days_parameter(days: int) -> None:
    """
    Validate that days parameter is within acceptable range.
    
    Args:
        days: Number of days for analysis
    
    Raises:
        InvalidDaysParameterError: If days is not between 1 and 365
    """
    if days <= 0 or days > 365:
        raise InvalidDaysParameterError("Days must be between 1 and 365")


def _get_employee_ids_in_scope(
    db: Session,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> List[int]:
    """
    Get list of employee IDs matching scope filters.
    
    Uses same centralized filter logic as Skill Update Activity.
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        List of employee IDs
    """
    query = db.query(Employee.employee_id)
    query = apply_org_filters_to_employee_ids(query, sub_segment_id, project_id, team_id)
    
    employee_ids = [e[0] for e in query.all()]
    
    return employee_ids


def _count_employees_with_updates(
    db: Session,
    employee_ids: List[int],
    cutoff_date: datetime
) -> int:
    """
    Count distinct employees with at least one skill update since cutoff.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs in scope
        cutoff_date: Only count updates after this date
    
    Returns:
        Count of distinct employees with >= 1 update
    """
    count = db.query(
        func.count(func.distinct(EmployeeSkill.employee_id))
    ).filter(
        EmployeeSkill.employee_id.in_(employee_ids),
        EmployeeSkill.last_updated >= cutoff_date
    ).scalar()
    
    return count or 0


def _build_response(
    window_days: int,
    employees_in_scope: int,
    employees_with_update: int,
    freshness_percent: float
) -> Dict[str, Any]:
    """
    Build standardized response dict.
    
    Args:
        window_days: Time window used
        employees_in_scope: Total employees in scope
        employees_with_update: Employees with updates
        freshness_percent: Calculated percentage
    
    Returns:
        Response dict matching API contract
    """
    return {
        "window_days": window_days,
        "employees_in_scope": employees_in_scope,
        "employees_with_update": employees_with_update,
        "freshness_percent": freshness_percent
    }
