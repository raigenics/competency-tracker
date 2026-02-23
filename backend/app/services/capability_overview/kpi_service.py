"""
KPI Service - GET /skills/capability-kpis

Provides aggregate KPIs for the Capability Overview page:
- Total Skills (with at least one mapped employee)
- Average Proficiency (across mapped employees)
- Total Certifications (count of non-null certification fields)

All metrics are scoped to employees in non-deleted sub-segments.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import EmployeeSkill, Employee, Team, Project, SubSegment
from app.schemas.skill import CapabilityKPIsResponse

logger = logging.getLogger(__name__)


def get_capability_kpis(db: Session) -> CapabilityKPIsResponse:
    """
    Get KPI metrics for the Capability Overview page.
    
    Scope: All employees in non-deleted sub-segments.
    
    Args:
        db: Database session
    
    Returns:
        CapabilityKPIsResponse with total_skills, avg_proficiency, total_certifications
    """
    logger.info("Fetching capability KPIs")
    
    # Base subquery: employee_ids in non-deleted sub-segments
    scoped_employee_ids = _get_scoped_employee_ids_subquery(db)
    
    # Query KPIs
    total_skills = _query_total_skills_with_employees(db, scoped_employee_ids)
    avg_proficiency = _query_avg_proficiency(db, scoped_employee_ids)
    total_certifications = _query_total_certifications(db, scoped_employee_ids)
    
    logger.info(
        f"KPIs: total_skills={total_skills}, "
        f"avg_proficiency={avg_proficiency}, "
        f"total_certifications={total_certifications}"
    )
    
    return CapabilityKPIsResponse(
        total_skills=total_skills,
        avg_proficiency=avg_proficiency,
        total_certifications=total_certifications
    )


def _get_scoped_employee_ids_subquery(db: Session):
    """
    Build subquery for employee IDs within non-deleted sub-segments.
    
    Path: Employee → Team → Project → SubSegment
    """
    return (
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


def _query_total_skills_with_employees(db: Session, scoped_employee_ids) -> int:
    """
    Count distinct skills that have at least one mapped employee.
    
    A skill is "mapped" if it appears in employee_skills for a scoped employee.
    """
    result = (
        db.query(func.count(func.distinct(EmployeeSkill.skill_id)))
        .filter(
            EmployeeSkill.employee_id.in_(
                db.query(scoped_employee_ids.c.employee_id)
            ),
            EmployeeSkill.deleted_at.is_(None)
        )
        .scalar()
    )
    return result or 0


def _query_avg_proficiency(db: Session, scoped_employee_ids) -> Optional[float]:
    """
    Calculate average proficiency_level_id across all mapped employees.
    
    Returns None if no data.
    """
    result = (
        db.query(func.avg(EmployeeSkill.proficiency_level_id))
        .filter(
            EmployeeSkill.employee_id.in_(
                db.query(scoped_employee_ids.c.employee_id)
            ),
            EmployeeSkill.deleted_at.is_(None)
        )
        .scalar()
    )
    return round(float(result), 2) if result is not None else None


def _query_total_certifications(db: Session, scoped_employee_ids) -> int:
    """
    Count employee_skills with non-null, non-empty certification field.
    """
    result = (
        db.query(func.count(EmployeeSkill.emp_skill_id))
        .filter(
            EmployeeSkill.employee_id.in_(
                db.query(scoped_employee_ids.c.employee_id)
            ),
            EmployeeSkill.deleted_at.is_(None),
            EmployeeSkill.certification.isnot(None),
            EmployeeSkill.certification != ''
        )
        .scalar()
    )
    return result or 0
