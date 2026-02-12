"""
Project model - master/dimension table.

NORMALIZED: employees no longer have direct project_id FK.
Access employees via teams: project.teams -> team.employees

"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    """Project model for organizational structure."""
    
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False, index=True)
    sub_segment_id = Column(Integer, ForeignKey("sub_segments.sub_segment_id", ondelete="CASCADE"), nullable=False)
    
    # Audit columns
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        default=func.now()
    )
    created_by = Column(String(100), nullable=False, default="system", index=True)
    
    # Soft delete columns
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by = Column(String(100), nullable=True, index=True)
    
    # Relationships
    sub_segment = relationship("SubSegment", back_populates="projects")
    teams = relationship("Team", back_populates="project")
    
    @property
    def employees(self):
        """
        Get all employees in this project via teams.
        For backward compatibility - prefer explicit team queries.
        """
        all_employees = []
        for team in self.teams:
            all_employees.extend(team.employees)
        return all_employees
    
    def __repr__(self):
        return f"<Project(id={self.project_id}, name='{self.project_name}', sub_segment_id={self.sub_segment_id})>"
