"""
Skill alias model - maps alternative skill names to master skills.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class SkillAlias(Base):
    """
    Skill alias model for mapping alternative skill names to canonical skills.
    Helps with skill normalization and deduplication.
    """
    
    __tablename__ = "skill_aliases"
    
    # Primary key
    alias_id = Column(Integer, primary_key=True, index=True)
    
    # Alias text (unique constraint)
    alias_text = Column(Text, nullable=False, unique=True, index=True)
    
    # Master skill reference
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Source and confidence tracking
    source = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=True)
    
    # Audit timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    
    # Relationships
    skill = relationship("Skill", backref="aliases")
    
    def __repr__(self):
        return f"<SkillAlias(id={self.alias_id}, alias_text='{self.alias_text}', skill_id={self.skill_id})>"
