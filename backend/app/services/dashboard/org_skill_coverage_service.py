"""
Dashboard Section: Organizational Skill Coverage

PUBLIC ENTRYPOINT:
- get_org_skill_coverage(db) -> Dict[str, Any]

HELPERS:
- _query_sub_segment_aggregates() - DB query for sub-segment level aggregates
- _query_certified_count_for_sub_segment() - DB query for certification count per sub-segment
- _query_organization_certified_count() - DB query for org-wide certification count
- _build_sub_segment_data() - Pure function to build sub-segment data dict (unit testable)
- _calculate_certified_percentage() - Pure function to calculate percentage (unit testable)
- _aggregate_organization_totals() - Pure function to sum up org totals (unit testable)
- _build_final_response() - Pure function to build final response dict (unit testable)

OUTPUT CONTRACT (MUST NOT CHANGE):
- Returns dict with keys: 'sub_segments', 'organization_total', 'as_of'
- sub_segments: List of dicts with keys:
  - sub_segment_name, total_employees, frontend_dev, backend_dev, full_stack, cloud_eng, devops, certified_pct
- organization_total: Dict with same keys (except sub_segment_name)
- as_of: Date string in format 'YYYY-MM-DD'

CRITICAL - DO NOT CHANGE:
- Role name mappings: 'Manual Tester' -> frontend_dev, 'Tech Lead' -> backend_dev, 'Developer' -> full_stack, 'PM' -> cloud_eng/devops
- Certification logic: certification is not None and certification != ''
- Percentage rounding: round() without decimals
- The per-sub-segment certified count query (even if inefficient)

ISOLATION:
- This file is self-contained and does NOT import from other dashboard sections.
- Changes here must NOT affect other dashboard sections.
"""
from typing import Dict, Any, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.employee import Employee
from app.models.sub_segment import SubSegment
from app.models.role import Role
from app.models.employee_skill import EmployeeSkill


def get_org_skill_coverage(db: Session) -> Dict[str, Any]:
    """
    Get organization-wide skill coverage by sub-segment and role.
    
    This always returns organization-wide data and ignores any dashboard filters.
    
    Args:
        db: Database session
    
    Returns:
        Dict containing:
        - sub_segments: List of sub-segment data with employee counts by role
        - organization_total: Aggregated organization totals
        - as_of: Current date as string
    """
    # Query sub-segment aggregates
    sub_segment_results = _query_sub_segment_aggregates(db)
    
    # Process results
    sub_segments_data = []
    org_totals = {
        'total_employees': 0,
        'frontend_dev': 0,
        'backend_dev': 0,
        'full_stack': 0,
        'cloud_eng': 0,
        'devops': 0
    }
    
    for result in sub_segment_results:
        # Query certification count for this sub-segment
        certified_count = _query_certified_count_for_sub_segment(
            db, result.sub_segment_name
        )
        
        # Build sub-segment data dict
        sub_segment_data = _build_sub_segment_data(
            result, certified_count
        )
        
        sub_segments_data.append(sub_segment_data)
        
        # Aggregate to organization totals
        org_totals = _aggregate_organization_totals(org_totals, sub_segment_data)
    
    # Query organization-wide certification count
    org_certified_count = _query_organization_certified_count(db)
    
    # Build final response
    return _build_final_response(
        sub_segments_data, org_totals, org_certified_count
    )


def _query_sub_segment_aggregates(db: Session):
    """
    Query sub-segment level employee aggregates grouped by role.
    
    Returns query result with columns:
    - sub_segment_name
    - total_employees
    - frontend_dev (Manual Tester count)
    - backend_dev (Tech Lead count)
    - full_stack (Developer count)
    - cloud_eng (PM count)
    - devops (PM count)
    """
    sub_segment_query = db.query(
        SubSegment.sub_segment_name,
        func.count(func.distinct(Employee.employee_id)).label('total_employees'),
        func.sum(case((Role.role_name == 'Manual Tester', 1), else_=0)).label('frontend_dev'),
        func.sum(case((Role.role_name == 'Tech Lead', 1), else_=0)).label('backend_dev'),
        func.sum(case((Role.role_name == 'Developer', 1), else_=0)).label('full_stack'),
        func.sum(case((Role.role_name == 'PM', 1), else_=0)).label('cloud_eng'),
        func.sum(case((Role.role_name == 'PM', 1), else_=0)).label('devops')
    ).outerjoin(Employee, SubSegment.sub_segment_id == Employee.sub_segment_id
    ).outerjoin(Role, Employee.role_id == Role.role_id
    ).group_by(SubSegment.sub_segment_id, SubSegment.sub_segment_name
    ).order_by(SubSegment.sub_segment_name)
    
    return sub_segment_query.all()


def _query_certified_count_for_sub_segment(
    db: Session, sub_segment_name: str
) -> int:
    """
    Query count of distinct employees with certifications in a sub-segment.
    
    CRITICAL: This query structure must NOT be changed even if inefficient.
    It uses a subquery to look up sub_segment_id and filters for non-empty certifications.
    
    Args:
        db: Database session
        sub_segment_name: Name of the sub-segment
    
    Returns:
        Count of certified employees
    """
    certified_count = db.query(func.count(func.distinct(Employee.employee_id))).filter(
        Employee.sub_segment_id == db.query(SubSegment.sub_segment_id).filter(
            SubSegment.sub_segment_name == sub_segment_name
        ).scalar(),
        Employee.employee_id.in_(
            db.query(EmployeeSkill.employee_id).filter(
                EmployeeSkill.certification.isnot(None),
                EmployeeSkill.certification != ''
            ).distinct()
        )
    ).scalar()
    
    return certified_count or 0


def _query_organization_certified_count(db: Session) -> int:
    """
    Query count of distinct employees with certifications organization-wide.
    
    Args:
        db: Database session
    
    Returns:
        Count of certified employees across organization
    """
    org_certified_count = db.query(func.count(func.distinct(Employee.employee_id))).filter(
        Employee.employee_id.in_(
            db.query(EmployeeSkill.employee_id).filter(
                EmployeeSkill.certification.isnot(None),
                EmployeeSkill.certification != ''
            ).distinct()
        )
    ).scalar()
    
    return org_certified_count or 0


def _build_sub_segment_data(result, certified_count: int) -> Dict[str, Any]:
    """
    Build sub-segment data dictionary from query result.
    
    Pure function - unit testable without DB.
    
    Args:
        result: Query result row with employee counts
        certified_count: Count of certified employees
    
    Returns:
        Dict with sub-segment metrics
    """
    total_employees = int(result.total_employees or 0)
    
    certified_pct = _calculate_certified_percentage(
        certified_count, total_employees
    )
    
    frontend_dev = int(result.frontend_dev or 0)
    backend_dev = int(result.backend_dev or 0)
    full_stack = int(result.full_stack or 0)
    cloud_eng = int(result.cloud_eng or 0)
    devops = int(result.devops or 0)
    
    return {
        'sub_segment_name': result.sub_segment_name,
        'total_employees': total_employees,
        'frontend_dev': frontend_dev,
        'backend_dev': backend_dev,
        'full_stack': full_stack,
        'cloud_eng': cloud_eng,
        'devops': devops,
        'certified_pct': certified_pct
    }


def _calculate_certified_percentage(
    certified_count: int, total_employees: int
) -> int:
    """
    Calculate certification percentage.
    
    Pure function - unit testable.
    
    CRITICAL: Uses round() without decimals to match existing behavior.
    
    Args:
        certified_count: Number of certified employees
        total_employees: Total number of employees
    
    Returns:
        Percentage as integer (rounded)
    """
    if total_employees > 0:
        return round((certified_count / total_employees) * 100)
    else:
        return 0


def _aggregate_organization_totals(
    org_totals: Dict[str, int], sub_segment_data: Dict[str, Any]
) -> Dict[str, int]:
    """
    Aggregate sub-segment data into organization totals.
    
    Pure function - unit testable.
    
    Args:
        org_totals: Current organization totals dict
        sub_segment_data: Sub-segment data to add
    
    Returns:
        Updated organization totals dict
    """
    org_totals['total_employees'] += sub_segment_data['total_employees']
    org_totals['frontend_dev'] += sub_segment_data['frontend_dev']
    org_totals['backend_dev'] += sub_segment_data['backend_dev']
    org_totals['full_stack'] += sub_segment_data['full_stack']
    org_totals['cloud_eng'] += sub_segment_data['cloud_eng']
    org_totals['devops'] += sub_segment_data['devops']
    
    return org_totals


def _build_final_response(
    sub_segments_data: List[Dict[str, Any]],
    org_totals: Dict[str, int],
    org_certified_count: int
) -> Dict[str, Any]:
    """
    Build final response dictionary.
    
    Pure function - unit testable.
    
    Args:
        sub_segments_data: List of sub-segment data dicts
        org_totals: Organization totals dict
        org_certified_count: Organization-wide certification count
    
    Returns:
        Final response dict with required structure
    """
    org_certified_pct = _calculate_certified_percentage(
        org_certified_count, org_totals['total_employees']
    )
    
    organization_total = {
        'total_employees': org_totals['total_employees'],
        'frontend_dev': org_totals['frontend_dev'],
        'backend_dev': org_totals['backend_dev'],
        'full_stack': org_totals['full_stack'],
        'cloud_eng': org_totals['cloud_eng'],
        'devops': org_totals['devops'],
        'certified_pct': org_certified_pct
    }
    
    return {
        'sub_segments': sub_segments_data,
        'organization_total': organization_total,
        'as_of': date.today().strftime('%Y-%m-%d')
    }
