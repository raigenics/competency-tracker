"""
Skill category model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class SkillCategory(Base):
    """Skill category model for skill classification."""
    
    __tablename__ = "skill_categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    subcategories = relationship("SkillSubcategory", back_populates="category")
    # Note: Direct skills relationship removed since skills.category_id column was dropped
    # To access skills in a category, use: category.subcategories -> subcategory.skills
    
    def __repr__(self):
        return f"<SkillCategory(id={self.category_id}, name='{self.category_name}')>"
