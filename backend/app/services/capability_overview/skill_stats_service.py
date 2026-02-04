"""
Skill Stats Service - GET /skills/stats/overview

Handles skill statistics and overview queries.
Zero dependencies on other services.
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import Skill, SkillCategory, SkillSubcategory, EmployeeSkill
from app.schemas.skill import SkillStatsResponse

logger = logging.getLogger(__name__)


def get_skill_stats(db: Session) -> SkillStatsResponse:
    """
    Get skill statistics and overview.
    
    Args:
        db: Database session
    
    Returns:
        SkillStatsResponse with totals, breakdowns, and top skills
    """
    logger.info("Fetching skill statistics")
    
    # Query all stats
    total_skills = _query_total_skills(db)
    by_category = _query_skills_by_category(db)
    by_subcategory = _query_skills_by_subcategory(db)
    most_popular = _query_most_popular_skills(db)
    
    # Build response
    response = _build_stats_response(
        total_skills, by_category, by_subcategory, most_popular
    )
    
    logger.info(f"Stats: {total_skills} total skills, "
                f"{len(by_category)} categories, {len(most_popular)} top skills")
    return response


# === DATABASE QUERIES ===

def _query_total_skills(db: Session) -> int:
    """Count total skills in database."""
    return db.query(func.count(Skill.skill_id)).scalar() or 0


def _query_skills_by_category(db: Session) -> Dict[str, int]:
    """
    Count skills grouped by category.
    Returns dict of {category_name: skill_count}.
    """
    results = db.query(
        SkillCategory.category_name, 
        func.count(Skill.skill_id)
    ).join(Skill).group_by(SkillCategory.category_name).all()
    
    return dict(results)


def _query_skills_by_subcategory(db: Session) -> Dict[str, int]:
    """
    Count skills grouped by subcategory.
    Returns dict of {subcategory_name: skill_count}.
    """
    results = db.query(
        SkillSubcategory.subcategory_name,
        func.count(Skill.skill_id)
    ).join(Skill).group_by(SkillSubcategory.subcategory_name).all()
    
    return dict(results)


def _query_most_popular_skills(db: Session, limit: int = 10) -> List[tuple]:
    """
    Query top N skills by employee count.
    Returns list of (skill_name, employee_count) tuples.
    """
    return db.query(
        Skill.skill_name,
        func.count(EmployeeSkill.employee_id.distinct())
    ).join(EmployeeSkill).group_by(
        Skill.skill_name
    ).order_by(
        desc(func.count(EmployeeSkill.employee_id.distinct()))
    ).limit(limit).all()


# === RESPONSE BUILDING ===

def _build_stats_response(
    total_skills: int,
    by_category: Dict[str, int],
    by_subcategory: Dict[str, int],
    most_popular_raw: List[tuple]
) -> SkillStatsResponse:
    """
    Build SkillStatsResponse from queried data.
    Pure function - no DB access.
    """
    most_popular_skills = _format_popular_skills(most_popular_raw)
    
    return SkillStatsResponse(
        total_skills=total_skills,
        by_category=by_category,
        by_subcategory=by_subcategory,
        most_popular_skills=most_popular_skills
    )


def _format_popular_skills(raw_data: List[tuple]) -> List[Dict[str, any]]:
    """
    Transform raw tuples to list of dicts.
    Pure function.
    """
    return [
        {"skill_name": skill_name, "employee_count": count}
        for skill_name, count in raw_data
    ]
