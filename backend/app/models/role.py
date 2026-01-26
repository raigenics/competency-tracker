"""
Role model - master/dimension table for employee roles/designations.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Role(Base):
    """Role model for employee roles and designations."""
    
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True, nullable=False, index=True)
    role_description = Column(String(500), nullable=True)
    
    # Relationships
    employees = relationship("Employee", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.role_id}, name='{self.role_name}')>"
