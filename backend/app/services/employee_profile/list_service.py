"""
List Service - GET /employees

Handles paginated employee listing with optional filters.
Zero dependencies on other services.
"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Employee, EmployeeSkill
from app.schemas.employee import EmployeeResponse, OrganizationInfo
from app.schemas.common import PaginationParams

logger = logging.getLogger(__name__)


def get_employees_paginated(
    db: Session,
    pagination: PaginationParams,
    sub_segment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    role_id: Optional[int] = None,
    search: Optional[str] = None
) -> Tuple[List[EmployeeResponse], int]:
    """
    Get paginated list of employees with optional filters.
    
    Args:
        db: Database session
        pagination: Pagination parameters (page, size, offset)
        sub_segment_id: Optional sub-segment ID filter
        project_id: Optional project ID filter
        team_id: Optional team ID filter
        role_id: Optional role ID filter
        search: Optional search by name or ZID
    
    Returns:
        Tuple of (employee_responses, total_count)
    """
    logger.info(f"Fetching employees: page={pagination.page}, size={pagination.size}, "
                f"sub_segment_id={sub_segment_id}, project_id={project_id}, "
                f"team_id={team_id}, role_id={role_id}, search={search}")
    
    # Build filtered query
    query = _build_employee_query(db, sub_segment_id, project_id, team_id, role_id, search)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and fetch
    employees = query.offset(pagination.offset).limit(pagination.size).all()
    
    # Build response with skills count
    response_items = _build_employee_responses(db, employees)
    
    logger.info(f"Returning {len(response_items)} employees (total: {total})")
    return response_items, total


# === DATABASE QUERIES ===

def _build_employee_query(
    db: Session,
    sub_segment_id: Optional[int],
    project_id: Optional[int],
    team_id: Optional[int],
    role_id: Optional[int],
    search: Optional[str]
):
    """
    Build filtered employee query with eager loading.
    Returns query object (not executed).
    """
    query = db.query(Employee).options(
        joinedload(Employee.sub_segment),
        joinedload(Employee.project),
        joinedload(Employee.team),
        joinedload(Employee.role)
    )
    
    # Apply ID-based filters (more efficient than name-based)
    if sub_segment_id:
        query = query.filter(Employee.sub_segment_id == sub_segment_id)
    
    if project_id:
        query = query.filter(Employee.project_id == project_id)
    
    if team_id:
        query = query.filter(Employee.team_id == team_id)
    
    if role_id:
        query = query.filter(Employee.role_id == role_id)
    
    # Search by name or ZID
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Employee.full_name.ilike(search_term)) |
            (Employee.zid.ilike(search_term))
        )
    
    return query


def _get_skills_count(db: Session, employee_id: int) -> int:
    """
    Count skills for a specific employee.
    Returns 0 if no skills found.
    """
    count = db.query(func.count(EmployeeSkill.emp_skill_id)).filter(
        EmployeeSkill.employee_id == employee_id
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_employee_responses(
    db: Session,
    employees: List[Employee]
) -> List[EmployeeResponse]:
    """
    Build EmployeeResponse list from employee models.
    Queries skills count for each employee.
    """
    response_items = []
    
    for employee in employees:
        skills_count = _get_skills_count(db, employee.employee_id)
        
        employee_data = EmployeeResponse(
            employee_id=employee.employee_id,
            zid=employee.zid,
            full_name=employee.full_name,
            role=employee.role,
            start_date_of_working=employee.start_date_of_working,
            organization=_build_organization_info(employee),
            skills_count=skills_count
        )
        response_items.append(employee_data)
    
    return response_items


def _build_organization_info(employee: Employee) -> OrganizationInfo:
    """
    Build OrganizationInfo from employee relationships.
    Pure function - no DB access.
    """
    return OrganizationInfo(
        sub_segment=employee.sub_segment.sub_segment_name,
        project=employee.project.project_name,
        team=employee.team.team_name
    )
