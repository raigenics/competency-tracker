"""
Taxonomy Search Service - GET /skills/capability/search

Handles skill search across the entire taxonomy.
Returns matching skills with their full hierarchy path (category → subcategory → skill).
Zero dependencies on other services.
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models import Skill, SkillSubcategory, SkillCategory
from app.schemas.skill import SkillSearchResponse, SkillSearchResultItem

logger = logging.getLogger(__name__)


def search_skills_in_taxonomy(db: Session, query: str) -> SkillSearchResponse:
    """
    Search for skills by name across the entire taxonomy.
    Returns matching skills with their full hierarchy path (category → subcategory → skill).
    
    This endpoint enables instant search without requiring the tree to be expanded first.
    Query is case-insensitive and matches partial skill names.
    
    Args:
        db: Database session
        query: Search query (minimum 2 characters, validated by router)
    
    Returns:
        SkillSearchResponse with matching skills and their hierarchy
    """
    logger.info(f"Searching skills in taxonomy with query: '{query}'")
    
    # Search skills with full hierarchy
    search_results = _query_skills_with_hierarchy(db, query)
    
    # Transform to response format
    results = _build_search_results(search_results)
    
    logger.info(f"Found {len(results)} skills matching '{query}'")
    
    return SkillSearchResponse(
        results=results,
        count=len(results)
    )


# === DATABASE QUERIES ===

def _query_skills_with_hierarchy(db: Session, query: str) -> List[tuple]:
    """
    Search skills with case-insensitive partial match.
    Join with subcategory and category to get full hierarchy.
    Returns list of (Skill, SkillSubcategory, SkillCategory) tuples.
    """
    return db.query(Skill, SkillSubcategory, SkillCategory).join(
        SkillSubcategory,
        Skill.subcategory_id == SkillSubcategory.subcategory_id
    ).join(
        SkillCategory,
        SkillSubcategory.category_id == SkillCategory.category_id
    ).filter(
        Skill.skill_name.ilike(f"%{query}%")
    ).order_by(
        SkillCategory.category_name,
        SkillSubcategory.subcategory_name,
        Skill.skill_name
    ).all()


# === RESPONSE BUILDING ===

def _build_search_results(
    raw_results: List[tuple]
) -> List[SkillSearchResultItem]:
    """
    Transform raw query results to SkillSearchResultItem list.
    Pure function - no DB access.
    
    Args:
        raw_results: List of (Skill, SkillSubcategory, SkillCategory) tuples
    
    Returns:
        List of SkillSearchResultItem with full hierarchy
    """
    return [
        SkillSearchResultItem(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            category_id=category.category_id,
            category_name=category.category_name,
            subcategory_id=subcategory.subcategory_id,
            subcategory_name=subcategory.subcategory_name
        )
        for skill, subcategory, category in raw_results
    ]
