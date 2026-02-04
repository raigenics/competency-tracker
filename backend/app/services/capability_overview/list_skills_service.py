"""
List Skills Service - GET /skills

Handles paginated skill listing with optional filters.
Zero dependencies on other services.
"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Skill, SkillCategory, SkillSubcategory, EmployeeSkill
from app.schemas.skill import SkillResponse, CategoryInfo
from app.schemas.common import PaginationParams

logger = logging.getLogger(__name__)


def get_skills_paginated(
    db: Session,
    pagination: PaginationParams,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None
) -> Tuple[List[SkillResponse], int]:
    """
    Get paginated list of skills with optional filters.
    
    Args:
        db: Database session
        pagination: Pagination parameters (page, size, offset)
        category: Optional category name filter (case-insensitive partial match)
        subcategory: Optional subcategory name filter (case-insensitive partial match)
        search: Optional skill name search (case-insensitive partial match)
    
    Returns:
        Tuple of (skill_responses, total_count)
    """
    logger.info(f"Fetching skills: page={pagination.page}, size={pagination.size}, "
                f"category={category}, subcategory={subcategory}, search={search}")
    
    # Query skills with category/subcategory relationships
    query_results = _query_skills_with_filters(db, category, subcategory, search)
    
    # Get total count
    total = _count_skills(query_results)
    
    # Apply pagination and fetch
    skills = _paginate_and_fetch(query_results, pagination)
    
    # Build response with employee counts
    response_items = _build_skill_responses(db, skills)
    
    logger.info(f"Returning {len(response_items)} skills (total: {total})")
    return response_items, total


# === DATABASE QUERIES ===

def _query_skills_with_filters(
    db: Session,
    category: Optional[str],
    subcategory: Optional[str],
    search: Optional[str]
):
    """
    Build and return filtered skill query with eager loading.
    Does NOT execute the query - returns query object for counting/pagination.
    """
    query = db.query(Skill).options(
        joinedload(Skill.subcategory).joinedload(SkillSubcategory.category)
    )
    
    if category:
        query = query.join(SkillCategory).filter(
            SkillCategory.category_name.ilike(f"%{category}%")
        )
    
    if subcategory:
        query = query.join(SkillSubcategory).filter(
            SkillSubcategory.subcategory_name.ilike(f"%{subcategory}%")
        )
    
    if search:
        query = query.filter(Skill.skill_name.ilike(f"%{search}%"))
    
    return query


def _count_skills(query) -> int:
    """Count total skills in query (before pagination)."""
    return query.count()


def _paginate_and_fetch(query, pagination: PaginationParams) -> List[Skill]:
    """Apply pagination and execute query."""
    return query.offset(pagination.offset).limit(pagination.size).all()


def _get_employee_count_for_skill(db: Session, skill_id: int) -> int:
    """Count distinct employees with a specific skill."""
    return db.query(func.count(EmployeeSkill.employee_id.distinct())).filter(
        EmployeeSkill.skill_id == skill_id
    ).scalar() or 0


# === RESPONSE BUILDING ===

def _build_skill_responses(db: Session, skills: List[Skill]) -> List[SkillResponse]:
    """
    Transform Skill models to SkillResponse schemas with employee counts.
    Pure transformation logic (except for employee count query).
    """
    response_items = []
    
    for skill in skills:
        employee_count = _get_employee_count_for_skill(db, skill.skill_id)
        
        skill_data = SkillResponse(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            category=_build_category_info(skill),
            employee_count=employee_count
        )
        response_items.append(skill_data)
    
    return response_items


def _build_category_info(skill: Skill) -> CategoryInfo:
    """
    Build CategoryInfo from skill's relationships.
    Pure function - no DB access.
    """
    return CategoryInfo(
        category_id=skill.category.category_id,
        category_name=skill.category.category_name,
        subcategory_id=skill.subcategory.subcategory_id if skill.subcategory else None,
        subcategory_name=skill.subcategory.subcategory_name if skill.subcategory else None
    )
