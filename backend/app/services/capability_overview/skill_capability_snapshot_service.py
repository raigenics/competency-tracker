"""
Skill Capability Snapshot Service - GET /skills/{skill_id}/capability-snapshot

Handles capability snapshot KPI queries for a specific skill.
Zero dependencies on other services.

Returns:
    - employee_count: Employees mapped to this skill
    - certified_count: Employees with a certification tagged to this skill
    - team_count: Distinct teams with employees having this skill
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import EmployeeSkill, Employee
from app.schemas.skill import SkillCapabilitySnapshotResponse

logger = logging.getLogger(__name__)


def get_skill_capability_snapshot(db: Session, skill_id: int) -> SkillCapabilitySnapshotResponse:
    """
    Get capability snapshot KPIs for a specific skill.
    
    Args:
        db: Database session
        skill_id: The skill ID to fetch KPIs for
    
    Returns:
        SkillCapabilitySnapshotResponse with employee_count, certified_count, team_count
    """
    logger.info(f"Fetching capability snapshot for skill_id: {skill_id}")
    
    # Query all stats
    employee_count = _query_employee_count(db, skill_id)
    certified_count = _query_certified_count(db, skill_id)
    team_count = _query_team_count(db, skill_id)
    
    # Build response
    response = SkillCapabilitySnapshotResponse(
        employee_count=employee_count,
        certified_count=certified_count,
        team_count=team_count
    )
    
    logger.info(f"Capability snapshot for skill {skill_id}: "
                f"{employee_count} employees, {certified_count} certified, {team_count} teams")
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
        Count of distinct teams
    """
    return db.query(
        func.count(Employee.team_id.distinct())
    ).join(
        EmployeeSkill, Employee.employee_id == EmployeeSkill.employee_id
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        Employee.deleted_at.is_(None)
    ).scalar() or 0
