"""
Subcategories Service - GET /skills/subcategories/

Handles subcategory listing with optional category filter.
Zero dependencies on other services.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import SkillCategory, SkillSubcategory, Skill
from app.schemas.skill import SubcategoryResponse

logger = logging.getLogger(__name__)


def get_subcategories(
    db: Session,
    category: Optional[str] = None
) -> List[SubcategoryResponse]:
    """
    Get all skill subcategories with optional category filter.
    
    Args:
        db: Database session
        category: Optional category name filter (case-insensitive partial match)
    
    Returns:
        List of SubcategoryResponse with skill counts
    """
    logger.info(f"Fetching subcategories (category filter: {category})")
    
    # Query subcategories with optional filter
    subcategories = _query_subcategories_with_filter(db, category)
    
    # Build responses with counts
    response_items = _build_subcategory_responses(db, subcategories)
    
    logger.info(f"Returning {len(response_items)} subcategories")
    return response_items


# === DATABASE QUERIES ===

def _query_subcategories_with_filter(
    db: Session,
    category: Optional[str]
) -> List[SkillSubcategory]:
    """
    Query subcategories with optional category filter.
    Eager loads category relationship.
    """
    query = db.query(SkillSubcategory).options(
        joinedload(SkillSubcategory.category)
    )
    
    if category:
        query = query.join(SkillCategory).filter(
            SkillCategory.category_name.ilike(f"%{category}%")
        )
    
    return query.all()


def _query_skill_count_for_subcategory(db: Session, subcategory_id: int) -> int:
    """
    Count skills in a subcategory.
    Returns 0 if no skills found.
    """
    count = db.query(func.count(Skill.skill_id)).filter(
        Skill.subcategory_id == subcategory_id
    ).scalar()
    
    return count or 0


# === RESPONSE BUILDING ===

def _build_subcategory_responses(
    db: Session,
    subcategories: List[SkillSubcategory]
) -> List[SubcategoryResponse]:
    """
    Build SubcategoryResponse list from subcategory models.
    Queries skill count for each subcategory.
    """
    response_items = []
    
    for subcategory in subcategories:
        skill_count = _query_skill_count_for_subcategory(db, subcategory.subcategory_id)
        
        subcategory_data = SubcategoryResponse(
            subcategory_id=subcategory.subcategory_id,
            subcategory_name=subcategory.subcategory_name,
            category_name=subcategory.category.category_name,
            skill_count=skill_count
        )
        response_items.append(subcategory_data)
    
    return response_items
