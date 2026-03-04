"""
Skill Employees Summary Service - GET /skills/{skill_id}/employees/summary

Aggregates summary statistics for the View Employees screen.
Returns employee_count, avg_proficiency, certified_count, team_count for a skill.

Zero dependencies on other services.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import EmployeeSkill, Employee
from app.schemas.skill import SkillEmployeesSummaryResponse

logger = logging.getLogger(__name__)


def get_skill_employees_summary(db: Session, skill_id: int) -> SkillEmployeesSummaryResponse:
    """
    Get aggregated summary statistics for employees with a specific skill.
    
    Args:
        db: Database session
        skill_id: The skill ID to fetch summary for
    
    Returns:
        SkillEmployeesSummaryResponse with employee_count, avg_proficiency, 
        certified_count, team_count
    """
    logger.info(f"Fetching employees summary for skill_id: {skill_id}")
    
    # Query all stats
    employee_count = _query_employee_count(db, skill_id)
    avg_proficiency = _query_avg_proficiency(db, skill_id)
    certified_count = _query_certified_count(db, skill_id)
    team_count = _query_team_count(db, skill_id)
    
    # Build response
    response = SkillEmployeesSummaryResponse(
        employee_count=employee_count,
        avg_proficiency=avg_proficiency,
        certified_count=certified_count,
        team_count=team_count
    )
    
    logger.info(f"Employees summary for skill {skill_id}: "
                f"{employee_count} employees, avg_proficiency={avg_proficiency}, "
                f"{certified_count} certified, {team_count} teams")
    return response


# === DATABASE QUERIES (Repository layer) ===

def _query_employee_count(db: Session, skill_id: int) -> int:
    """
    Count distinct employees mapped to this skill.
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Count of distinct employees with this skill
    """
    return db.query(
        func.count(EmployeeSkill.employee_id.distinct())
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None)
    ).scalar() or 0


def _query_avg_proficiency(db: Session, skill_id: int) -> float:
    """
    Calculate average proficiency for employees with this skill.
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Average proficiency value rounded to 1 decimal, or 0.0 if no data
    """
    result = db.query(
        func.avg(EmployeeSkill.proficiency_level_id)
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        EmployeeSkill.proficiency_level_id.isnot(None)
    ).scalar()
    
    if result is None:
        return 0.0
    return round(float(result), 1)


def _query_certified_count(db: Session, skill_id: int) -> int:
    """
    Count distinct employees with a certification for this skill.
    Certification is non-null and non-empty.
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Count of distinct employees with certification for this skill
    """
    return db.query(
        func.count(EmployeeSkill.employee_id.distinct())
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        EmployeeSkill.certification.isnot(None),
        EmployeeSkill.certification != ''
    ).scalar() or 0


def _query_team_count(db: Session, skill_id: int) -> int:
    """
    Count distinct teams that have employees with this skill.
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Count of distinct teams with employees having this skill
    """
    # NOTE: Employee.team is a relationship, NOT a column.
    # Use Employee.team_id (the FK column) for the query.
    return db.query(
        func.count(Employee.team_id.distinct())
    ).join(
        EmployeeSkill, Employee.employee_id == EmployeeSkill.employee_id
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        Employee.team_id.isnot(None)
    ).scalar() or 0
