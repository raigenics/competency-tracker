"""
Role model - master/dimension table for employee roles/designations.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Role(Base):
    """Role model for employee roles and designations."""
    
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, index=True)
    # Note: unique constraint is enforced via partial unique index ix_roles_role_name
    # (WHERE deleted_at IS NULL) to allow soft-deleted role names to be reused
    role_name = Column(String(100), nullable=False, index=True)
    role_alias = Column(Text, nullable=True)  # Comma-separated alias names
    role_description = Column(String(500), nullable=True)
    
    # Audit columns
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        default=func.now()
    )
    created_by = Column(String(100), nullable=False, default="system", index=True)
    
    # Soft delete columns
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by = Column(String(100), nullable=True, index=True)
    
    # Relationships
    employees = relationship("Employee", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.role_id}, name='{self.role_name}')>"
