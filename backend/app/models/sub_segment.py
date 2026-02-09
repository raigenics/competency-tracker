"""
Sub-segment model - master/dimension table.

Sub-segments are organizational units within a parent segment.

NORMALIZED: employees no longer have direct sub_segment_id FK.
Access employees via: sub_segment.projects -> project.teams -> team.employees
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class SubSegment(Base):
    """Sub-segment model for organizational structure."""
    
    __tablename__ = "sub_segments"
    
    sub_segment_id = Column(Integer, primary_key=True, index=True)
    sub_segment_name = Column(String, unique=True, nullable=False, index=True)
    
    # Foreign key to parent segment (nullable for backward compatibility)
    # Will be populated for all records after migration, but remains nullable
    # to allow legacy code to continue working until fully migrated
    segment_id = Column(
        Integer, 
        ForeignKey("segments.segment_id", ondelete="RESTRICT"), 
        nullable=True,
        index=True
    )
    
    # Relationships
    segment = relationship("Segment", back_populates="sub_segments")
    projects = relationship("Project", back_populates="sub_segment")
    
    @property
    def employees(self):
        """
        Get all employees in this sub_segment via projects -> teams.
        For backward compatibility - prefer explicit project/team queries.
        """
        all_employees = []
        for project in self.projects:
            for team in project.teams:
                all_employees.extend(team.employees)
        return all_employees
    
    def __repr__(self):
        return f"<SubSegment(id={self.sub_segment_id}, name='{self.sub_segment_name}', segment_id={self.segment_id})>"

