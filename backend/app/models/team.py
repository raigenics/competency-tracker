"""
Team model - master/dimension table.

Teams are the canonical organizational unit for employees.
- employees.team_id points here (current team)

"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Team(Base):
    """Team model for organizational structure."""
    
    __tablename__ = "teams"
    
    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    
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
    project = relationship("Project", back_populates="teams")
    employees = relationship("Employee", back_populates="team")
    
    @property
    def sub_segment(self):
        """Get sub_segment via project relationship."""
        return self.project.sub_segment if self.project else None
    
    @property
    def sub_segment_id(self):
        """Get sub_segment_id via project relationship."""
        return self.project.sub_segment_id if self.project else None
    
    def __repr__(self):
        return f"<Team(id={self.team_id}, name='{self.team_name}', project_id={self.project_id})>"
