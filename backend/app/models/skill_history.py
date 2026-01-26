"""
Proficiency Change History Model - Audit Trail Pattern
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class ChangeAction(str, enum.Enum):
    """Types of changes that can be tracked."""
    INSERT = "INSERT"      # New skill record created
    UPDATE = "UPDATE"      # Proficiency level changed
    DELETE = "DELETE"      # Skill record removed (rare)


class ChangeSource(str, enum.Enum):
    """Source of the change."""
    IMPORT = "IMPORT"      # Excel import
    UI = "UI"              # Manual UI update
    SYSTEM = "SYSTEM"      # System-generated change
    API = "API"            # API call


class EmployeeSkillHistory(Base):
    """
    Audit trail for employee skill changes.
    
    This table records EVERY change to employee skills, creating a complete audit trail.
    Each row represents a state transition or new record creation.
    """
    
    __tablename__ = "employee_skill_history"
    
    # Primary key
    history_id = Column(Integer, primary_key=True, index=True)
    
    # What was changed (foreign keys)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False, index=True)
    emp_skill_id = Column(Integer, ForeignKey("employee_skills.emp_skill_id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Change metadata
    action = Column(Enum(ChangeAction), nullable=False, index=True)
    changed_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    change_source = Column(Enum(ChangeSource), nullable=False, index=True)
    changed_by = Column(String(100), nullable=True)  # Future: user identifier
    
    # Before state (NULL for INSERT operations)
    old_proficiency_level_id = Column(Integer, ForeignKey("proficiency_levels.proficiency_level_id"), nullable=True)
    old_years_experience = Column(Integer, nullable=True)
    old_last_used = Column(DateTime, nullable=True)
    old_certification = Column(String(500), nullable=True)
    
    # After state (NULL for DELETE operations)
    new_proficiency_level_id = Column(Integer, ForeignKey("proficiency_levels.proficiency_level_id"), nullable=True)
    new_years_experience = Column(Integer, nullable=True)
    new_last_used = Column(DateTime, nullable=True)
    new_certification = Column(String(500), nullable=True)
    
    # Additional context
    change_reason = Column(String(500), nullable=True)  # Optional reason for change
    batch_id = Column(String(50), nullable=True)  # For grouping related changes (e.g., import batch)
    
    # Relationships
    employee = relationship("Employee")
    skill = relationship("Skill")
    employee_skill = relationship("EmployeeSkill")
    old_proficiency = relationship("ProficiencyLevel", foreign_keys=[old_proficiency_level_id])
    new_proficiency = relationship("ProficiencyLevel", foreign_keys=[new_proficiency_level_id])
    
    # Indexes for performance
    __table_args__ = (
        # Composite indexes for common queries
        {"mysql_engine": "InnoDB"}
    )
    
    def __repr__(self):
        return f"<EmployeeSkillHistory(id={self.history_id}, employee_id={self.employee_id}, skill_id={self.skill_id}, action={self.action}, changed_at={self.changed_at})>"


# Alternative: If you want ONLY proficiency changes (more focused)
class ProficiencyChangeHistory(Base):
    """
    Simplified version - tracks ONLY proficiency level changes.
    Use this if you only care about proficiency transitions.
    """
    
    __tablename__ = "proficiency_change_history"
    
    change_id = Column(Integer, primary_key=True, index=True)
    
    # What changed
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # The transition
    from_proficiency_id = Column(Integer, ForeignKey("proficiency_levels.proficiency_level_id"), nullable=True)  # NULL for new skills
    to_proficiency_id = Column(Integer, ForeignKey("proficiency_levels.proficiency_level_id"), nullable=False)
    
    # When and how
    changed_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    change_source = Column(Enum(ChangeSource), nullable=False)
    changed_by = Column(String(100), nullable=True)
    change_reason = Column(String(500), nullable=True)
    batch_id = Column(String(50), nullable=True)
    
    # Relationships
    employee = relationship("Employee")
    skill = relationship("Skill")
    from_proficiency = relationship("ProficiencyLevel", foreign_keys=[from_proficiency_id])
    to_proficiency = relationship("ProficiencyLevel", foreign_keys=[to_proficiency_id])
    
    def __repr__(self):
        return f"<ProficiencyChangeHistory(employee_id={self.employee_id}, skill_id={self.skill_id}, {self.from_proficiency_id}→{self.to_proficiency_id})>"
