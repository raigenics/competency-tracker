"""
Employee Skills Service

Handles bulk saving of employee skills using transactional replace-all strategy.
Deletes existing skills and inserts new ones atomically.

SRP: This service only handles employee skills CRUD operations.
"""
import logging
from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.employee import Employee
from app.models.skill import Skill
from app.models.employee_skill import EmployeeSkill
from app.models.proficiency import ProficiencyLevel
from app.schemas.employee import EmployeeSkillItem

logger = logging.getLogger(__name__)

# Mapping from frontend proficiency string to database level name
PROFICIENCY_MAP = {
    'NOVICE': 'Novice',
    'ADVANCED_BEGINNER': 'Advanced Beginner',
    'COMPETENT': 'Competent',
    'PROFICIENT': 'Proficient',
    'EXPERT': 'Expert'
}


def _parse_last_used_date(month: Optional[str], year: Optional[str]) -> Optional[date]:
    """
    Parse month and year strings into a date object.
    Uses first day of the month.
    
    Args:
        month: Month string (01-12)
        year: Year string (YY or YYYY)
        
    Returns:
        date object or None if both are empty
    """
    if not month and not year:
        return None
    
    # Default month to January if not provided
    month_int = int(month) if month else 1
    
    # Parse year, handling 2-digit years
    if year:
        year_int = int(year)
        if year_int < 100:
            # Assume 20XX for 2-digit years
            year_int = 2000 + year_int
    else:
        # Default to current year if not provided
        from datetime import datetime
        year_int = datetime.now().year
    
    try:
        return date(year_int, month_int, 1)
    except ValueError as e:
        logger.warning(f"Invalid date: year={year_int}, month={month_int}: {e}")
        return None


def _get_proficiency_level_id(db: Session, proficiency_name: str) -> int:
    """
    Get proficiency level ID from name.
    
    Args:
        db: Database session
        proficiency_name: Proficiency name (e.g., 'NOVICE', 'EXPERT')
        
    Returns:
        Proficiency level ID
        
    Raises:
        HTTPException: If proficiency level not found
    """
    # Map frontend value to database value
    db_name = PROFICIENCY_MAP.get(proficiency_name.upper())
    if not db_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid proficiency level: {proficiency_name}. Valid values: {list(PROFICIENCY_MAP.keys())}"
        )
    
    level = db.query(ProficiencyLevel).filter(
        ProficiencyLevel.level_name == db_name
    ).first()
    
    if not level:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Proficiency level not found: {db_name}"
        )
    
    return level.proficiency_level_id


def validate_employee_exists(db: Session, employee_id: int) -> Employee:
    """
    Validate that employee exists.
    
    Args:
        db: Database session
        employee_id: Employee ID
        
    Returns:
        Employee object
        
    Raises:
        HTTPException: If employee not found
    """
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {employee_id}"
        )
    
    return employee


def validate_skills_exist(db: Session, skill_ids: List[int]) -> None:
    """
    Validate that all skill IDs exist in the approved skills list.
    
    Args:
        db: Database session
        skill_ids: List of skill IDs to validate
        
    Raises:
        HTTPException: If any skill not found
    """
    if not skill_ids:
        return
    
    existing_ids = {
        row[0] for row in 
        db.query(Skill.skill_id).filter(Skill.skill_id.in_(skill_ids)).all()
    }
    
    missing_ids = set(skill_ids) - existing_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid skill_id(s): {list(missing_ids)}. Skills must be from approved list."
        )


def save_employee_skills(
    db: Session,
    employee_id: int,
    skills: List[EmployeeSkillItem]
) -> Tuple[int, int]:
    """
    Save employee skills using replace-all strategy.
    
    Atomically:
    1. Delete all existing skills for the employee
    2. Insert all submitted skills
    
    Args:
        db: Database session
        employee_id: Employee ID
        skills: List of skill items to save
        
    Returns:
        Tuple of (skills_saved, skills_deleted)
        
    Raises:
        HTTPException: On validation errors
        SQLAlchemyError: On database errors
    """
    # Validate employee exists
    validate_employee_exists(db, employee_id)
    
    # Validate all skill IDs exist
    skill_ids = [s.skill_id for s in skills]
    validate_skills_exist(db, skill_ids)
    
    try:
        # Count existing skills before delete
        existing_count = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee_id
        ).count()
        
        # Delete all existing skills for this employee
        db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee_id
        ).delete(synchronize_session=False)
        
        logger.info(f"Deleted {existing_count} existing skills for employee {employee_id}")
        
        # Insert new skills
        for skill_item in skills:
            # Get proficiency level ID
            proficiency_level_id = _get_proficiency_level_id(db, skill_item.proficiency)
            
            # Parse last_used date
            last_used = _parse_last_used_date(
                skill_item.last_used_month,
                skill_item.last_used_year
            )
            
            # Parse years_experience to int (rounded)
            years_exp = None
            if skill_item.years_experience is not None:
                years_exp = int(round(skill_item.years_experience))
            
            # Create new skill record
            new_skill = EmployeeSkill(
                employee_id=employee_id,
                skill_id=skill_item.skill_id,
                proficiency_level_id=proficiency_level_id,
                years_experience=years_exp,
                last_used=last_used,
                started_learning_from=skill_item.started_from,
                certification=skill_item.certification
            )
            db.add(new_skill)
        
        # Commit transaction
        db.commit()
        
        logger.info(f"Saved {len(skills)} skills for employee {employee_id}")
        return (len(skills), existing_count)
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error saving skills for employee {employee_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error saving skills"
        )
