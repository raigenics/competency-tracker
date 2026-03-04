"""
Raw skill input model - stores original skill text from various sources before normalization.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class RawSkillInput(Base):
    """
    Raw skill input model for tracking skill text from various sources.
    Stores unnormalized skill text and tracks resolution to master skills.
    
    Status values:
    - UNRESOLVED: Skill not yet mapped to master data
    - RESOLVED: Skill mapped to existing skill via alias
    """
    
    __tablename__ = "raw_skill_inputs"
    
    # Primary key
    raw_skill_id = Column(Integer, primary_key=True, index=True)
    
    # Import job linkage (UUID string from ImportJob.job_id)
    job_id = Column(String(36), nullable=True, index=True)
    
    # Skill text fields
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False, index=True)
    
    # Source tracking
    sub_segment_id = Column(Integer, ForeignKey("sub_segments.sub_segment_id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="SET NULL"), nullable=True)
    
    # Resolution tracking
    resolved_skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_method = Column(String(20), nullable=True)
    resolution_confidence = Column(Float, nullable=True)
    
    # Resolution status and audit
    status = Column(String(20), nullable=False, default="UNRESOLVED", index=True)
    resolved_by = Column(String(50), nullable=True)  # User who resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    
    # Relationships
    sub_segment = relationship("SubSegment", backref="raw_skill_inputs")
    employee = relationship("Employee", backref="raw_skill_inputs")
    resolved_skill = relationship("Skill", backref="raw_skill_inputs")
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_raw_skills_segment_created', 'sub_segment_id', 'created_at'),
        Index('idx_raw_skills_job_status', 'job_id', 'status'),
        {"mysql_engine": "InnoDB"}
    )
    
    def __repr__(self):
        return f"<RawSkillInput(id={self.raw_skill_id}, raw_text='{self.raw_text[:30]}...', resolved_skill_id={self.resolved_skill_id})>"
