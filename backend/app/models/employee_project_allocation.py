"""
Employee Project Allocation model - tracks employee allocation to projects over time.

This table supports future staffing and availability planning.
Availability is DERIVED (100% - sum of allocations), not stored.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class EmployeeProjectAllocation(Base):
    """
    Employee project allocation model.
    
    Tracks what percentage of an employee's time is allocated to a specific project.
    Multiple allocations per employee are allowed (can work on multiple projects).
    """
    
    __tablename__ = "employee_project_allocations"
    
    # Primary key
    allocation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign keys
    employee_id = Column(
        Integer, 
        ForeignKey("employees.employee_id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    project_id = Column(
        Integer, 
        ForeignKey("projects.project_id"), 
        nullable=False, 
        index=True
    )
    
    # Allocation details
    allocation_pct = Column(Integer, nullable=False)  # 0-100
    allocation_type = Column(String(30), nullable=False)  # BILLABLE, INTERNAL, BENCH, SHADOW
    
    # Date range
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL = ongoing/active
    
    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    employee = relationship("Employee", back_populates="project_allocations")
    project = relationship("Project")
    
    # Table-level constraints and indexes
    __table_args__ = (
        CheckConstraint('allocation_pct >= 0 AND allocation_pct <= 100', name='ck_allocation_pct_range'),
        CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_end_date_after_start'),
        Index('ix_employee_project_allocations_emp_dates', 'employee_id', 'start_date', 'end_date'),
    )
    
    def __repr__(self):
        return (
            f"<EmployeeProjectAllocation(id={self.allocation_id}, "
            f"employee_id={self.employee_id}, project_id={self.project_id}, "
            f"pct={self.allocation_pct}%, type={self.allocation_type})>"
        )
