"""
Service layer for Capability Finder (Advanced Query) feature.
Handles business logic for fetching typeahead/autocomplete data.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func
from app.models.skill import Skill
from app.models.role import Role


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
