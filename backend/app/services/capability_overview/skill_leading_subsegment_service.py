"""
Skill Leading Sub-Segment Service - GET /skills/{skill_id}/leading-subsegment

Computes the sub-segment with the highest number of distinct employees 
mapped to a specific skill.

Zero dependencies on other services.

Returns:
    - leading_sub_segment_name: Name of the leading sub-segment (or None if no data)
    - leading_sub_segment_employee_count: Count of distinct employees
"""
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.models import EmployeeSkill, Employee, Team, Project, SubSegment
from app.schemas.skill import SkillLeadingSubSegmentResponse

logger = logging.getLogger(__name__)


def get_skill_leading_subsegment(db: Session, skill_id: int) -> SkillLeadingSubSegmentResponse:
    """
    Get the leading sub-segment for a specific skill.
    
    Leading sub-segment = the sub-segment with the highest number of 
    distinct employees mapped to this skill.
    
    Args:
        db: Database session
        skill_id: The skill ID to query
    
    Returns:
        SkillLeadingSubSegmentResponse with name and count
    """
    logger.info(f"Fetching leading sub-segment for skill_id: {skill_id}")
    
    # Query for leading sub-segment
    result = _query_leading_subsegment(db, skill_id)
    
    # Build response
    if result:
        name, count = result
        response = SkillLeadingSubSegmentResponse(
            leading_sub_segment_name=name,
            leading_sub_segment_employee_count=count
        )
    else:
        response = SkillLeadingSubSegmentResponse(
            leading_sub_segment_name=None,
            leading_sub_segment_employee_count=0
        )
    
    logger.info(f"Leading sub-segment for skill {skill_id}: "
                f"{response.leading_sub_segment_name} ({response.leading_sub_segment_employee_count})")
    return response


# === DATABASE QUERIES (Repository layer) ===

def _query_leading_subsegment(db: Session, skill_id: int) -> Optional[Tuple[str, int]]:
    """
    Query the sub-segment with the highest distinct employee count for a skill.
    
    Joins: EmployeeSkill → Employee → Team → Project → SubSegment
    Groups by: sub_segment_id
    Orders by: count DESC, then sub_segment_name ASC (deterministic tie-breaker)
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Tuple of (sub_segment_name, employee_count) or None if no data
    """
    result = db.query(
        SubSegment.sub_segment_name,
        func.count(func.distinct(EmployeeSkill.employee_id)).label('employee_count')
    ).join(
        Project, Project.sub_segment_id == SubSegment.sub_segment_id
    ).join(
        Team, Team.project_id == Project.project_id
    ).join(
        Employee, Employee.team_id == Team.team_id
    ).join(
        EmployeeSkill, EmployeeSkill.employee_id == Employee.employee_id
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        Employee.deleted_at.is_(None),
        SubSegment.deleted_at.is_(None),
        Project.deleted_at.is_(None)
    ).group_by(
        SubSegment.sub_segment_id,
        SubSegment.sub_segment_name
    ).order_by(
        desc('employee_count'),
        asc(SubSegment.sub_segment_name)  # Deterministic tie-breaker
    ).first()
    
    if result:
        return (result[0], result[1])
    return None
