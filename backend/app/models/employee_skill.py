"""
Employee skill model - fact table (volatile, wiped and replaced on import).
"""
from sqlalchemy import Column, Integer, ForeignKey, Date, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class EmployeeSkill(Base):
    """Employee skill model for competency assessment."""
    
    __tablename__ = "employee_skills"
    
    emp_skill_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_level_id = Column(Integer, ForeignKey("proficiency_levels.proficiency_level_id", ondelete="CASCADE"), nullable=False)
    years_experience = Column(Integer, nullable=True)
    last_used = Column(Date, nullable=True)
    started_learning_from = Column(Date, nullable=True)
    certification = Column(String(500), nullable=True)
    comment = Column(Text, nullable=True)
    interest_level = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)
    
    # New columns added for soft delete and audit tracking
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="employee_skills")
    skill = relationship("Skill", back_populates="employee_skills")
    proficiency_level = relationship("ProficiencyLevel", back_populates="employee_skills")
    
    def __repr__(self):
        return f"<EmployeeSkill(id={self.emp_skill_id}, employee_id={self.employee_id}, skill_id={self.skill_id}, proficiency_id={self.proficiency_level_id})>"
