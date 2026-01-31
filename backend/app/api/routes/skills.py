"""
API routes for skill data management and queries.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.db.session import get_db
from app.models import (
    Skill, SkillCategory, SkillSubcategory, EmployeeSkill, 
    Employee, ProficiencyLevel
)
from app.schemas.skill import (
    SkillResponse, SkillListResponse, SkillDetailResponse,
    SkillStatsResponse, CategoryResponse, SubcategoryResponse,
    CategoryInfo, SkillSummaryResponse, TaxonomyTreeResponse,
    TaxonomyCategoryItem, TaxonomySubcategoryItem, TaxonomySkillItem,
    CategoriesResponse, CategorySummaryItem,
    SubcategoriesResponse, SubcategorySummaryItem,
    SkillsResponse
)
from app.schemas.common import PaginationParams

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
    logger.info(f"Fetching skills with pagination: page={pagination.page}, size={pagination.size}")
    
    try:
        # Build query with joins
        query = db.query(Skill).options(
            joinedload(Skill.category),
            joinedload(Skill.subcategory)
        )
        
        # Apply filters
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
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        skills = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Build response data
        response_items = []
        for skill in skills:
            # Count employees with this skill
            employee_count = db.query(func.count(EmployeeSkill.employee_id.distinct())).filter(
                EmployeeSkill.skill_id == skill.skill_id
            ).scalar()
            
            skill_data = SkillResponse(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                category=CategoryInfo(
                    category_id=skill.category.category_id,
                    category_name=skill.category.category_name,
                    subcategory_id=skill.subcategory.subcategory_id if skill.subcategory else None,
                    subcategory_name=skill.subcategory.subcategory_name if skill.subcategory else None
                ),
                employee_count=employee_count
            )
            response_items.append(skill_data)
        
        return SkillListResponse.create(response_items, total, pagination)
        
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
    logger.info(f"Fetching skill details for ID: {skill_id}")
    
    try:
        skill = db.query(Skill).options(
            joinedload(Skill.category),
            joinedload(Skill.subcategory)
        ).filter(Skill.skill_id == skill_id).first()
        
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID {skill_id} not found"
            )
        
        # Get proficiency distribution
        proficiency_dist = dict(
            db.query(ProficiencyLevel.level_name, func.count(EmployeeSkill.emp_skill_id))
            .join(EmployeeSkill)
            .filter(EmployeeSkill.skill_id == skill_id)
            .group_by(ProficiencyLevel.level_name)
            .all()
        )
        
        # Get averages
        avg_experience = db.query(func.avg(EmployeeSkill.years_experience)).filter(
            EmployeeSkill.skill_id == skill_id,
            EmployeeSkill.years_experience.isnot(None)
        ).scalar()
        
        avg_interest = db.query(func.avg(EmployeeSkill.interest_level)).filter(
            EmployeeSkill.skill_id == skill_id,
            EmployeeSkill.interest_level.isnot(None)
        ).scalar()
        
        # Count unique employees
        employee_count = db.query(func.count(EmployeeSkill.employee_id.distinct())).filter(
            EmployeeSkill.skill_id == skill_id
        ).scalar()
        
        return SkillDetailResponse(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            category=CategoryInfo(
                category_id=skill.category.category_id,
                category_name=skill.category.category_name,
                subcategory_id=skill.subcategory.subcategory_id if skill.subcategory else None,
                subcategory_name=skill.subcategory.subcategory_name if skill.subcategory else None
            ),
            employee_count=employee_count,
            proficiency_distribution=proficiency_dist,
            avg_years_experience=round(avg_experience, 2) if avg_experience else None,
            avg_interest_level=round(avg_interest, 2) if avg_interest else None
        )
        
    except HTTPException:
        raise
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
    logger.info("Fetching skill statistics")
    
    try:
        # Total skills
        total_skills = db.query(func.count(Skill.skill_id)).scalar()
        
        # Count by category
        by_category = dict(
            db.query(SkillCategory.category_name, func.count(Skill.skill_id))
            .join(Skill)
            .group_by(SkillCategory.category_name)
            .all()
        )
        
        # Count by subcategory  
        by_subcategory = dict(
            db.query(SkillSubcategory.subcategory_name, func.count(Skill.skill_id))
            .join(Skill)
            .group_by(SkillSubcategory.subcategory_name)
            .all()
        )
        
        # Most popular skills (top 10 by employee count)
        most_popular_skills = [
            {"skill_name": skill_name, "employee_count": count}
            for skill_name, count in 
            db.query(Skill.skill_name, func.count(EmployeeSkill.employee_id.distinct()))
            .join(EmployeeSkill)
            .group_by(Skill.skill_name)
            .order_by(desc(func.count(EmployeeSkill.employee_id.distinct())))
            .limit(10)
            .all()
        ]
        
        return SkillStatsResponse(
            total_skills=total_skills,
            by_category=by_category,
            by_subcategory=by_subcategory,
            most_popular_skills=most_popular_skills
        )
        
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
    logger.info("Fetching skill categories")
    
    try:
        categories = db.query(SkillCategory).all()
        
        response_items = []
        for category in categories:
            # Count skills and subcategories
            skill_count = db.query(func.count(Skill.skill_id)).filter(
                Skill.category_id == category.category_id
            ).scalar()
            
            subcategory_count = db.query(func.count(SkillSubcategory.subcategory_id)).filter(
                SkillSubcategory.category_id == category.category_id
            ).scalar()
            
            category_data = CategoryResponse(
                category_id=category.category_id,
                category_name=category.category_name,
                skill_count=skill_count,
                subcategory_count=subcategory_count
            )
            response_items.append(category_data)
        
        return response_items
        
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
    logger.info("Fetching skill subcategories")
    
    try:
        query = db.query(SkillSubcategory).options(
            joinedload(SkillSubcategory.category)
        )
        
        if category:
            query = query.join(SkillCategory).filter(
                SkillCategory.category_name.ilike(f"%{category}%")
            )
        
        subcategories = query.all()
        
        response_items = []
        for subcategory in subcategories:
            # Count skills in this subcategory
            skill_count = db.query(func.count(Skill.skill_id)).filter(
                Skill.subcategory_id == subcategory.subcategory_id
            ).scalar()
            
            subcategory_data = SubcategoryResponse(
                subcategory_id=subcategory.subcategory_id,
                subcategory_name=subcategory.subcategory_name,
                category_name=subcategory.category.category_name,
                skill_count=skill_count
            )
            response_items.append(subcategory_data)
        
        return response_items
        
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
    logger.info("Fetching complete skill taxonomy tree")
    
    try:
        # Get ALL categories (no filtering)
        categories = db.query(SkillCategory)\
            .order_by(SkillCategory.category_name)\
            .all()
        
        logger.info(f"Found {len(categories)} categories in database")
        
        taxonomy_categories = []
        
        for category in categories:
            # Get all subcategories for this category
            subcategories = db.query(SkillSubcategory)\
                .filter(SkillSubcategory.category_id == category.category_id)\
                .order_by(SkillSubcategory.subcategory_name)\
                .all()
            
            taxonomy_subcategories = []
            
            for subcategory in subcategories:
                # Get all skills for this subcategory
                skills = db.query(Skill)\
                    .filter(
                        Skill.category_id == category.category_id,
                        Skill.subcategory_id == subcategory.subcategory_id
                    )\
                    .order_by(Skill.skill_name)\
                    .all()
                
                # Build skill items with real database IDs
                taxonomy_skills = [
                    TaxonomySkillItem(
                        skill_id=skill.skill_id,
                        skill_name=skill.skill_name
                    )
                    for skill in skills
                ]
                
                taxonomy_subcategories.append(
                    TaxonomySubcategoryItem(
                        subcategory_id=subcategory.subcategory_id,
                        subcategory_name=subcategory.subcategory_name,
                        skills=taxonomy_skills
                    )
                )
            
            # Add category even if it has no subcategories (empty list is ok)
            taxonomy_categories.append(
                TaxonomyCategoryItem(
                    category_id=category.category_id,
                    category_name=category.category_name,
                    subcategories=taxonomy_subcategories
                )
            )
        
        logger.info(
            f"Taxonomy tree built: {len(taxonomy_categories)} categories, "
            f"{sum(len(c.subcategories) for c in taxonomy_categories)} subcategories total"
        )
        
        return TaxonomyTreeResponse(categories=taxonomy_categories)
        
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
    Get summary statistics for a specific skill, aggregating across all related skills with similar names.
    
    For example, if the skill is "ReactJS", this will find all skills matching "react" 
    (ReactJS, React, React.js, etc.) and aggregate employee counts across them.
    
    Returns:
        - skill_id: The primary skill identifier
        - skill_name: The primary skill name
        - employee_count: Number of distinct employees who have ANY matching skill
        - employee_ids: List of employee IDs with this skill (for "View All" functionality)
        - avg_experience_years: Average years of experience (rounded to 1 decimal)
        - certified_count: Number of distinct certified employees (backward compatibility)
        - certified_employee_count: Number of distinct certified employees
    
    Raises:
        - 404: If skill not found
        - 200: With zeros if skill exists but no employees have it
    """
    logger.info(f"Fetching summary for skill_id: {skill_id}")
    
    try:
        # Check if primary skill exists
        skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
        if not skill:
            logger.warning(f"Skill not found: {skill_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID {skill_id} not found"
            )
        
        # Extract the core skill name for matching (e.g., "ReactJS" -> "react")
        # This will match ReactJS, React, React.js, etc.
        skill_name_pattern = skill.skill_name.lower()
        
        # Find all related skill IDs with similar names
        related_skills = db.query(Skill.skill_id)\
            .filter(Skill.skill_name.ilike(f"%{skill_name_pattern}%"))\
            .all()
        
        related_skill_ids = [s.skill_id for s in related_skills]
        
        logger.info(f"Found {len(related_skill_ids)} related skills for '{skill.skill_name}': {related_skill_ids}")
        
        # Get distinct employee count across all related skills
        employee_count_query = db.query(func.count(EmployeeSkill.employee_id.distinct()))\
            .filter(EmployeeSkill.skill_id.in_(related_skill_ids))
        
        employee_count = employee_count_query.scalar() or 0
        
        # Get list of employee IDs (for "View All" functionality)
        employee_ids_query = db.query(EmployeeSkill.employee_id.distinct())\
            .filter(EmployeeSkill.skill_id.in_(related_skill_ids))\
            .order_by(EmployeeSkill.employee_id)
        
        employee_ids = [row[0] for row in employee_ids_query.all()]
        
        # Get average years of experience (ignore nulls, across all related skills)
        avg_experience = db.query(func.avg(EmployeeSkill.years_experience))\
            .filter(
                EmployeeSkill.skill_id.in_(related_skill_ids),
                EmployeeSkill.years_experience.isnot(None),
                EmployeeSkill.years_experience > 0
            )\
            .scalar()
        
        avg_experience_years = round(float(avg_experience), 1) if avg_experience else 0.0
        
        # Get certified employee count using proper business rules:
        # - Exclude NULL, empty string, and "no" (case-insensitive)
        # - Count distinct employees (not rows)
        certified_employee_count = db.query(func.count(EmployeeSkill.employee_id.distinct()))\
            .filter(
                EmployeeSkill.skill_id.in_(related_skill_ids),
                EmployeeSkill.certification.isnot(None),
                func.nullif(func.trim(EmployeeSkill.certification), '') != None,
                func.lower(func.trim(EmployeeSkill.certification)) != 'no'
            )\
            .scalar() or 0
        
        logger.info(
            f"Skill summary for {skill.skill_name} (ID: {skill_id}, {len(related_skill_ids)} related): "
            f"employees={employee_count} (IDs: {len(employee_ids)}), "
            f"avg_exp={avg_experience_years}y, certified={certified_employee_count}"
        )
        
        return SkillSummaryResponse(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            employee_count=employee_count,
            employee_ids=employee_ids,
            avg_experience_years=avg_experience_years,
            certified_count=certified_employee_count,  # Backward compatibility
            certified_employee_count=certified_employee_count
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error fetching skill summary for skill_id {skill_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill summary"
        )


# === Lazy-loading Taxonomy Endpoints ===

@router.get("/capability/categories", response_model=CategoriesResponse)
async def get_categories(db: Session = Depends(get_db)):
    """
    Get lightweight list of all categories with counts only.
    Used for initial page load to minimize data transfer.
    
    Returns:
        List of categories with subcategory_count and skill_count for each.
    """
    logger.info("Fetching categories with counts for lazy loading")
    
    try:
        # Get all categories with counts
        categories = db.query(SkillCategory)\
            .order_by(SkillCategory.category_name)\
            .all()
        
        category_items = []
        
        for category in categories:
            # Count subcategories
            subcategory_count = db.query(func.count(SkillSubcategory.subcategory_id))\
                .filter(SkillSubcategory.category_id == category.category_id)\
                .scalar() or 0
            
            # Count skills in this category
            skill_count = db.query(func.count(Skill.skill_id))\
                .filter(Skill.category_id == category.category_id)\
                .scalar() or 0
            
            category_items.append(CategorySummaryItem(
                category_id=category.category_id,
                category_name=category.category_name,
                subcategory_count=subcategory_count,
                skill_count=skill_count
            ))
        
        logger.info(f"Returning {len(category_items)} categories")
        return CategoriesResponse(categories=category_items)
        
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
    logger.info(f"Fetching subcategories for category {category_id}")
    
    try:
        # Verify category exists
        category = db.query(SkillCategory)\
            .filter(SkillCategory.category_id == category_id)\
            .first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found"
            )
        
        # Get subcategories with skill counts
        subcategories = db.query(SkillSubcategory)\
            .filter(SkillSubcategory.category_id == category_id)\
            .order_by(SkillSubcategory.subcategory_name)\
            .all()
        
        subcategory_items = []
        
        for subcategory in subcategories:
            # Count skills in this subcategory
            skill_count = db.query(func.count(Skill.skill_id))\
                .filter(
                    Skill.category_id == category_id,
                    Skill.subcategory_id == subcategory.subcategory_id
                )\
                .scalar() or 0
            
            subcategory_items.append(SubcategorySummaryItem(
                subcategory_id=subcategory.subcategory_id,
                subcategory_name=subcategory.subcategory_name,
                skill_count=skill_count
            ))
        
        logger.info(f"Returning {len(subcategory_items)} subcategories for category {category_id}")
        return SubcategoriesResponse(
            category_id=category.category_id,
            category_name=category.category_name,
            subcategories=subcategory_items
        )
        
    except HTTPException:
        raise
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
    logger.info(f"Fetching skills for subcategory {subcategory_id}")
    
    try:
        # Verify subcategory exists and get category info
        subcategory = db.query(SkillSubcategory)\
            .filter(SkillSubcategory.subcategory_id == subcategory_id)\
            .first()
        
        if not subcategory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subcategory {subcategory_id} not found"
            )
        
        # Get category info
        category = db.query(SkillCategory)\
            .filter(SkillCategory.category_id == subcategory.category_id)\
            .first()
        
        # Get skills
        skills = db.query(Skill)\
            .filter(
                Skill.category_id == subcategory.category_id,
                Skill.subcategory_id == subcategory_id
            )\
            .order_by(Skill.skill_name)\
            .all()
        
        skill_items = [
            TaxonomySkillItem(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name
            )
            for skill in skills
        ]
        
        logger.info(f"Returning {len(skill_items)} skills for subcategory {subcategory_id}")
        return SkillsResponse(
            subcategory_id=subcategory.subcategory_id,
            subcategory_name=subcategory.subcategory_name,
            category_id=category.category_id,
            category_name=category.category_name,
            skills=skill_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skills for subcategory {subcategory_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skills"
        )

