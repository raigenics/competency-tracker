"""
Taxonomy Subcategories Service - GET /skills/capability/categories/{category_id}/subcategories

Handles subcategory list for a specific category in lazy-loading taxonomy.
Returns subcategories with skill counts when user expands a category node.
Zero dependencies on other services.

IN-USE FILTERING:
Only returns subcategories that have at least one "in-use" skill.
Skill counts reflect only skills with at least one employee_skills row (where deleted_at IS NULL).
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, exists

from app.models import SkillCategory, SkillSubcategory, Skill, EmployeeSkill
from app.schemas.skill import SubcategoriesResponse, SubcategorySummaryItem

logger = logging.getLogger(__name__)


def get_subcategories_for_category(
    db: Session,
    category_id: int
) -> SubcategoriesResponse:
    """
    Get subcategories for a specific category with skill counts.
    Used when user expands a category node.
    
    Args:
        db: Database session
        category_id: The category ID to fetch subcategories for
    
    Returns:
        SubcategoriesResponse with list of subcategories and parent category info
        
    Raises:
        ValueError: If category not found
    """
    logger.info(f"Fetching subcategories for category {category_id}")
    
    # Verify category exists
    category = _query_category_by_id(db, category_id)
    if not category:
        raise ValueError(f"Category {category_id} not found")
    
    # Query subcategories
    subcategories = _query_subcategories_for_category(db, category_id)
    
    # Build response with skill counts
    subcategory_items = _build_subcategory_summary_items(db, subcategories)
    
    logger.info(f"Returning {len(subcategory_items)} subcategories for category {category_id}")
    
    return SubcategoriesResponse(
        category_id=category.category_id,
        category_name=category.category_name,
        subcategories=subcategory_items
    )


# === DATABASE QUERIES ===

def _query_category_by_id(db: Session, category_id: int) -> Optional[SkillCategory]:
    """
    Query category by ID.
    Returns None if not found.
    """
    return db.query(SkillCategory).filter(
        SkillCategory.category_id == category_id
    ).first()


def _query_subcategories_for_category(
    db: Session,
    category_id: int
) -> List[SkillSubcategory]:
    """
    Query subcategories for a category that have at least one "in-use" skill.
    
    A subcategory is included only if it has at least one skill that:
    - EXISTS at least one row in employee_skills with matching skill_id
    - The employee_skills row is not soft-deleted (deleted_at IS NULL)
    
    Ordered by subcategory_name for deterministic results.
    """
    # Subquery: subcategory has at least one in-use skill
    has_in_use_skill = exists().where(
        Skill.subcategory_id == SkillSubcategory.subcategory_id,
        exists().where(
            EmployeeSkill.skill_id == Skill.skill_id,
            EmployeeSkill.deleted_at.is_(None)
        )
    )
    
    return db.query(SkillSubcategory).filter(
        SkillSubcategory.category_id == category_id,
        has_in_use_skill
    ).order_by(SkillSubcategory.subcategory_name).all()


def _query_skill_count_for_subcategory(db: Session, subcategory_id: int) -> int:
    """
    Count "in-use" skills in a subcategory.
    
    Counts only skills that have at least one employee_skills row (where deleted_at IS NULL).
    Returns 0 if no in-use skills found.
    """
    # Subquery: skill is in use
    in_use_subquery = exists().where(
        EmployeeSkill.skill_id == Skill.skill_id,
        EmployeeSkill.deleted_at.is_(None)
    )
    
    count = db.query(func.count(Skill.skill_id)).filter(
        Skill.subcategory_id == subcategory_id,
        in_use_subquery
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_subcategory_summary_items(
    db: Session,
    subcategories: List[SkillSubcategory]
) -> List[SubcategorySummaryItem]:
    """
    Build SubcategorySummaryItem list from subcategories.
    Queries skill count for each subcategory.
    """
    subcategory_items = []
    
    for subcategory in subcategories:
        skill_count = _query_skill_count_for_subcategory(db, subcategory.subcategory_id)
        
        subcategory_items.append(SubcategorySummaryItem(
            subcategory_id=subcategory.subcategory_id,
            subcategory_name=subcategory.subcategory_name,
            skill_count=skill_count
        ))
    
    return subcategory_items
