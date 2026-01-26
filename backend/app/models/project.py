"""
Project model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    """Project model for organizational structure."""
    
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False, index=True)
    sub_segment_id = Column(Integer, ForeignKey("sub_segments.sub_segment_id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    sub_segment = relationship("SubSegment", back_populates="projects")
    employees = relationship("Employee", back_populates="project")
    teams = relationship("Team", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id={self.project_id}, name='{self.project_name}', sub_segment_id={self.sub_segment_id})>"
