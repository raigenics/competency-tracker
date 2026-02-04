"""
Skill Detail Service - GET /skills/{skill_id}

Handles detailed skill information including proficiency distribution and averages.
Zero dependencies on other services.
"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Skill, SkillSubcategory, EmployeeSkill, ProficiencyLevel
from app.schemas.skill import SkillDetailResponse, CategoryInfo

logger = logging.getLogger(__name__)


def get_skill_detail(db: Session, skill_id: int) -> SkillDetailResponse:
    """
    Get detailed information about a specific skill.
    
    Args:
        db: Database session
        skill_id: The skill ID to fetch
    
    Returns:
        SkillDetailResponse with proficiency distribution and averages
        
    Raises:
        ValueError: If skill not found
    """
    logger.info(f"Fetching skill detail for ID: {skill_id}")
    
    # Query skill with relationships
    skill = _query_skill_by_id(db, skill_id)
    
    if not skill:
        raise ValueError(f"Skill with ID {skill_id} not found")
    
    # Get proficiency distribution
    proficiency_dist = _query_proficiency_distribution(db, skill_id)
    
    # Get averages
    avg_experience = _query_average_experience(db, skill_id)
    avg_interest = _query_average_interest(db, skill_id)
    
    # Get employee count
    employee_count = _query_employee_count(db, skill_id)
    
    # Build response
    response = _build_skill_detail_response(
        skill, employee_count, proficiency_dist, avg_experience, avg_interest
    )
    
    logger.info(f"Skill detail for '{skill.skill_name}': {employee_count} employees")
    return response


# === DATABASE QUERIES ===

def _query_skill_by_id(db: Session, skill_id: int) -> Optional[Skill]:
    """
    Query skill by ID with eager loading of relationships.
    Returns None if not found.
    """
    return db.query(Skill).options(
        joinedload(Skill.subcategory).joinedload(SkillSubcategory.category)
    ).filter(Skill.skill_id == skill_id).first()


def _query_proficiency_distribution(db: Session, skill_id: int) -> Dict[str, int]:
    """
    Get proficiency level distribution for a skill.
    Returns dict of {level_name: count}.
    """
    results = db.query(
        ProficiencyLevel.level_name, 
        func.count(EmployeeSkill.emp_skill_id)
    ).join(EmployeeSkill).filter(
        EmployeeSkill.skill_id == skill_id
    ).group_by(ProficiencyLevel.level_name).all()
    
    return dict(results)


def _query_average_experience(db: Session, skill_id: int) -> Optional[float]:
    """
    Calculate average years of experience for a skill.
    Ignores NULL values. Returns None if no data.
    """
    return db.query(func.avg(EmployeeSkill.years_experience)).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.years_experience.isnot(None)
    ).scalar()


def _query_average_interest(db: Session, skill_id: int) -> Optional[float]:
    """
    Calculate average interest level for a skill.
    Ignores NULL values. Returns None if no data.
    """
    return db.query(func.avg(EmployeeSkill.interest_level)).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.interest_level.isnot(None)
    ).scalar()


def _query_employee_count(db: Session, skill_id: int) -> int:
    """Count distinct employees with this skill."""
    return db.query(func.count(EmployeeSkill.employee_id.distinct())).filter(
        EmployeeSkill.skill_id == skill_id
    ).scalar() or 0


# === RESPONSE BUILDING ===

def _build_skill_detail_response(
    skill: Skill,
    employee_count: int,
    proficiency_dist: Dict[str, int],
    avg_experience: Optional[float],
    avg_interest: Optional[float]
) -> SkillDetailResponse:
    """
    Build SkillDetailResponse from queried data.
    Pure function - no DB access.
    """
    return SkillDetailResponse(
        skill_id=skill.skill_id,
        skill_name=skill.skill_name,
        category=_build_category_info(skill),
        employee_count=employee_count,
        proficiency_distribution=proficiency_dist,
        avg_years_experience=_round_average(avg_experience),
        avg_interest_level=_round_average(avg_interest)
    )


def _build_category_info(skill: Skill) -> CategoryInfo:
    """
    Build CategoryInfo from skill's relationships.
    Pure function - no DB access.
    """
    return CategoryInfo(
        category_id=skill.category.category_id,
        category_name=skill.category.category_name,
        subcategory_id=skill.subcategory.subcategory_id if skill.subcategory else None,
        subcategory_name=skill.subcategory.subcategory_name if skill.subcategory else None
    )


def _round_average(value: Optional[float]) -> Optional[float]:
    """
    Round average to 2 decimal places.
    Pure function.
    """
    return round(value, 2) if value is not None else None
