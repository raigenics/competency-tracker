"""
Service layer for dropdown data operations.
"""
from typing import List
from sqlalchemy.orm import Session
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team


class DropdownService:
    """Service for managing dropdown data operations."""

    @staticmethod
    def get_sub_segments(db: Session) -> List[SubSegment]:
        """
        Get all sub-segments ordered alphabetically.
        
        Args:
            db: Database session
            
        Returns:
            List of SubSegment objects ordered by name
        """
        return db.query(SubSegment).order_by(SubSegment.sub_segment_name).all()

    @staticmethod
    def get_projects_by_sub_segment(db: Session, sub_segment_id: int) -> List[Project]:
        """
        Get all projects for a specific sub-segment ordered alphabetically.
        
        Args:
            db: Database session
            sub_segment_id: ID of the sub-segment
            
        Returns:
            List of Project objects for the sub-segment ordered by name
            
        Raises:
            ValueError: If sub_segment_id is invalid
        """
        # Validate sub-segment exists
        sub_segment = db.query(SubSegment).filter(SubSegment.sub_segment_id == sub_segment_id).first()
        if not sub_segment:
            raise ValueError(f"Sub-segment with ID {sub_segment_id} not found")
        
        return (
            db.query(Project)
            .filter(Project.sub_segment_id == sub_segment_id)
            .order_by(Project.project_name)
            .all()
        )

    @staticmethod
    def get_teams_by_project(db: Session, project_id: int) -> List[Team]:
        """
        Get all teams for a specific project ordered alphabetically.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            List of Team objects for the project ordered by name
            
        Raises:
            ValueError: If project_id is invalid
        """
        # Validate project exists
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        return (
            db.query(Team)
            .filter(Team.project_id == project_id)
            .order_by(Team.team_name)
            .all()
        )
