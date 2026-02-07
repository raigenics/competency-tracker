"""
Segment model - master/dimension table for organizational hierarchy.

Segments are the top-level organizational units (e.g., Business Divisions, Departments).
They contain multiple sub_segments.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Segment(Base):
    """Segment model for top-level organizational structure."""
    
    __tablename__ = "segments"
    
    segment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    segment_name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        default=func.now()
    )
    
    # Relationships
    sub_segments = relationship(
        "SubSegment", 
        back_populates="segment",
        cascade="all, delete-orphan",
        passive_deletes=False  # RESTRICT constraint prevents deletion if sub_segments exist
    )
    
    def __repr__(self):
        return f"<Segment(id={self.segment_id}, name='{self.segment_name}')>"
