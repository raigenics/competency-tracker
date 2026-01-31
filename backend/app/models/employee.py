"""
Employee model - fact table (volatile, wiped and replaced on import).
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Employee(Base):
    """Employee model for competency tracking."""
    
    __tablename__ = "employees"
    
    employee_id = Column(Integer, primary_key=True, index=True)
    zid = Column(String(50), unique=True, nullable=False, index=True)  # Business ID from Excel
    full_name = Column(String(255), nullable=False, index=True)
    start_date_of_working = Column(Date, nullable=True)
    sub_segment_id = Column(Integer, ForeignKey("sub_segments.sub_segment_id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=True)
    
    # New columns added for soft delete and audit tracking
    email = Column(String(255), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    
    # Relationships
    sub_segment = relationship("SubSegment", back_populates="employees")
    project = relationship("Project", back_populates="employees")
    team = relationship("Team", back_populates="employees")
    role = relationship("Role", back_populates="employees")
    employee_skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Employee(id={self.employee_id}, zid='{self.zid}', name='{self.full_name}', role='{self.role.role_name if self.role else None}')>"
