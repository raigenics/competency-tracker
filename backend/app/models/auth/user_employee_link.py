"""
User-Employee Link Model

PURPOSE:
Optional 1:1 mapping between User (auth identity) and Employee (org member).
Not all users are employees (e.g., external admins, segment heads from other divisions).
Not all employees have user accounts (e.g., they may not need system access).

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserEmployeeLink(Base):
    """
    Optional link between User and Employee.
    
    Use case: When a logged-in user needs their employee profile data.
    Constraint: One user can map to at most one employee.
    """
    
    __tablename__ = "user_employee_link"
    
    # Composite primary key (user-centric)
    user_id = Column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        primary_key=True,
        index=True
    )
    
    employee_id = Column(
        Integer, 
        ForeignKey("employees.employee_id", ondelete="CASCADE"), 
        nullable=False,
        unique=True,  # One employee can only link to one user
        index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="employee_link")
    employee = relationship("Employee")
    
    def __repr__(self):
        return f"<UserEmployeeLink(user_id={self.user_id}, employee_id={self.employee_id})>"
