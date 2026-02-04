"""
Taxonomy Tree Service - GET /skills/taxonomy/tree

Handles complete skill taxonomy tree with all categories, subcategories, and skills.
Returns ALL categories from database, even if they have no subcategories/skills.
Zero dependencies on other services.
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models import Skill, SkillCategory, SkillSubcategory
from app.schemas.skill import (
    TaxonomyTreeResponse, TaxonomyCategoryItem,
    TaxonomySubcategoryItem, TaxonomySkillItem
)

logger = logging.getLogger(__name__)


def get_taxonomy_tree(db: Session) -> TaxonomyTreeResponse:
    """
    Get complete skill taxonomy tree with all categories, subcategories, and skills.
    Returns ALL categories from database, even if they have no subcategories or skills.
    
    Args:
        db: Database session
    
    Returns:
        TaxonomyTreeResponse with complete nested structure
    """
    logger.info("Fetching complete skill taxonomy tree")
    
    # Query all categories (no filtering)
    categories = _query_all_categories(db)
    logger.info(f"Found {len(categories)} categories in database")
    
    # Build nested tree structure
    taxonomy_categories = _build_taxonomy_tree(db, categories)
    
    total_subcategories = sum(len(c.subcategories) for c in taxonomy_categories)
    logger.info(f"Taxonomy tree built: {len(taxonomy_categories)} categories, "
                f"{total_subcategories} subcategories total")
    
    return TaxonomyTreeResponse(categories=taxonomy_categories)


# === DATABASE QUERIES ===

def _query_all_categories(db: Session) -> List[SkillCategory]:
    """
    Query ALL categories from database, ordered by name.
    No filtering applied.
    """
    return db.query(SkillCategory).order_by(
        SkillCategory.category_name
    ).all()


def _query_subcategories_for_category(
    db: Session,
    category_id: int
) -> List[SkillSubcategory]:
    """
    Query all subcategories for a specific category, ordered by name.
    """
    return db.query(SkillSubcategory).filter(
        SkillSubcategory.category_id == category_id
    ).order_by(SkillSubcategory.subcategory_name).all()


def _query_skills_for_subcategory(
    db: Session,
    subcategory_id: int
) -> List[Skill]:
    """
    Query all skills for a specific subcategory, ordered by name.
    """
    return db.query(Skill).filter(
        Skill.subcategory_id == subcategory_id
    ).order_by(Skill.skill_name).all()


# === TREE BUILDING ===

def _build_taxonomy_tree(
    db: Session,
    categories: List[SkillCategory]
) -> List[TaxonomyCategoryItem]:
    """
    Build complete taxonomy tree from categories.
    Queries subcategories and skills for each category/subcategory.
    """
    taxonomy_categories = []
    
    for category in categories:
        subcategories = _query_subcategories_for_category(db, category.category_id)
        
        taxonomy_subcategories = _build_subcategory_items(db, subcategories)
        
        # Add category even if it has no subcategories (empty list is ok)
        taxonomy_categories.append(
            TaxonomyCategoryItem(
                category_id=category.category_id,
                category_name=category.category_name,
                subcategories=taxonomy_subcategories
            )
        )
    
    return taxonomy_categories


def _build_subcategory_items(
    db: Session,
    subcategories: List[SkillSubcategory]
) -> List[TaxonomySubcategoryItem]:
    """
    Build subcategory items with their skills.
    Pure transformation for each subcategory.
    """
    taxonomy_subcategories = []
    
    for subcategory in subcategories:
        skills = _query_skills_for_subcategory(db, subcategory.subcategory_id)
        
        taxonomy_skills = _build_skill_items(skills)
        
        taxonomy_subcategories.append(
            TaxonomySubcategoryItem(
                subcategory_id=subcategory.subcategory_id,
                subcategory_name=subcategory.subcategory_name,
                skills=taxonomy_skills
            )
        )
    
    return taxonomy_subcategories


def _build_skill_items(skills: List[Skill]) -> List[TaxonomySkillItem]:
    """
    Build skill items from skill models.
    Pure function - no DB access.
    """
    return [
        TaxonomySkillItem(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name
        )
        for skill in skills
    ]
