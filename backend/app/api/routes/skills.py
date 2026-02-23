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
    SkillSummaryResponse, TaxonomyTreeResponse,
    CategoriesResponse, SubcategoriesResponse,
    SkillsResponse, SkillSearchResponse,
    CapabilityKPIsResponse, CategoryCoverageResponse,
    SkillCapabilitySnapshotResponse, SkillProficiencyBreakdownResponse,
    SkillLeadingSubSegmentResponse, SkillEmployeesSummaryResponse,
    SkillEmployeesListResponse
)
from app.schemas.common import PaginationParams

# Import isolated service modules
from app.services.capability_overview import list_skills_service
from app.services.capability_overview import skill_detail_service
from app.services.capability_overview import taxonomy_tree_service
from app.services.capability_overview import skill_summary_service
from app.services.capability_overview import taxonomy_categories_service
from app.services.capability_overview import taxonomy_subcategories_service
from app.services.capability_overview import taxonomy_skills_service
from app.services.capability_overview import taxonomy_search_service
from app.services.capability_overview import kpi_service
from app.services.capability_overview import category_coverage_service
from app.services.capability_overview import skill_capability_snapshot_service
from app.services.capability_overview import skill_proficiency_breakdown_service
from app.services.capability_overview import skill_leading_subsegment_service
from app.services.capability_overview import skill_employees_summary_service
from app.services.capability_overview import skill_employees_list_service

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


@router.get("/capability-kpis", response_model=CapabilityKPIsResponse)
async def get_capability_kpis(db: Session = Depends(get_db)):
    """
    Get KPI metrics for the Capability Overview page.
    
    Returns:
        - total_skills: Skills with at least one mapped employee
        - avg_proficiency: Average proficiency level across mapped employees
        - total_certifications: Count of certifications within the current scope
    """
    logger.info("GET /skills/capability-kpis")
    
    try:
        return kpi_service.get_capability_kpis(db)
        
    except Exception as e:
        logger.error(f"Error fetching capability KPIs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching capability KPIs"
        )


@router.get("/category-coverage", response_model=CategoryCoverageResponse)
async def get_category_coverage(db: Session = Depends(get_db)):
    """
    Get employee concentration by skill category.
    
    Returns:
        - most_populated_category: Category with highest employee concentration
        - least_populated_category: Category with lowest non-zero employee concentration
    """
    logger.info("GET /skills/category-coverage")
    
    try:
        return category_coverage_service.get_category_coverage(db)
        
    except Exception as e:
        logger.error(f"Error fetching category coverage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching category coverage"
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


@router.get("/{skill_id}/capability-snapshot", response_model=SkillCapabilitySnapshotResponse)
async def get_skill_capability_snapshot(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get capability snapshot KPIs for a specific skill.
    
    Returns:
        - employee_count: Employees mapped to this skill
        - certified_count: Employees with a certification tagged to this skill
        - team_count: Distinct teams with employees having this skill
    """
    logger.info(f"GET /skills/{skill_id}/capability-snapshot")
    
    try:
        return skill_capability_snapshot_service.get_skill_capability_snapshot(db, skill_id)
        
    except Exception as e:
        logger.error(f"Error fetching capability snapshot for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching capability snapshot"
        )


@router.get("/{skill_id}/proficiency-breakdown", response_model=SkillProficiencyBreakdownResponse)
async def get_skill_proficiency_breakdown(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get proficiency breakdown for a specific skill.
    
    Returns:
        - counts: Dict of proficiency level names (Novice, Adv. Beginner, Competent, Proficient, Expert) to counts
        - avg: Average proficiency value (1-5) rounded to 1 decimal
        - median: Median proficiency value (1-5)
        - total: Total employees with proficiency data
    """
    logger.info(f"GET /skills/{skill_id}/proficiency-breakdown")
    
    try:
        return skill_proficiency_breakdown_service.get_skill_proficiency_breakdown(db, skill_id)
        
    except Exception as e:
        logger.error(f"Error fetching proficiency breakdown for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching proficiency breakdown"
        )


@router.get("/{skill_id}/leading-subsegment", response_model=SkillLeadingSubSegmentResponse)
async def get_skill_leading_subsegment(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the leading sub-segment for a specific skill.
    
    Leading sub-segment = the sub-segment with the highest number of 
    distinct employees mapped to this skill.
    
    Returns:
        - leading_sub_segment_name: Name of the leading sub-segment (or null if no data)
        - leading_sub_segment_employee_count: Count of distinct employees in that sub-segment
    """
    logger.info(f"GET /skills/{skill_id}/leading-subsegment")
    
    try:
        return skill_leading_subsegment_service.get_skill_leading_subsegment(db, skill_id)
        
    except Exception as e:
        logger.error(f"Error fetching leading subsegment for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching leading sub-segment"
        )


@router.get("/{skill_id}/employees/summary", response_model=SkillEmployeesSummaryResponse)
async def get_skill_employees_summary(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get aggregated summary statistics for employees with a specific skill.
    Used for View Employees header KPIs.
    
    Returns:
        - employee_count: Count of distinct employees with this skill
        - avg_proficiency: Average proficiency value (1-5) rounded to 1 decimal
        - certified_count: Count of employees with certification for this skill
        - team_count: Count of distinct teams with employees having this skill
    """
    logger.info(f"GET /skills/{skill_id}/employees/summary")
    
    try:
        return skill_employees_summary_service.get_skill_employees_summary(db, skill_id)
        
    except Exception as e:
        logger.error(f"Error fetching employees summary for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employees summary"
        )


@router.get("/{skill_id}/employees", response_model=SkillEmployeesListResponse)
async def get_skill_employees_list(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed list of employees with a specific skill.
    Used for the View Employees table.
    
    Returns:
        - skill_id: The queried skill ID
        - skill_name: The skill name
        - employees: List of employees with proficiency, certification, and last updated info
        - total_count: Total number of employees
    """
    logger.info(f"GET /skills/{skill_id}/employees")
    
    try:
        return skill_employees_list_service.get_skill_employees_list(db, skill_id)
        
    except ValueError as e:
        logger.warning(f"Skill not found: skill_id {skill_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching employees list for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employees list"
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

