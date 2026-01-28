"""
Service layer for Capability Finder (Advanced Query) feature.
Handles business logic for fetching typeahead/autocomplete data.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func, and_, or_
from app.models.skill import Skill
from app.models.role import Role
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill
from app.models.proficiency import ProficiencyLevel
from app.models.sub_segment import SubSegment
from app.models.team import Team
from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo


class CapabilityFinderService:
    """Service for capability finder data operations."""
    
    @staticmethod
    def get_all_skills(db: Session) -> List[str]:
        """
        Get all distinct skill names sorted alphabetically.
        
        Args:
            db: Database session
            
        Returns:
            List of skill names sorted A-Z
        """
        skills = db.query(Skill.skill_name)\
            .distinct()\
            .order_by(Skill.skill_name)\
            .all()
        
        return [skill[0] for skill in skills]
    
    @staticmethod
    def get_all_roles(db: Session) -> List[str]:
        """
        Get all distinct role names sorted alphabetically.
        
        Args:
            db: Database session
            
        Returns:
            List of role names sorted A-Z
        """
        roles = db.query(Role.role_name)\
            .distinct()\
            .order_by(Role.role_name)\
            .all()
        
        return [role[0] for role in roles]
    
    @staticmethod
    def search_matching_talent(
        db: Session,
        skills: List[str],
        sub_segment_id: Optional[int] = None,
        team_id: Optional[int] = None,
        role: Optional[str] = None,
        min_proficiency: int = 0,
        min_experience_years: int = 0
    ) -> List[EmployeeSearchResult]:
        """
        Search for employees matching specified criteria.
        
        Args:
            db: Database session
            skills: List of required skill names (AND logic - must have ALL)
            sub_segment_id: Optional sub-segment filter
            team_id: Optional team filter
            role: Optional role name filter
            min_proficiency: Minimum proficiency level (0-5)
            min_experience_years: Minimum years of experience
            
        Returns:
            List of matching employees with their top 3 skills
        """
        # Build base query for employees who match ALL required skills
        query = db.query(Employee).join(EmployeeSkill).join(Skill)
        
        # Apply filters
        filters = []
          # Skills filter with AND logic
        if skills and len(skills) > 0:
            # Find skill IDs for the required skill names
            skill_ids = db.query(Skill.skill_id)\
                .filter(Skill.skill_name.in_(skills))\
                .all()
            skill_ids = [s[0] for s in skill_ids]
            
            if skill_ids:
                # Subquery to find employees who have ALL required skills
                # with minimum proficiency and experience
                skill_subquery = db.query(EmployeeSkill.employee_id)\
                    .filter(
                        EmployeeSkill.skill_id.in_(skill_ids),
                        EmployeeSkill.proficiency_level_id >= min_proficiency,
                        EmployeeSkill.years_experience >= min_experience_years
                    )\
                    .group_by(EmployeeSkill.employee_id)\
                    .having(func.count(distinct(EmployeeSkill.skill_id)) == len(skill_ids))
                
                filters.append(Employee.employee_id.in_(skill_subquery))
        
        # Organization filters
        if sub_segment_id:
            filters.append(Employee.sub_segment_id == sub_segment_id)
        
        if team_id:
            filters.append(Employee.team_id == team_id)
        
        if role:
            query = query.join(Role, Employee.role_id == Role.role_id)
            filters.append(Role.role_name == role)
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get distinct employees
        employees = query.distinct().all()
        
        # Build results with top 3 skills for each employee
        results = []
        for employee in employees:            # Get top 3 skills ordered by proficiency DESC, last_used DESC, skill_name ASC
            top_skills_query = db.query(
                Skill.skill_name,
                EmployeeSkill.proficiency_level_id
            )\
                .join(EmployeeSkill, EmployeeSkill.skill_id == Skill.skill_id)\
                .filter(EmployeeSkill.employee_id == employee.employee_id)\
                .order_by(
                    EmployeeSkill.proficiency_level_id.desc(),
                    EmployeeSkill.last_used.desc(),
                    Skill.skill_name.asc()
                )\
                .limit(3)\
                .all()
            
            top_skills = [
                SkillInfo(name=skill_name, proficiency=proficiency)
                for skill_name, proficiency in top_skills_query
            ]
            
            # Get organization info
            sub_segment_name = employee.sub_segment.sub_segment_name if employee.sub_segment else ""
            team_name = employee.team.team_name if employee.team else ""
            role_name = employee.role.role_name if employee.role else ""
            
            results.append(EmployeeSearchResult(
                employee_id=employee.employee_id,
                employee_name=employee.full_name,
                sub_segment=sub_segment_name,
                team=team_name,
                role=role_name,
                top_skills=top_skills
            ))
        
        return results
