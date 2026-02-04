"""
Categories Service - GET /skills/categories/

Handles category listing with counts.
Zero dependencies on other services.
"""
import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Skill, SkillCategory, SkillSubcategory
from app.schemas.skill import CategoryResponse

logger = logging.getLogger(__name__)


def get_categories(db: Session) -> List[CategoryResponse]:
    """
    Get all skill categories with counts.
    
    Args:
        db: Database session
    
    Returns:
        List of CategoryResponse with skill and subcategory counts
    """
    logger.info("Fetching skill categories")
    
    # Query all categories
    categories = _query_all_categories(db)
    
    # Build responses with counts
    response_items = _build_category_responses(db, categories)
    
    logger.info(f"Returning {len(response_items)} categories")
    return response_items


# === DATABASE QUERIES ===

def _query_all_categories(db: Session) -> List[SkillCategory]:
    """Query all categories from database."""
    return db.query(SkillCategory).all()


def _query_skill_count_for_category(db: Session, category_id: int) -> int:
    """
    Count skills in a category (via subcategories join).
    Returns 0 if no skills found.
    """
    count = db.query(func.count(Skill.skill_id)).join(
        SkillSubcategory
    ).filter(
        SkillSubcategory.category_id == category_id
    ).scalar()
    
    return count or 0


def _query_subcategory_count_for_category(db: Session, category_id: int) -> int:
    """
    Count subcategories in a category.
    Returns 0 if no subcategories found.
    """
    count = db.query(func.count(SkillSubcategory.subcategory_id)).filter(
        SkillSubcategory.category_id == category_id
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_category_responses(
    db: Session, 
    categories: List[SkillCategory]
) -> List[CategoryResponse]:
    """
    Build CategoryResponse list from category models.
    Queries counts for each category.
    """
    response_items = []
    
    for category in categories:
        skill_count = _query_skill_count_for_category(db, category.category_id)
        subcategory_count = _query_subcategory_count_for_category(db, category.category_id)
        
        category_data = CategoryResponse(
            category_id=category.category_id,
            category_name=category.category_name,
            skill_count=skill_count,
            subcategory_count=subcategory_count
        )
        response_items.append(category_data)
    
    return response_items
