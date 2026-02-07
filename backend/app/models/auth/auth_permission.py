"""
AuthPermission Model - Granular Permissions

PURPOSE:
Defines fine-grained permissions (future-proofing).
Examples: "view_employees", "edit_skills", "manage_roles", "export_data"

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuthPermission(Base):
    """
    Permission definition.
    
    Represents a specific action or capability.
    Assigned to roles via auth_role_permissions junction table.
    """
    
    __tablename__ = "auth_permissions"
    
    # Primary Key
    permission_id = Column(Integer, primary_key=True, index=True)
    
    # Permission identification
    permission_code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "view_employees"
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relationships
    role_assignments = relationship("AuthRolePermission", back_populates="permission")
    
    def __repr__(self):
        return f"<AuthPermission(id={self.permission_id}, code='{self.permission_code}')>"
