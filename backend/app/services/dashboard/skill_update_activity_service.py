"""
Dashboard Section: Skill Update Activity (Detailed Metrics)

PUBLIC ENTRYPOINT:
- get_skill_update_activity(db, days, sub_segment_id, project_id, team_id) -> Dict[str, int]

HELPERS:
- _validate_days_parameter() - Validate days input
- _calculate_cutoff_dates() - Calculate datetime cutoffs
- _get_employee_ids_in_scope() - Query employees matching filters
- _query_updates_per_employee() - Count updates per employee
- _calculate_activity_metrics() - Calculate activity categories
- _query_stagnant_employees() - Find employees with no recent updates
- _build_response() - Format final response

OUTPUT CONTRACT:
- Returns dict with keys:
  - days: Input days parameter (echoed back)
  - engaged: DISTINCT employees with >= 2 updates in last N days (mutually exclusive)
  - active: DISTINCT employees with exactly 1 update in last N days (mutually exclusive)
  - inactive: DISTINCT employees with 0 updates in last N days (mutually exclusive)
  - stagnant_180_days: DISTINCT employees with no updates in last 180 days

BUSINESS LOGIC:
- All counts are of DISTINCT employees (not skills)
- Engaged threshold: >= 2 updates
- Active threshold: exactly 1 update
- Inactive: 0 updates in last N days
- Stagnant period: 180 days (fixed, not based on `days` parameter)
- engaged + active + inactive == total employees in scope

ISOLATION:
- This file is self-contained and does NOT import from other dashboard sections.
- Changes here must NOT affect other dashboard sections.
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Employee, EmployeeSkill
from app.services.utils.org_query_helpers import apply_org_filters_to_employee_ids


class InvalidDaysParameterError(ValueError):
    """Raised when days parameter is out of valid range."""
    pass


def get_skill_update_activity(
    db: Session,
    days: int,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None
) -> Dict[str, int]:
    """
    Get skill update activity metrics based on employee skill update timestamps.
    
    Analyzes employee learning activity by counting skill updates in different
    time periods and categorizing employees by activity level.
    
    Args:
        db: Database session
        days: Time window in days for activity analysis (1-365)
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        Dict with keys:
        - days: Input parameter echoed back
        - engaged: Count of distinct employees with >= 2 updates
        - active: Count of distinct employees with exactly 1 update
        - inactive: Count of distinct employees with 0 updates
        - stagnant_180_days: Count of distinct employees with no updates in 180 days
    
    Raises:
        InvalidDaysParameterError: If days is not between 1 and 365
    """
    # Validate input
    _validate_days_parameter(days)
    
    # Calculate cutoff dates
    cutoff_date, stagnant_cutoff = _calculate_cutoff_dates(days)
    
    # Get employee IDs in scope
    employee_ids = _get_employee_ids_in_scope(
        db, sub_segment_id, project_id, team_id
    )
    
    # Handle empty scope
    if not employee_ids:
        return {
            "days": days,
            "engaged": 0,
            "active": 0,
            "inactive": 0,
            "stagnant_180_days": 0
        }
    
    # Query updates per employee
    update_counts = _query_updates_per_employee(db, employee_ids, cutoff_date)
    
    # Calculate activity metrics
    engaged, active, inactive = _calculate_activity_metrics(
        employee_ids, update_counts
    )
    
    # Query stagnant employees
    stagnant_count = _query_stagnant_employees(
        db, employee_ids, stagnant_cutoff
    )
    
    # Build response
    return _build_response(
        days, engaged, active, inactive, stagnant_count
    )


def _validate_days_parameter(days: int) -> None:
    """
    Validate that days parameter is within acceptable range.
    
    Pure validation logic - unit testable.
    
    Args:
        days: Number of days for analysis
    
    Raises:
        InvalidDaysParameterError: If days is not between 1 and 365
    """
    if days <= 0 or days > 365:
        raise InvalidDaysParameterError("Days must be between 1 and 365")


def _calculate_cutoff_dates(days: int) -> Tuple[datetime, datetime]:
    """
    Calculate cutoff dates for activity analysis.
    
    Pure function - unit testable.
    
    Args:
        days: Number of days for activity window
    
    Returns:
        Tuple of (cutoff_date, stagnant_cutoff)
        - cutoff_date: N days ago from now
        - stagnant_cutoff: 180 days ago from now (fixed)
    """
    now = datetime.utcnow()
    cutoff_date = now - timedelta(days=days)
    stagnant_cutoff = now - timedelta(days=180)
    
    return cutoff_date, stagnant_cutoff


def _get_employee_ids_in_scope(
    db: Session,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> List[int]:
    """
    Get list of employee IDs matching scope filters.
    
    PHASE 1 NORMALIZATION:
    - Uses centralized join-based filtering logic
    - No longer filters directly on Employee.project_id or Employee.sub_segment_id
    - Canonical: team_id (direct FK) > project_id (Team join) > sub_segment_id (Team->Project joins)
    
    Applies hierarchical filtering: Team > Project > Sub-Segment > All.
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        List of employee IDs
    """
    # PHASE 1 NORMALIZATION: Use centralized helper for join-based filtering
    # OLD: Direct inline filters on Employee.sub_segment_id, Employee.project_id
    # NEW: Canonical helper enforces team_id as source of truth with joins
    query = db.query(Employee.employee_id)
    query = apply_org_filters_to_employee_ids(query, sub_segment_id, project_id, team_id)
    
    employee_ids = [e[0] for e in query.all()]
    
    return employee_ids


def _query_updates_per_employee(
    db: Session,
    employee_ids: List[int],
    cutoff_date: datetime
) -> Dict[int, int]:
    """
    Query count of skill updates per employee since cutoff date.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs in scope
        cutoff_date: Only count updates after this date
    
    Returns:
        Dict mapping employee_id -> update_count
    """
    updates_per_employee = db.query(
        EmployeeSkill.employee_id,
        func.count(EmployeeSkill.emp_skill_id).label('update_count')
    ).filter(
        EmployeeSkill.employee_id.in_(employee_ids),
        EmployeeSkill.last_updated >= cutoff_date
    ).group_by(EmployeeSkill.employee_id).all()
    
    update_counts_dict = {emp_id: count for emp_id, count in updates_per_employee}
    
    return update_counts_dict


def _calculate_activity_metrics(
    employee_ids: List[int],
    update_counts: Dict[int, int]
) -> Tuple[int, int, int]:
    """
    Calculate activity metrics from update counts.
    
    Pure function - unit testable.
    
    BUSINESS RULES (mutually exclusive buckets):
    - engaged: Employees with >= 2 updates (mutually exclusive)
    - active: Employees with exactly 1 update (mutually exclusive)
    - inactive: Employees with 0 updates in last N days
    
    Args:
        employee_ids: All employee IDs in scope
        update_counts: Dict of employee_id -> update_count
    
    Returns:
        Tuple of (engaged, active, inactive)
    """
    # Engaged: DISTINCT employees with >= 2 updates
    engaged = sum(1 for count in update_counts.values() if count >= 2)
    
    # Active: DISTINCT employees with exactly 1 update
    active = sum(1 for count in update_counts.values() if count == 1)
    
    # Inactive: employees with 0 updates in last N days
    inactive = len(employee_ids) - engaged - active
    
    return engaged, active, inactive


def _query_stagnant_employees(
    db: Session,
    employee_ids: List[int],
    stagnant_cutoff: datetime
) -> int:
    """
    Count employees with no updates since stagnant cutoff.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs in scope
        stagnant_cutoff: Date threshold (180 days ago)
    
    Returns:
        Count of stagnant employees
    """
    # Find employees WITH recent updates
    employees_with_recent_updates = db.query(
        func.distinct(EmployeeSkill.employee_id)
    ).filter(
        EmployeeSkill.employee_id.in_(employee_ids),
        EmployeeSkill.last_updated >= stagnant_cutoff
    ).all()
    
    employees_with_recent_updates_set = {e[0] for e in employees_with_recent_updates}
    
    # Stagnant = total employees - employees with recent updates
    stagnant_count = len(employee_ids) - len(employees_with_recent_updates_set)
    
    return stagnant_count


def _build_response(
    days: int,
    engaged: int,
    active: int,
    inactive: int,
    stagnant_count: int
) -> Dict[str, int]:
    """
    Build final response dictionary.
    
    Pure function - unit testable.
    
    Args:
        days: Input days parameter
        engaged: Count of employees with >= 2 updates
        active: Count of employees with exactly 1 update
        inactive: Count of employees with 0 updates
        stagnant_count: Count of employees with no updates in 180 days
    
    Returns:
        Response dict with required keys
    """
    return {
        "days": days,
        "engaged": engaged,
        "active": active,
        "inactive": inactive,
        "stagnant_180_days": stagnant_count
    }
