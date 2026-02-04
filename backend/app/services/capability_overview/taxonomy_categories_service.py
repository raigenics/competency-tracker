"""
Taxonomy Categories Service - GET /skills/capability/categories

Handles lightweight category list for lazy-loading taxonomy page.
Returns categories with counts only (no subcategories/skills).
Zero dependencies on other services.
"""
import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import SkillCategory, SkillSubcategory, Skill
from app.schemas.skill import CategoriesResponse, CategorySummaryItem

logger = logging.getLogger(__name__)


def get_categories_for_lazy_loading(db: Session) -> CategoriesResponse:
    """
    Get lightweight list of all categories with counts only.
    Used for initial page load to minimize data transfer.
    
    Args:
        db: Database session
    
    Returns:
        CategoriesResponse with list of categories with subcategory_count and skill_count
    """
    logger.info("Fetching categories with counts for lazy loading")
    
    # Query all categories
    categories = _query_all_categories(db)
    
    # Build response with counts
    category_items = _build_category_summary_items(db, categories)
    
    logger.info(f"Returning {len(category_items)} categories")
    return CategoriesResponse(categories=category_items)


# === DATABASE QUERIES ===

def _query_all_categories(db: Session) -> List[SkillCategory]:
    """Query all categories, ordered by name."""
    return db.query(SkillCategory).order_by(
        SkillCategory.category_name
    ).all()


def _query_subcategory_count(db: Session, category_id: int) -> int:
    """Count subcategories in a category."""
    count = db.query(func.count(SkillSubcategory.subcategory_id)).filter(
        SkillSubcategory.category_id == category_id
    ).scalar()
    
    return count or 0


def _query_skill_count_for_category(db: Session, category_id: int) -> int:
    """
    Count skills in a category (via subcategory join).
    Returns 0 if no skills found.
    """
    count = db.query(func.count(Skill.skill_id)).join(
        SkillSubcategory
    ).filter(
        SkillSubcategory.category_id == category_id
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_category_summary_items(
    db: Session,
    categories: List[SkillCategory]
) -> List[CategorySummaryItem]:
    """
    Build CategorySummaryItem list from categories.
    Queries counts for each category.
    """
    category_items = []
    
    for category in categories:
        subcategory_count = _query_subcategory_count(db, category.category_id)
        skill_count = _query_skill_count_for_category(db, category.category_id)
        
        category_items.append(CategorySummaryItem(
            category_id=category.category_id,
            category_name=category.category_name,
            subcategory_count=subcategory_count,
            skill_count=skill_count
        ))
    
    return category_items
