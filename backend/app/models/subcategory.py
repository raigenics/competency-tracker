"""
Skill subcategory model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class SkillSubcategory(Base):
    """Skill subcategory model for detailed skill classification."""
    
    __tablename__ = "skill_subcategories"
    
    subcategory_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("skill_categories.category_id", ondelete="CASCADE"), nullable=False)
    subcategory_name = Column(String, nullable=False, index=True)
    
    # Relationships
    category = relationship("SkillCategory", back_populates="subcategories")
    skills = relationship("Skill", back_populates="subcategory")
    
    def __repr__(self):
        return f"<SkillSubcategory(id={self.subcategory_id}, name='{self.subcategory_name}', category_id={self.category_id})>"
