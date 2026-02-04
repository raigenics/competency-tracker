"""
Stats Service - GET /employees/stats/overview

Handles employee statistics and overview.
Zero dependencies on other services.
"""
import logging
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Employee, EmployeeSkill, SubSegment, Project, Team
from app.schemas.employee import EmployeeStatsResponse

logger = logging.getLogger(__name__)


def get_employee_stats(db: Session) -> EmployeeStatsResponse:
    """
    Get employee statistics and overview.
    
    Args:
        db: Database session
    
    Returns:
        EmployeeStatsResponse with totals and breakdowns
    """
    logger.info("Fetching employee statistics")
    
    # Query all statistics
    total_employees = _query_total_employees(db)
    by_sub_segment = _query_employees_by_sub_segment(db)
    by_project = _query_employees_by_project(db)
    by_team = _query_employees_by_team(db)
    avg_skills = _query_average_skills_per_employee(db)
    
    # Build response
    response = _build_stats_response(
        total_employees, by_sub_segment, by_project, by_team, avg_skills
    )
    
    logger.info(f"Stats: {total_employees} total employees, "
                f"avg {response.avg_skills_per_employee} skills/employee")
    return response


# === DATABASE QUERIES ===

def _query_total_employees(db: Session) -> int:
    """Count total employees in database."""
    return db.query(func.count(Employee.employee_id)).scalar() or 0


def _query_employees_by_sub_segment(db: Session) -> Dict[str, int]:
    """
    Count employees grouped by sub-segment.
    Returns dict of {sub_segment_name: employee_count}.
    """
    results = db.query(
        SubSegment.sub_segment_name,
        func.count(Employee.employee_id)
    ).join(Employee).group_by(SubSegment.sub_segment_name).all()
    
    return dict(results)


def _query_employees_by_project(db: Session) -> Dict[str, int]:
    """
    Count employees grouped by project.
    Returns dict of {project_name: employee_count}.
    """
    results = db.query(
        Project.project_name,
        func.count(Employee.employee_id)
    ).join(Employee).group_by(Project.project_name).all()
    
    return dict(results)


def _query_employees_by_team(db: Session) -> Dict[str, int]:
    """
    Count employees grouped by team.
    Returns dict of {team_name: employee_count}.
    """
    results = db.query(
        Team.team_name,
        func.count(Employee.employee_id)
    ).join(Employee).group_by(Team.team_name).all()
    
    return dict(results)


def _query_average_skills_per_employee(db: Session) -> float:
    """
    Calculate average number of skills per employee.
    Uses subquery to count skills per employee, then averages.
    """
    avg_skills = db.query(func.avg(
        db.query(func.count(EmployeeSkill.emp_skill_id))
        .filter(EmployeeSkill.employee_id == Employee.employee_id)
        .scalar_subquery()
    )).scalar()
    
    return avg_skills or 0.0


# === RESPONSE BUILDING ===

def _build_stats_response(
    total_employees: int,
    by_sub_segment: Dict[str, int],
    by_project: Dict[str, int],
    by_team: Dict[str, int],
    avg_skills: float
) -> EmployeeStatsResponse:
    """
    Build EmployeeStatsResponse from queried data.
    Pure function - no DB access.
    """
    return EmployeeStatsResponse(
        total_employees=total_employees,
        by_sub_segment=by_sub_segment,
        by_project=by_project,
        by_team=by_team,
        avg_skills_per_employee=round(avg_skills, 2)
    )
