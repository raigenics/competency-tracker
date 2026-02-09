"""
Taxonomy Categories Service - GET /skills/capability/categories

Handles lightweight category list for lazy-loading taxonomy page.
Returns categories with counts only (no subcategories/skills).
Zero dependencies on other services.

IN-USE FILTERING:
Only returns categories that have at least one "in-use" subcategory (which has at least one "in-use" skill).
Subcategory and skill counts reflect only those with at least one employee_skills row (where deleted_at IS NULL).
"""
import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, exists

from app.models import SkillCategory, SkillSubcategory, Skill, EmployeeSkill
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
    """
    Query categories that have at least one "in-use" subcategory.
    
    A category is included only if it has at least one subcategory that has at least one skill with:
    - EXISTS at least one row in employee_skills with matching skill_id
    - The employee_skills row is not soft-deleted (deleted_at IS NULL)
    
    Ordered by category_name for deterministic results.
    """
    # Subquery: category has at least one in-use subcategory
    has_in_use_subcategory = exists().where(
        SkillSubcategory.category_id == SkillCategory.category_id,
        exists().where(
            Skill.subcategory_id == SkillSubcategory.subcategory_id,
            exists().where(
                EmployeeSkill.skill_id == Skill.skill_id,
                EmployeeSkill.deleted_at.is_(None)
            )
        )
    )
    
    return db.query(SkillCategory).filter(
        has_in_use_subcategory
    ).order_by(
        SkillCategory.category_name
    ).all()


def _query_subcategory_count(db: Session, category_id: int) -> int:
    """
    Count "in-use" subcategories in a category.
    
    Counts only subcategories that have at least one skill with at least one
    employee_skills row (where deleted_at IS NULL).
    """
    # Subquery: subcategory has at least one in-use skill
    has_in_use_skill = exists().where(
        Skill.subcategory_id == SkillSubcategory.subcategory_id,
        exists().where(
            EmployeeSkill.skill_id == Skill.skill_id,
            EmployeeSkill.deleted_at.is_(None)
        )
    )
    
    count = db.query(func.count(SkillSubcategory.subcategory_id)).filter(
        SkillSubcategory.category_id == category_id,
        has_in_use_skill
    ).scalar()
    
    return count or 0


def _query_skill_count_for_category(db: Session, category_id: int) -> int:
    """
    Count "in-use" skills in a category (via subcategory join).
    
    Counts only skills that have at least one employee_skills row (where deleted_at IS NULL).
    Returns 0 if no in-use skills found.
    """
    # Subquery: skill is in use
    in_use_subquery = exists().where(
        EmployeeSkill.skill_id == Skill.skill_id,
        EmployeeSkill.deleted_at.is_(None)
    )
    
    count = db.query(func.count(Skill.skill_id)).join(
        SkillSubcategory
    ).filter(
        SkillSubcategory.category_id == category_id,
        in_use_subquery
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
