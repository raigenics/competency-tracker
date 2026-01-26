"""
Sub-segment model - master/dimension table.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class SubSegment(Base):
    """Sub-segment model for organizational structure."""
    
    __tablename__ = "sub_segments"
    
    sub_segment_id = Column(Integer, primary_key=True, index=True)
    sub_segment_name = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    employees = relationship("Employee", back_populates="sub_segment")
    projects = relationship("Project", back_populates="sub_segment")
    
    def __repr__(self):
        return f"<SubSegment(id={self.sub_segment_id}, name='{self.sub_segment_name}')>"
