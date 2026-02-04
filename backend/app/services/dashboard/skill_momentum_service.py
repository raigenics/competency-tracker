"""
Dashboard Section: Skill Momentum (Update Tracking)

PUBLIC ENTRYPOINT:
- get_skill_momentum(db, sub_segment_id, project_id, team_id) -> Dict[str, int]

HELPERS:
- _get_employee_ids_in_scope() - Query employees matching filters
- _calculate_time_cutoffs() - Calculate datetime cutoffs
- _query_skills_updated_in_period() - Count skills updated in time range
- _build_response() - Format final response dict

OUTPUT CONTRACT (MUST NOT CHANGE):
- Returns dict with keys:
  - updated_last_3_months: Count of distinct skills updated in last 90 days
  - updated_last_6_months: Count of distinct skills updated 90-180 days ago
  - not_updated_6_months: Count of distinct skills not updated in 180+ days

BUSINESS LOGIC:
- Time periods: 3 months = 90 days, 6 months = 180 days
- Counts are of DISTINCT emp_skill_id (not employees)
- Only counts skills for employees in scope

ISOLATION:
- This file is self-contained and does NOT import from other dashboard sections.
- Changes here must NOT affect other dashboard sections.
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Employee, EmployeeSkill


def get_skill_momentum(
    db: Session,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None
) -> Dict[str, int]:
    """
    Get skill progress momentum - counts of skill updates in different time periods.
    
    Tracks skill update activity across three time buckets:
    - Last 3 months (0-90 days ago)
    - Last 6 months (90-180 days ago)
    - Not updated in 6+ months (180+ days ago)
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        Dict with keys:
        - updated_last_3_months: Skill count
        - updated_last_6_months: Skill count (between 3-6 months)
        - not_updated_6_months: Skill count
    """
    # Get employee IDs in scope
    employee_ids = _get_employee_ids_in_scope(
        db, sub_segment_id, project_id, team_id
    )
    
    # Handle empty scope
    if not employee_ids:
        return {
            "updated_last_3_months": 0,
            "updated_last_6_months": 0,
            "not_updated_6_months": 0
        }
    
    # Calculate time cutoffs
    three_months_ago, six_months_ago = _calculate_time_cutoffs()
    
    # Query skill counts for each time period
    updated_3m = _query_skills_updated_in_period(
        db, employee_ids, three_months_ago, None
    )
    
    updated_6m = _query_skills_updated_in_period(
        db, employee_ids, six_months_ago, three_months_ago
    )
    
    not_updated = _query_skills_updated_before(
        db, employee_ids, six_months_ago
    )
    
    # Build response
    return _build_response(updated_3m, updated_6m, not_updated)


def _get_employee_ids_in_scope(
    db: Session,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int]
) -> List[int]:
    """
    Get list of employee IDs matching scope filters.
    
    Applies hierarchical filtering: Team > Project > Sub-Segment > All.
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        List of employee IDs
    """
    employee_filter = db.query(Employee.employee_id)
    
    if team_id:
        employee_filter = employee_filter.filter(Employee.team_id == team_id)
    elif project_id:
        employee_filter = employee_filter.filter(Employee.project_id == project_id)
    elif sub_segment_id:
        employee_filter = employee_filter.filter(Employee.sub_segment_id == sub_segment_id)
    
    employee_ids = [e[0] for e in employee_filter.all()]
    
    return employee_ids


def _calculate_time_cutoffs():
    """
    Calculate datetime cutoffs for time periods.
    
    Pure function - unit testable.
    
    Returns:
        Tuple of (three_months_ago, six_months_ago) datetime objects
    """
    now = datetime.now()
    three_months_ago = now - timedelta(days=90)
    six_months_ago = now - timedelta(days=180)
    
    return three_months_ago, six_months_ago


def _query_skills_updated_in_period(
    db: Session,
    employee_ids: List[int],
    start_date: datetime,
    end_date: Optional[datetime]
) -> int:
    """
    Count distinct skills updated within a time period.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs in scope
        start_date: Start of time period (inclusive)
        end_date: End of time period (exclusive), None for no upper bound
    
    Returns:
        Count of distinct emp_skill_id
    """
    query = db.query(func.count(func.distinct(EmployeeSkill.emp_skill_id))).filter(
        EmployeeSkill.employee_id.in_(employee_ids),
        EmployeeSkill.last_updated >= start_date
    )
    
    if end_date is not None:
        query = query.filter(EmployeeSkill.last_updated < end_date)
    
    count = query.scalar() or 0
    
    return count


def _query_skills_updated_before(
    db: Session,
    employee_ids: List[int],
    cutoff_date: datetime
) -> int:
    """
    Count distinct skills NOT updated since cutoff date.
    
    Args:
        db: Database session
        employee_ids: List of employee IDs in scope
        cutoff_date: Cutoff datetime (skills updated before this)
    
    Returns:
        Count of distinct emp_skill_id
    """
    count = db.query(func.count(func.distinct(EmployeeSkill.emp_skill_id))).filter(
        EmployeeSkill.employee_id.in_(employee_ids),
        EmployeeSkill.last_updated < cutoff_date
    ).scalar() or 0
    
    return count


def _build_response(
    updated_3m: int,
    updated_6m: int,
    not_updated: int
) -> Dict[str, int]:
    """
    Build final response dictionary.
    
    Pure function - unit testable.
    
    Args:
        updated_3m: Count for last 3 months
        updated_6m: Count for 3-6 months ago
        not_updated: Count for 6+ months ago
    
    Returns:
        Response dict with required keys
    """
    return {
        "updated_last_3_months": updated_3m,
        "updated_last_6_months": updated_6m,
        "not_updated_6_months": not_updated
    }
