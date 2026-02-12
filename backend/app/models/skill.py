"""
Skill model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Skill(Base):
    """Skill model for competency tracking."""
    
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String, nullable=False, index=True)
    subcategory_id = Column(Integer, ForeignKey("skill_subcategories.subcategory_id", ondelete="CASCADE"), nullable=False)
    
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
    subcategory = relationship("SkillSubcategory", back_populates="skills")
    employee_skills = relationship("EmployeeSkill", back_populates="skill")
    
    @property
    def category(self):
        """
        Compatibility property: derive category from subcategory.
        This maintains API compatibility while the category_id column has been removed from the database.
        """
        return self.subcategory.category if self.subcategory else None
    
    def __repr__(self):
        return f"<Skill(id={self.skill_id}, name='{self.skill_name}', subcategory_id={self.subcategory_id})>"
