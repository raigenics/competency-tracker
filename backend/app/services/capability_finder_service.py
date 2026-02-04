"""
Service layer for Capability Finder (Advanced Query) feature.

THIN FACADE - delegates to isolated use-case services.
Each method delegates to exactly one service module to maintain backward compatibility.

This facade exists to preserve existing imports and router code.
All business logic has been extracted to isolated service modules under
app/services/capability_finder/ to ensure changes in one use case cannot break others.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.services.capability_finder.skills_service import get_all_skills as _get_all_skills
from app.services.capability_finder.roles_service import get_all_roles as _get_all_roles
from app.services.capability_finder.search_service import search_matching_talent as _search_matching_talent
from app.services.capability_finder.export_service import export_matching_talent_to_excel as _export_matching_talent_to_excel
from app.schemas.capability_finder import EmployeeSearchResult


class CapabilityFinderService:
    """
    Service facade for Capability Finder operations.
    
    This class maintains backward compatibility by delegating to isolated
    service modules. Each method calls exactly one service function.
    """
    
    @staticmethod
    def get_all_skills(db: Session) -> List[str]:
        """
        Get all distinct skill names sorted alphabetically.
        
        Delegates to: skills_service.get_all_skills()
        
        Args:
            db: Database session
            
        Returns:
            List of skill names sorted A-Z
        """
        return _get_all_skills(db)
    
    @staticmethod
    def get_all_roles(db: Session) -> List[str]:
        """
        Get all distinct role names sorted alphabetically.
        
        Delegates to: roles_service.get_all_roles()
        
        Args:
            db: Database session
            
        Returns:
            List of role names sorted A-Z
        """
        return _get_all_roles(db)
    
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
        
        Delegates to: search_service.search_matching_talent()
        
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
        return _search_matching_talent(
            db=db,
            skills=skills,
            sub_segment_id=sub_segment_id,
            team_id=team_id,
            role=role,
            min_proficiency=min_proficiency,
            min_experience_years=min_experience_years
        )
    
    @staticmethod
    def export_matching_talent_to_excel(
        db: Session,
        mode: str,
        skills: List[str],
        sub_segment_id: Optional[int] = None,
        team_id: Optional[int] = None,
        role: Optional[str] = None,
        min_proficiency: int = 0,
        min_experience_years: int = 0,
        selected_employee_ids: List[int] = None
    ):
        """
        Export matching talent to Excel format with all skills consolidated per employee.
        
        Delegates to: export_service.export_matching_talent_to_excel()
        
        Args:
            db: Database session
            mode: 'all' or 'selected'
            skills: List of required skill names (AND logic)
            sub_segment_id: Optional sub-segment filter
            team_id: Optional team filter
            role: Optional role name filter
            min_proficiency: Minimum proficiency level (0-5)
            min_experience_years: Minimum years of experience
            selected_employee_ids: List of employee IDs for mode='selected'
            
        Returns:
            BytesIO object containing Excel file
        """
        return _export_matching_talent_to_excel(
            db=db,
            mode=mode,
            skills=skills,
            sub_segment_id=sub_segment_id,
            team_id=team_id,
            role=role,
            min_proficiency=min_proficiency,
            min_experience_years=min_experience_years,
            selected_employee_ids=selected_employee_ids
        )
