"""
Taxonomy Skills Service - GET /skills/capability/subcategories/{subcategory_id}/skills

Handles skill list for a specific subcategory in lazy-loading taxonomy.
Returns skills when user expands a subcategory node.
Zero dependencies on other services.

IN-USE FILTERING:
Only returns skills that have at least one row in employee_skills (where deleted_at IS NULL).
This ensures the taxonomy tree shows only skills that are actually used by employees.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import exists

from app.models import Skill, SkillSubcategory, SkillCategory, EmployeeSkill
from app.schemas.skill import SkillsResponse, TaxonomySkillItem

logger = logging.getLogger(__name__)


def get_skills_for_subcategory(
    db: Session,
    subcategory_id: int
) -> SkillsResponse:
    """
    Get skills for a specific subcategory.
    Used when user expands a subcategory node.
    
    Args:
        db: Database session
        subcategory_id: The subcategory ID to fetch skills for
    
    Returns:
        SkillsResponse with list of skills and parent category/subcategory info
        
    Raises:
        ValueError: If subcategory not found
    """
    logger.info(f"Fetching skills for subcategory {subcategory_id}")
    
    # Verify subcategory exists and get category info
    subcategory = _query_subcategory_by_id(db, subcategory_id)
    if not subcategory:
        raise ValueError(f"Subcategory {subcategory_id} not found")
    
    # Get category info
    category = _query_category_by_id(db, subcategory.category_id)
    
    # Query skills
    skills = _query_skills_for_subcategory(db, subcategory_id)
    
    # Build response
    skill_items = _build_skill_items(skills)
    
    logger.info(f"Returning {len(skill_items)} skills for subcategory {subcategory_id}")
    
    return SkillsResponse(
        subcategory_id=subcategory.subcategory_id,
        subcategory_name=subcategory.subcategory_name,
        category_id=category.category_id,
        category_name=category.category_name,
        skills=skill_items
    )


# === DATABASE QUERIES ===

def _query_subcategory_by_id(
    db: Session,
    subcategory_id: int
) -> Optional[SkillSubcategory]:
    """
    Query subcategory by ID.
    Returns None if not found.
    """
    return db.query(SkillSubcategory).filter(
        SkillSubcategory.subcategory_id == subcategory_id
    ).first()


def _query_category_by_id(db: Session, category_id: int) -> Optional[SkillCategory]:
    """
    Query category by ID.
    Returns None if not found.
    """
    return db.query(SkillCategory).filter(
        SkillCategory.category_id == category_id
    ).first()


def _query_skills_for_subcategory(
    db: Session,
    subcategory_id: int
) -> List[Skill]:
    """
    Query skills for a subcategory that are "in use" (have at least one employee_skills row).
    
    A skill is considered "in use" if:
    - EXISTS at least one row in employee_skills with matching skill_id
    - The employee_skills row is not soft-deleted (deleted_at IS NULL)
    
    Ordered by skill_name for deterministic results.
    """
    # Subquery: skill is in use if it has at least one non-deleted employee_skills row
    in_use_subquery = exists().where(
        EmployeeSkill.skill_id == Skill.skill_id,
        EmployeeSkill.deleted_at.is_(None)
    )
    
    return db.query(Skill).filter(
        Skill.subcategory_id == subcategory_id,
        in_use_subquery
    ).order_by(Skill.skill_name).all()


# === RESPONSE BUILDING ===

def _build_skill_items(skills: List[Skill]) -> List[TaxonomySkillItem]:
    """
    Build TaxonomySkillItem list from skill models.
    Pure function - no DB access.
    """
    return [
        TaxonomySkillItem(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name
        )
        for skill in skills
    ]
