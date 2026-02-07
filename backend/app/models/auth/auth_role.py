"""
AuthRole Model - Authorization Roles

PURPOSE:
Defines authorization roles (NOT job roles like "Developer" or "Manager").
Examples: SUPER_ADMIN, SEGMENT_HEAD, PROJECT_MANAGER, TEAM_LEAD, EMPLOYEE, READ_ONLY

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuthRole(Base):
    """
    Authorization role definition.
    
    Represents a set of permissions that can be granted to users.
    Roles can be scoped (e.g., SEGMENT_HEAD for a specific segment).
    """
    
    __tablename__ = "auth_roles"
    
    # Primary Key
    role_id = Column(Integer, primary_key=True, index=True)
    
    # Role identification
    role_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "SUPER_ADMIN"
    role_name = Column(String(100), nullable=False)  # e.g., "Super Administrator"
    
    # Hierarchy/priority (lower number = higher privilege)
    level_rank = Column(Integer, nullable=False, default=100)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relationships
    role_permissions = relationship("AuthRolePermission", back_populates="role")
    user_assignments = relationship("AuthUserScopeRole", back_populates="role")
    
    def __repr__(self):
        return f"<AuthRole(id={self.role_id}, code='{self.role_code}', rank={self.level_rank})>"
