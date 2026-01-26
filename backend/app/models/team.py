"""
Team model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Team(Base):
    """Team model for organizational structure."""
    
    __tablename__ = "teams"
    
    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="teams")
    employees = relationship("Employee", back_populates="team")
    
    def __repr__(self):
        return f"<Team(id={self.team_id}, name='{self.team_name}', project_id={self.project_id})>"
