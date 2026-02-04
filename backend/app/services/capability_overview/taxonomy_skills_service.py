"""
Taxonomy Skills Service - GET /skills/capability/subcategories/{subcategory_id}/skills

Handles skill list for a specific subcategory in lazy-loading taxonomy.
Returns skills when user expands a subcategory node.
Zero dependencies on other services.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Skill, SkillSubcategory, SkillCategory
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
    Query all skills for a subcategory, ordered by name.
    """
    return db.query(Skill).filter(
        Skill.subcategory_id == subcategory_id
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
