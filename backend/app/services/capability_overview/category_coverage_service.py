"""
Category Coverage Service - GET /skills/category-coverage

Provides employee concentration metrics per skill category:
- Most populated category (highest employee count)
- Least populated category (lowest non-zero employee count)

All metrics are scoped to employees in non-deleted sub-segments.
"""
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    EmployeeSkill, Employee, Team, Project, SubSegment,
    Skill, SkillSubcategory, SkillCategory
)
from app.schemas.skill import CategoryCoverageResponse, CategoryCoverageItem

logger = logging.getLogger(__name__)


def get_category_coverage(db: Session) -> CategoryCoverageResponse:
    """
    Get employee concentration by skill category.
    
    Scope: All employees in non-deleted sub-segments.
    
    Returns:
        CategoryCoverageResponse with most_populated and least_populated categories
    """
    logger.info("Fetching category coverage")
    
    # Query employee count per category
    category_counts = _query_employee_count_by_category(db)
    
    # Find most and least populated
    most_populated = None
    least_populated = None
    
    if category_counts:
        # Sort by employee count descending
        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1]['employee_count'],
            reverse=True
        )
        
        # Most populated = first (highest count)
        if sorted_categories:
            cat_id, data = sorted_categories[0]
            most_populated = CategoryCoverageItem(
                category_id=cat_id,
                category_name=data['category_name'],
                employee_count=data['employee_count']
            )
        
        # Least populated = last with non-zero count
        non_zero = [item for item in sorted_categories if item[1]['employee_count'] > 0]
        if non_zero:
            cat_id, data = non_zero[-1]
            least_populated = CategoryCoverageItem(
                category_id=cat_id,
                category_name=data['category_name'],
                employee_count=data['employee_count']
            )
    
    logger.info(
        f"Category coverage: most={most_populated.category_name if most_populated else None}, "
        f"least={least_populated.category_name if least_populated else None}"
    )
    
    return CategoryCoverageResponse(
        most_populated_category=most_populated,
        least_populated_category=least_populated
    )


def _query_employee_count_by_category(db: Session) -> Dict[int, Dict]:
    """
    Query distinct employee count grouped by skill category.
    
    Join path: EmployeeSkill → Skill → SkillSubcategory → SkillCategory
    Filter: Non-deleted employees in non-deleted sub-segments
    
    Returns:
        Dict of {category_id: {category_name, employee_count}}
    """
    # Subquery for scoped employee IDs (non-deleted, in non-deleted sub-segments)
    scoped_employees = (
        db.query(Employee.employee_id)
        .join(Team, Employee.team_id == Team.team_id)
        .join(Project, Team.project_id == Project.project_id)
        .join(SubSegment, Project.sub_segment_id == SubSegment.sub_segment_id)
        .filter(
            Employee.deleted_at.is_(None),
            Team.deleted_at.is_(None),
            Project.deleted_at.is_(None),
            SubSegment.deleted_at.is_(None)
        )
        .subquery()
    )
    
    # Query employee count per category
    results = (
        db.query(
            SkillCategory.category_id,
            SkillCategory.category_name,
            func.count(func.distinct(EmployeeSkill.employee_id)).label('employee_count')
        )
        .join(SkillSubcategory, SkillCategory.category_id == SkillSubcategory.category_id)
        .join(Skill, SkillSubcategory.subcategory_id == Skill.subcategory_id)
        .join(EmployeeSkill, Skill.skill_id == EmployeeSkill.skill_id)
        .filter(
            EmployeeSkill.employee_id.in_(
                db.query(scoped_employees.c.employee_id)
            ),
            EmployeeSkill.deleted_at.is_(None),
            Skill.deleted_at.is_(None)
        )
        .group_by(SkillCategory.category_id, SkillCategory.category_name)
        .all()
    )
    
    return {
        row.category_id: {
            'category_name': row.category_name,
            'employee_count': row.employee_count
        }
        for row in results
    }
