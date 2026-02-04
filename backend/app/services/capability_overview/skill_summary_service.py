"""
Skill Summary Service - GET /skills/{skill_id}/summary

Handles skill summary statistics with exact skill_id matching.
Returns employees who have THIS SPECIFIC SKILL only, not related skills with similar names.
Zero dependencies on other services.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Skill, EmployeeSkill
from app.schemas.skill import SkillSummaryResponse

logger = logging.getLogger(__name__)


def get_skill_summary(db: Session, skill_id: int) -> SkillSummaryResponse:
    """
    Get summary statistics for a specific skill using EXACT skill_id match.
    
    Returns employees who have THIS SPECIFIC SKILL only, not related skills with similar names.
    For example, clicking "React" returns only employees with React, NOT ReactJS or React.js.
    
    Args:
        db: Database session
        skill_id: The skill ID to fetch summary for
    
    Returns:
        SkillSummaryResponse with employee count, avg experience, and certified count
        
    Raises:
        ValueError: If skill not found
    """
    logger.info(f"Fetching summary for skill_id: {skill_id}")
    
    # Verify skill exists
    skill = _query_skill_by_id(db, skill_id)
    if not skill:
        raise ValueError(f"Skill with ID {skill_id} not found")
    
    logger.info(f"Fetching employees for exact skill_id: {skill_id} ('{skill.skill_name}')")
    
    # Query stats using exact skill_id match
    employee_count = _query_employee_count(db, skill_id)
    employee_ids = _query_employee_ids(db, skill_id)
    avg_experience = _query_average_experience(db, skill_id)
    certified_count = _query_certified_employee_count(db, skill_id)
    
    # Build response
    response = _build_skill_summary_response(
        skill, employee_count, employee_ids, avg_experience, certified_count
    )
    
    logger.info(f"Skill summary for {skill.skill_name} (ID: {skill_id}, EXACT MATCH): "
                f"employees={employee_count} (IDs: {len(employee_ids)}), "
                f"avg_exp={response.avg_experience_years}y, certified={certified_count}")
    
    return response


# === DATABASE QUERIES ===

def _query_skill_by_id(db: Session, skill_id: int) -> Optional[Skill]:
    """
    Query skill by ID.
    Returns None if not found.
    """
    return db.query(Skill).filter(Skill.skill_id == skill_id).first()


def _query_employee_count(db: Session, skill_id: int) -> int:
    """
    Count distinct employees with THIS SPECIFIC SKILL.
    Uses exact skill_id match.
    """
    count = db.query(func.count(EmployeeSkill.employee_id.distinct())).filter(
        EmployeeSkill.skill_id == skill_id
    ).scalar()
    
    return count or 0


def _query_employee_ids(db: Session, skill_id: int) -> List[int]:
    """
    Get list of employee IDs with THIS SPECIFIC SKILL.
    Uses exact skill_id match.
    Returns sorted list for "View All" functionality.
    """
    results = db.query(EmployeeSkill.employee_id.distinct()).filter(
        EmployeeSkill.skill_id == skill_id
    ).order_by(EmployeeSkill.employee_id).all()
    
    return [row[0] for row in results]


def _query_average_experience(db: Session, skill_id: int) -> Optional[float]:
    """
    Calculate average years of experience for THIS SPECIFIC SKILL.
    Uses exact skill_id match.
    Ignores NULL and zero values.
    """
    return db.query(func.avg(EmployeeSkill.years_experience)).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.years_experience.isnot(None),
        EmployeeSkill.years_experience > 0
    ).scalar()


def _query_certified_employee_count(db: Session, skill_id: int) -> int:
    """
    Count distinct certified employees for THIS SPECIFIC SKILL.
    Uses exact skill_id match.
    
    Business rules:
    - Exclude NULL, empty string, and "no" (case-insensitive)
    - Count distinct employees (not rows)
    """
    count = db.query(func.count(EmployeeSkill.employee_id.distinct())).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.certification.isnot(None),
        func.nullif(func.trim(EmployeeSkill.certification), '') != None,
        func.lower(func.trim(EmployeeSkill.certification)) != 'no'
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_skill_summary_response(
    skill: Skill,
    employee_count: int,
    employee_ids: List[int],
    avg_experience: Optional[float],
    certified_count: int
) -> SkillSummaryResponse:
    """
    Build SkillSummaryResponse from queried data.
    Pure function - no DB access.
    """
    avg_experience_years = _round_to_one_decimal(avg_experience)
    
    return SkillSummaryResponse(
        skill_id=skill.skill_id,
        skill_name=skill.skill_name,
        employee_count=employee_count,
        employee_ids=employee_ids,
        avg_experience_years=avg_experience_years,
        certified_count=certified_count,  # Backward compatibility
        certified_employee_count=certified_count
    )


def _round_to_one_decimal(value: Optional[float]) -> float:
    """
    Round to 1 decimal place, return 0.0 if None.
    Pure function.
    """
    if value is None:
        return 0.0
    return round(float(value), 1)
