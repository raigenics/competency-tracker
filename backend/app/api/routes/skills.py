"""
API routes for skill data management and queries.

Refactored for Clean Code, SRP, and testability.
All business logic extracted to isolated service modules.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.skill import (
    SkillListResponse, SkillDetailResponse,
    SkillStatsResponse, CategoryResponse, SubcategoryResponse,
    SkillSummaryResponse, TaxonomyTreeResponse,
    CategoriesResponse, SubcategoriesResponse,
    SkillsResponse, SkillSearchResponse
)
from app.schemas.common import PaginationParams

# Import isolated service modules
from app.services.capability_overview import list_skills_service
from app.services.capability_overview import skill_detail_service
from app.services.capability_overview import skill_stats_service
from app.services.capability_overview import categories_service
from app.services.capability_overview import subcategories_service
from app.services.capability_overview import taxonomy_tree_service
from app.services.capability_overview import skill_summary_service
from app.services.capability_overview import taxonomy_categories_service
from app.services.capability_overview import taxonomy_subcategories_service
from app.services.capability_overview import taxonomy_skills_service
from app.services.capability_overview import taxonomy_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/", response_model=SkillListResponse)
async def get_skills(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(None, description="Filter by category name"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory name"),
    search: Optional[str] = Query(None, description="Search in skill name"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of skills with optional filters.
    """
    logger.info(f"GET /skills - page={pagination.page}, size={pagination.size}")
    
    try:
        skills, total = list_skills_service.get_skills_paginated(
            db, pagination, category, subcategory, search
        )
        return SkillListResponse.create(skills, total, pagination)
        
    except Exception as e:
        logger.error(f"Error fetching skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skills"
        )


@router.get("/{skill_id}", response_model=SkillDetailResponse)
async def get_skill(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific skill including proficiency distribution.
    """
    logger.info(f"GET /skills/{skill_id}")
    
    try:
        return skill_detail_service.get_skill_detail(db, skill_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching skill {skill_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill details"
        )


@router.get("/stats/overview", response_model=SkillStatsResponse)
async def get_skill_stats(db: Session = Depends(get_db)):
    """
    Get skill statistics and overview.
    """
    logger.info("GET /skills/stats/overview")
    
    try:
        return skill_stats_service.get_skill_stats(db)
        
    except Exception as e:
        logger.error(f"Error fetching skill stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill statistics"
        )


@router.get("/categories/", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """
    Get all skill categories with counts.
    """
    logger.info("GET /skills/categories/")
    
    try:
        return categories_service.get_categories(db)
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching categories"
        )


@router.get("/subcategories/", response_model=List[SubcategoryResponse])
async def get_subcategories(
    category: Optional[str] = Query(None, description="Filter by category name"),
    db: Session = Depends(get_db)
):
    """
    Get all skill subcategories with optional category filter.
    """
    logger.info(f"GET /skills/subcategories/ - category={category}")
    
    try:
        return subcategories_service.get_subcategories(db, category)
        
    except Exception as e:
        logger.error(f"Error fetching subcategories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching subcategories"
        )


@router.get("/taxonomy/tree", response_model=TaxonomyTreeResponse)
async def get_taxonomy_tree(db: Session = Depends(get_db)):
    """
    Get complete skill taxonomy tree with all categories, subcategories, and skills.
    Returns ALL categories from the database, even if they have no subcategories or skills.
    
    Returns:
        Complete nested structure:
        - categories: All categories from skill_categories table
          - subcategories: All subcategories for each category
            - skills: All skills for each subcategory
    """
    logger.info("GET /skills/taxonomy/tree")
    
    try:
        return taxonomy_tree_service.get_taxonomy_tree(db)
        
    except Exception as e:
        logger.error(f"Error fetching taxonomy tree: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill taxonomy tree"
        )


@router.get("/{skill_id}/summary", response_model=SkillSummaryResponse)
async def get_skill_summary(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for a specific skill using EXACT skill_id match.
    
    Returns employees who have THIS SPECIFIC SKILL only, not related skills with similar names.
    For example, clicking "React" returns only employees with React, NOT ReactJS or React.js.
    
    Returns:
        - skill_id: The skill identifier
        - skill_name: The skill name
        - employee_count: Number of distinct employees with this exact skill_id
        - employee_ids: List of employee IDs with this skill (for "View All" functionality)
        - avg_experience_years: Average years of experience (rounded to 1 decimal)
        - certified_count: Number of distinct certified employees (backward compatibility)
        - certified_employee_count: Number of distinct certified employees
    
    Raises:
        - 404: If skill not found
        - 200: With zeros if skill exists but no employees have it
    """
    logger.info(f"GET /skills/{skill_id}/summary")
    
    try:
        return skill_summary_service.get_skill_summary(db, skill_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching skill summary for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill summary"
        )


# === Lazy-loading Taxonomy Endpoints ===

@router.get("/capability/categories", response_model=CategoriesResponse)
async def get_categories_for_lazy_loading(db: Session = Depends(get_db)):
    """
    Get lightweight list of all categories with counts only.
    Used for initial page load to minimize data transfer.
    
    Returns:
        List of categories with subcategory_count and skill_count for each.
    """
    logger.info("GET /skills/capability/categories")
    
    try:
        return taxonomy_categories_service.get_categories_for_lazy_loading(db)
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching categories"
        )


@router.get("/capability/categories/{category_id}/subcategories", response_model=SubcategoriesResponse)
async def get_subcategories_for_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get subcategories for a specific category with skill counts.
    Used when user expands a category node.
    
    Args:
        category_id: The category ID to fetch subcategories for
        
    Returns:
        List of subcategories with skill_count for each.
    """
    logger.info(f"GET /skills/capability/categories/{category_id}/subcategories")
    
    try:
        return taxonomy_subcategories_service.get_subcategories_for_category(db, category_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching subcategories for category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching subcategories"
        )


@router.get("/capability/subcategories/{subcategory_id}/skills", response_model=SkillsResponse)
async def get_skills_for_subcategory(
    subcategory_id: int,
    db: Session = Depends(get_db)
):
    """
    Get skills for a specific subcategory.
    Used when user expands a subcategory node.
    
    Args:
        subcategory_id: The subcategory ID to fetch skills for
        
    Returns:
        List of skills in the subcategory.
    """
    logger.info(f"GET /skills/capability/subcategories/{subcategory_id}/skills")
    
    try:
        return taxonomy_skills_service.get_skills_for_subcategory(db, subcategory_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching skills for subcategory {subcategory_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skills"
        )


@router.get("/capability/search", response_model=SkillSearchResponse)
async def search_skills_in_taxonomy(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    db: Session = Depends(get_db)
):
    """
    Search for skills by name across the entire taxonomy.
    Returns matching skills with their full hierarchy path (category → subcategory → skill).
    
    This endpoint enables instant search without requiring the tree to be expanded first.
    Minimum 2 characters required for search query.
    
    Query is case-insensitive and matches partial skill names.
    """
    logger.info(f"GET /skills/capability/search?q={q}")
    
    try:
        return taxonomy_search_service.search_skills_in_taxonomy(db, q)
        
    except Exception as e:
        logger.error(f"Error searching skills with query '{q}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching skills"
        )

