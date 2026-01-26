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
    CategoryInfo
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
