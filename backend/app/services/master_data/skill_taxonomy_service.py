"""
Service for fetching Skill Taxonomy hierarchy.

Implements optimized query pattern using 3 separate queries to avoid N+1:
1. Fetch all categories
2. Fetch all subcategories
3. Fetch all skills with employee counts

Builds the nested hierarchy in Python for efficient data transfer.
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.employee_skill import EmployeeSkill
from app.schemas.master_data_taxonomy import (
    TaxonomyAliasDTO,
    TaxonomySkillDTO,
    TaxonomySubCategoryDTO,
    TaxonomyCategoryDTO,
    SkillTaxonomyResponse,
)

logger = logging.getLogger(__name__)


def get_skill_taxonomy(
    db: Session,
    search_query: Optional[str] = None
) -> SkillTaxonomyResponse:
    """
    Fetch the complete skill taxonomy hierarchy.
    
    Uses 4 queries + 1 aggregation query to build the full tree efficiently:
    1. Categories
    2. Subcategories
    3. Skills
    4. Aliases
    5. Employee counts per skill (grouped query)
    
    Args:
        db: Database session
        search_query: Optional search term to filter skills by name
        
    Returns:
        SkillTaxonomyResponse with nested categories -> subcategories -> skills
    """
    logger.info(f"Fetching skill taxonomy hierarchy (search={search_query})")
    
    # Query 1: Get all categories sorted by name (exclude soft-deleted)
    categories = (
        db.query(SkillCategory)
        .filter(SkillCategory.deleted_at.is_(None))
        .order_by(SkillCategory.category_name)
        .all()
    )
    
    # Query 2: Get all subcategories sorted by name (exclude soft-deleted)
    subcategories = (
        db.query(SkillSubcategory)
        .filter(SkillSubcategory.deleted_at.is_(None))
        .order_by(SkillSubcategory.subcategory_name)
        .all()
    )
    
    # Query 3: Get all skills sorted by name (exclude soft-deleted)
    skills_query = (
        db.query(Skill)
        .filter(Skill.deleted_at.is_(None))
        .order_by(Skill.skill_name)
    )
    
    # Apply search filter if provided
    if search_query:
        search_pattern = f"%{search_query}%"
        skills_query = skills_query.filter(Skill.skill_name.ilike(search_pattern))
    
    skills = skills_query.all()
    
    # Query 4: Get employee counts per skill in one grouped query
    # Count distinct employees per skill, excluding soft-deleted records
    employee_counts_query = (
        db.query(
            EmployeeSkill.skill_id,
            func.count(func.distinct(EmployeeSkill.employee_id)).label('count')
        )
        .filter(EmployeeSkill.deleted_at.is_(None))  # Exclude soft-deleted
        .group_by(EmployeeSkill.skill_id)
    )
    
    employee_counts: Dict[int, int] = {
        row.skill_id: row.count
        for row in employee_counts_query.all()
    }
    
    # Query 5: Get all aliases sorted by alias_text
    aliases = (
        db.query(SkillAlias)
        .order_by(SkillAlias.alias_text)
        .all()
    )
    
    # Build alias lookup: skill_id -> list of TaxonomyAliasDTO
    aliases_by_skill: Dict[int, List[TaxonomyAliasDTO]] = {}
    for alias in aliases:
        dto = TaxonomyAliasDTO(
            id=alias.alias_id,
            text=alias.alias_text,
            source=alias.source,
            confidence_score=alias.confidence_score,
        )
        if alias.skill_id not in aliases_by_skill:
            aliases_by_skill[alias.skill_id] = []
        aliases_by_skill[alias.skill_id].append(dto)
    
    # Build lookup maps for efficient hierarchy construction
    skills_by_subcategory: Dict[int, List[TaxonomySkillDTO]] = {}
    for skill in skills:
        dto = TaxonomySkillDTO(
            id=skill.skill_id,
            name=skill.skill_name,
            description=None,  # Skills table doesn't have description column
            employee_count=employee_counts.get(skill.skill_id, 0),
            created_at=skill.created_at,
            created_by=skill.created_by,
            aliases=aliases_by_skill.get(skill.skill_id, []),
        )
        if skill.subcategory_id not in skills_by_subcategory:
            skills_by_subcategory[skill.subcategory_id] = []
        skills_by_subcategory[skill.subcategory_id].append(dto)
    
    subcategories_by_category: Dict[int, List[TaxonomySubCategoryDTO]] = {}
    for subcat in subcategories:
        dto = TaxonomySubCategoryDTO(
            id=subcat.subcategory_id,
            name=subcat.subcategory_name,
            description=None,  # Subcategories table doesn't have description column
            created_at=subcat.created_at,
            created_by=subcat.created_by,
            skills=skills_by_subcategory.get(subcat.subcategory_id, []),
        )
        if subcat.category_id not in subcategories_by_category:
            subcategories_by_category[subcat.category_id] = []
        subcategories_by_category[subcat.category_id].append(dto)
    
    # Build final category list
    category_dtos: List[TaxonomyCategoryDTO] = []
    for cat in categories:
        dto = TaxonomyCategoryDTO(
            id=cat.category_id,
            name=cat.category_name,
            description=None,  # Categories table doesn't have description column
            created_at=cat.created_at,
            created_by=cat.created_by,
            subcategories=subcategories_by_category.get(cat.category_id, []),
        )
        category_dtos.append(dto)
    
    # If search was applied, filter out empty categories/subcategories
    if search_query:
        # Filter subcategories that have matching skills
        for cat_dto in category_dtos:
            cat_dto.subcategories = [
                subcat for subcat in cat_dto.subcategories
                if len(subcat.skills) > 0
            ]
        # Filter categories that have non-empty subcategories
        category_dtos = [
            cat for cat in category_dtos
            if len(cat.subcategories) > 0
        ]
    
    # Calculate totals
    total_subcategories = sum(len(cat.subcategories) for cat in category_dtos)
    total_skills = sum(
        len(subcat.skills)
        for cat in category_dtos
        for subcat in cat.subcategories
    )
    
    logger.info(
        f"Taxonomy fetched: {len(category_dtos)} categories, "
        f"{total_subcategories} subcategories, {total_skills} skills"
    )
    
    return SkillTaxonomyResponse(
        categories=category_dtos,
        total_categories=len(category_dtos),
        total_subcategories=total_subcategories,
        total_skills=total_skills,
    )
