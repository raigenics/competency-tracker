"""
Dashboard service for employee scope and metrics calculations.
"""
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.models.employee import Employee
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team
from app.models.employee_skill import EmployeeSkill
from app.models.skill import Skill
from app.models.proficiency import ProficiencyLevel
from app.models.role import Role


class DashboardService:
    """Service class for dashboard-related data operations."""

    @staticmethod
    def get_employee_scope_count(
        db: Session,
        sub_segment_id: Optional[int] = None,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> Tuple[int, str, str]:
        """Get employee count and scope information based on filters."""
        # Validate filter hierarchy consistency
        DashboardService._validate_filter_hierarchy(db, sub_segment_id, project_id, team_id)
        
        # Determine scope level and build query
        if team_id:
            team = db.query(Team).filter(Team.team_id == team_id).first()
            if not team:
                raise ValueError(f"Team with ID {team_id} not found")
            count = db.query(func.count(Employee.employee_id)).filter(Employee.team_id == team_id).scalar()
            return count, "TEAM", team.team_name
        elif project_id:
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if not project:
                raise ValueError(f"Project with ID {project_id} not found")
            count = db.query(func.count(Employee.employee_id)).filter(Employee.project_id == project_id).scalar()
            return count, "PROJECT", project.project_name
        elif sub_segment_id:
            sub_segment = db.query(SubSegment).filter(SubSegment.sub_segment_id == sub_segment_id).first()
            if not sub_segment:
                raise ValueError(f"Sub-segment with ID {sub_segment_id} not found")
            count = db.query(func.count(Employee.employee_id)).filter(Employee.sub_segment_id == sub_segment_id).scalar()
            return count, "SUB_SEGMENT", sub_segment.sub_segment_name
        else:
            count = db.query(func.count(Employee.employee_id)).scalar()
            return count, "ORGANIZATION", "Organization-Wide"

    @staticmethod
    def _validate_filter_hierarchy(
        db: Session,
        sub_segment_id: Optional[int],
        project_id: Optional[int], 
        team_id: Optional[int]
    ) -> None:
        """Validate that the filter hierarchy is consistent."""
        if project_id and not sub_segment_id:
            raise ValueError("Project filter requires sub_segment_id to be provided")
        if team_id and not project_id:
            raise ValueError("Team filter requires project_id to be provided")

    @staticmethod
    def get_org_skill_coverage(db: Session) -> Dict[str, Any]:
        """Get organization-wide skill coverage by sub-segment and role. Ignores all filters."""
        from datetime import date
        
        sub_segment_query = db.query(
            SubSegment.sub_segment_name,
            func.count(func.distinct(Employee.employee_id)).label('total_employees'),
            func.sum(case((Role.role_name == 'Manual Tester', 1), else_=0)).label('frontend_dev'),
            func.sum(case((Role.role_name == 'Tech Lead', 1), else_=0)).label('backend_dev'),
            func.sum(case((Role.role_name == 'Developer', 1), else_=0)).label('full_stack'),
            func.sum(case((Role.role_name == 'PM', 1), else_=0)).label('cloud_eng'),
            func.sum(case((Role.role_name == 'PM', 1), else_=0)).label('devops')
        ).outerjoin(Employee, SubSegment.sub_segment_id == Employee.sub_segment_id
        ).outerjoin(Role, Employee.role_id == Role.role_id
        ).group_by(SubSegment.sub_segment_id, SubSegment.sub_segment_name
        ).order_by(SubSegment.sub_segment_name)
        
        sub_segment_results = sub_segment_query.all()
        sub_segments_data = []
        org_totals = {'total_employees': 0, 'frontend_dev': 0, 'backend_dev': 0, 'full_stack': 0, 'cloud_eng': 0, 'devops': 0}
        
        for result in sub_segment_results:
            total_employees = int(result.total_employees or 0)
            
            if total_employees > 0:
                certified_count = db.query(func.count(func.distinct(Employee.employee_id))).filter(
                    Employee.sub_segment_id == db.query(SubSegment.sub_segment_id).filter(SubSegment.sub_segment_name == result.sub_segment_name).scalar(),
                    Employee.employee_id.in_(
                        db.query(EmployeeSkill.employee_id).filter(
                            EmployeeSkill.certification.isnot(None),
                            EmployeeSkill.certification != ''
                        ).distinct()
                    )
                ).scalar()
                certified_pct = round((certified_count / total_employees) * 100) if total_employees > 0 else 0
            else:
                certified_pct = 0
            
            frontend_dev = int(result.frontend_dev or 0)
            backend_dev = int(result.backend_dev or 0)
            full_stack = int(result.full_stack or 0)
            cloud_eng = int(result.cloud_eng or 0)
            devops = int(result.devops or 0)
            
            sub_segment_data = {
                'sub_segment_name': result.sub_segment_name,
                'total_employees': total_employees,
                'frontend_dev': frontend_dev,
                'backend_dev': backend_dev,
                'full_stack': full_stack,
                'cloud_eng': cloud_eng,
                'devops': devops,
                'certified_pct': certified_pct
            }
            
            sub_segments_data.append(sub_segment_data)
            
            org_totals['total_employees'] += total_employees
            org_totals['frontend_dev'] += frontend_dev
            org_totals['backend_dev'] += backend_dev
            org_totals['full_stack'] += full_stack
            org_totals['cloud_eng'] += cloud_eng
            org_totals['devops'] += devops
        
        if org_totals['total_employees'] > 0:
            org_certified_count = db.query(func.count(func.distinct(Employee.employee_id))).filter(
                Employee.employee_id.in_(
                    db.query(EmployeeSkill.employee_id).filter(
                        EmployeeSkill.certification.isnot(None),
                        EmployeeSkill.certification != ''
                    ).distinct()
                )
            ).scalar()
            org_certified_pct = round((org_certified_count / org_totals['total_employees']) * 100)
        else:
            org_certified_pct = 0
        
        organization_total = {
            'total_employees': org_totals['total_employees'],
            'frontend_dev': org_totals['frontend_dev'],
            'backend_dev': org_totals['backend_dev'],
            'full_stack': org_totals['full_stack'],
            'cloud_eng': org_totals['cloud_eng'],
            'devops': org_totals['devops'],
            'certified_pct': org_certified_pct
        }
        
        return {
            'sub_segments': sub_segments_data,
            'organization_total': organization_total,
            'as_of': date.today().strftime('%Y-%m-%d')
        }