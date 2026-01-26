"""
Proficiency level model - static master/dimension table.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProficiencyLevel(Base):
    """Proficiency level model for skill assessment."""
    
    __tablename__ = "proficiency_levels"
    
    proficiency_level_id = Column(Integer, primary_key=True, index=True)
    level_name = Column(String, unique=True, nullable=False, index=True)
    level_description = Column(String, nullable=True)
    
    # Relationships
    employee_skills = relationship("EmployeeSkill", back_populates="proficiency_level")
    
    def __repr__(self):
        return f"<ProficiencyLevel(id={self.proficiency_level_id}, name='{self.level_name}')>"
