"""
Employee model - fact table (volatile, wiped and replaced on import).

NORMALIZED SCHEMA:
- team_id: FK to teams (current team)
- project/sub_segment derived via: team -> project -> sub_segment -> segment

REMOVED DENORMALIZED COLUMNS (see migration c3f8a2b7e9d1):
- sub_segment_id: Now derived via team.project.sub_segment
- project_id: Now derived via team.project
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
    
    # Current team (HYBRID pattern: kept for performance, must match active assignment)
    team_id = Column(Integer, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False)
    
    # Job role (NOT auth role - see auth.py for RBAC roles)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=True)
    
    # Contact & audit
    email = Column(String(255), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="employees")
    role = relationship("Role", back_populates="employees")
    employee_skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    
    # Derived properties (navigate through relationships)
    @property
    def project(self):
        """Get current project via team relationship."""
        return self.team.project if self.team else None
    
    @property
    def sub_segment(self):
        """Get current sub_segment via team.project relationship."""
        project = self.project
        return project.sub_segment if project else None
    
    @property
    def project_id(self):
        """Get current project_id (for backward compatibility in queries)."""
        return self.team.project_id if self.team else None
    
    @property
    def sub_segment_id(self):
        """Get current sub_segment_id (for backward compatibility in queries)."""
        project = self.project
        return project.sub_segment_id if project else None
    
    def __repr__(self):
        return f"<Employee(id={self.employee_id}, zid='{self.zid}', name='{self.full_name}', role='{self.role.role_name if self.role else None}')>"
