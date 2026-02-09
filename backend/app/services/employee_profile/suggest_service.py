"""
Suggest Service - GET /employees/suggest

Handles employee autocomplete suggestions.
Zero dependencies on other services.
"""
import logging
from typing import List
from sqlalchemy.orm import Session, joinedload

from app.models import Employee
from app.schemas.employee import EmployeeSuggestion

logger = logging.getLogger(__name__)


def get_employee_suggestions(
    db: Session,
    query: str,
    limit: int
) -> List[EmployeeSuggestion]:
    """
    Get employee suggestions for autocomplete.
    
    Args:
        db: Database session
        query: Search query (minimum 2 characters) - searches name and ZID
        limit: Maximum number of results (1-20)
    
    Returns:
        List of EmployeeSuggestion with employee info and organization
    """
    logger.info(f"Fetching employee suggestions for query: '{query}' with limit: {limit}")
    
    # Query employees matching search term
    employees = _query_employees_by_search(db, query, limit)
    
    # Build suggestions
    suggestions = _build_suggestions(employees)
    
    logger.info(f"Returning {len(suggestions)} suggestions for query: '{query}'")
    return suggestions


# === DATABASE QUERIES ===

def _query_employees_by_search(
    db: Session,
    query: str,
    limit: int
) -> List[Employee]:
    """
    Search for employees by full name OR ZID (case-insensitive partial match).
    Eager loads organization relationships.
    
    NORMALIZED SCHEMA: sub_segment/project derived via team relationship chain.
    """
    from app.models.team import Team
    from app.models.project import Project
    
    search_term = f"%{query}%"
    
    return db.query(Employee).options(
        # Canonical chain: team -> project -> sub_segment
        joinedload(Employee.team)
            .joinedload(Team.project)
            .joinedload(Project.sub_segment)
    ).filter(
        (Employee.full_name.ilike(search_term)) | 
        (Employee.zid.ilike(search_term))
    ).limit(limit).all()


# === RESPONSE BUILDING ===

def _build_suggestions(employees: List[Employee]) -> List[EmployeeSuggestion]:
    """
    Build EmployeeSuggestion list from employee models.
    Pure function - no DB access.
    """
    suggestions = []
    
    for employee in employees:
        suggestion = EmployeeSuggestion(
            employee_id=employee.employee_id,
            zid=employee.zid,
            full_name=employee.full_name,
            sub_segment=employee.sub_segment.sub_segment_name if employee.sub_segment else None,
            project=employee.project.project_name if employee.project else None,
            team=employee.team.team_name if employee.team else None
        )
        suggestions.append(suggestion)
    
    return suggestions
