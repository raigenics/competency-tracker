"""
Skill Employees List Service - GET /skills/{skill_id}/employees

Returns detailed employee list for the View Employees table.
Includes proficiency level, certification status, and days since last update.

Zero dependencies on other services.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Skill, Employee, EmployeeSkill, ProficiencyLevel
from app.models.team import Team
from app.models.project import Project
from app.schemas.skill import SkillEmployeesListResponse, SkillEmployeeListItem

logger = logging.getLogger(__name__)


def get_skill_employees_list(db: Session, skill_id: int) -> SkillEmployeesListResponse:
    """
    Get detailed employee list for a specific skill.
    
    Args:
        db: Database session
        skill_id: The skill ID to fetch employees for
    
    Returns:
        SkillEmployeesListResponse with list of employees and their skill-specific data
    
    Raises:
        ValueError: If skill_id does not exist
    """
    logger.info(f"Fetching employees list for skill_id: {skill_id}")
    
    # Get skill name first
    skill = _query_skill(db, skill_id)
    if skill is None:
        raise ValueError(f"Skill with id {skill_id} not found")
    
    # Query employee-skill data
    raw_data = _query_employee_skill_data(db, skill_id)
    
    # Transform to response items
    employees = _build_employee_list_items(raw_data)
    
    response = SkillEmployeesListResponse(
        skill_id=skill_id,
        skill_name=skill.skill_name,
        employees=employees,
        total_count=len(employees)
    )
    
    logger.info(f"Employees list for skill {skill_id}: {len(employees)} employees")
    return response


# === DATABASE QUERIES (Repository layer) ===

def _query_skill(db: Session, skill_id: int) -> Optional[Skill]:
    """
    Query skill by ID.
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Skill object or None if not found
    """
    return db.query(Skill).filter(
        Skill.skill_id == skill_id,
        Skill.deleted_at.is_(None)
    ).first()


def _query_employee_skill_data(db: Session, skill_id: int) -> List[Tuple]:
    """
    Query employee-skill mappings with related data for a skill.
    
    Returns list of tuples containing:
    (employee_id, employee_name, sub_segment_name, team_name, 
     proficiency_level_id, level_name, certification, last_updated)
    
    Uses canonical chain: employee -> team -> project -> sub_segment
    """
    from app.models.sub_segment import SubSegment
    
    return db.query(
        Employee.employee_id,
        Employee.full_name,
        SubSegment.sub_segment_name,
        Team.team_name,
        EmployeeSkill.proficiency_level_id,
        ProficiencyLevel.level_name,
        EmployeeSkill.certification,
        EmployeeSkill.last_updated
    ).join(
        EmployeeSkill, EmployeeSkill.employee_id == Employee.employee_id
    ).join(
        ProficiencyLevel, EmployeeSkill.proficiency_level_id == ProficiencyLevel.proficiency_level_id
    ).outerjoin(
        Team, Employee.team_id == Team.team_id
    ).outerjoin(
        Project, Team.project_id == Project.project_id
    ).outerjoin(
        SubSegment, Project.sub_segment_id == SubSegment.sub_segment_id
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        Employee.deleted_at.is_(None)
    ).order_by(
        Employee.full_name.asc()
    ).all()


# === PURE TRANSFORMATION FUNCTIONS ===

def _calculate_days_since_update(last_updated: Optional[datetime]) -> Optional[int]:
    """
    Calculate days since last_updated timestamp.
    
    Args:
        last_updated: Datetime of last update (may be None)
    
    Returns:
        Number of days since update, or None if last_updated is None
    """
    if last_updated is None:
        return None
    
    now = datetime.now(timezone.utc)
    
    # Handle timezone-naive datetimes
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)
    
    delta = now - last_updated
    return max(0, delta.days)


def _determine_certified(certification: Optional[str]) -> bool:
    """
    Determine if employee is certified based on certification field.
    
    Args:
        certification: Certification string value (may be None or empty)
    
    Returns:
        True if certification has a non-empty value, False otherwise
    """
    return bool(certification and certification.strip())


def _build_employee_list_items(raw_data: List[Tuple]) -> List[SkillEmployeeListItem]:
    """
    Transform raw query results to SkillEmployeeListItem list.
    
    Args:
        raw_data: List of tuples from database query
    
    Returns:
        List of SkillEmployeeListItem objects
    """
    items = []
    
    for row in raw_data:
        (employee_id, full_name, sub_segment_name, team_name,
         proficiency_level_id, level_name, certification, last_updated) = row
        
        items.append(SkillEmployeeListItem(
            employee_id=employee_id,
            employee_name=full_name,
            sub_segment=sub_segment_name,
            team_name=team_name,
            proficiency_level=proficiency_level_id,
            proficiency_label=level_name,
            certified=_determine_certified(certification),
            skill_last_updated_days=_calculate_days_since_update(last_updated)
        ))
    
    return items
