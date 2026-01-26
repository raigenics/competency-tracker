"""
Skill model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Skill(Base):
    """Skill model for competency tracking."""
    
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("skill_categories.category_id", ondelete="CASCADE"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("skill_subcategories.subcategory_id", ondelete="CASCADE"), nullable=True)
    
    # Relationships
    category = relationship("SkillCategory", back_populates="skills")
    subcategory = relationship("SkillSubcategory", back_populates="skills")
    employee_skills = relationship("EmployeeSkill", back_populates="skill")
    
    def __repr__(self):
        return f"<Skill(id={self.skill_id}, name='{self.skill_name}', category_id={self.category_id})>"
