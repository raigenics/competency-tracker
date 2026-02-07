"""
AuthRolePermission Model - Role-Permission Junction

PURPOSE:
Many-to-many relationship between roles and permissions.
Allows flexible permission assignment to roles.

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuthRolePermission(Base):
    """
    Junction table linking roles to permissions.
    
    Allows a role to have multiple permissions.
    Allows a permission to be assigned to multiple roles.
    """
    
    __tablename__ = "auth_role_permissions"
    
    # Composite primary key
    role_id = Column(
        Integer, 
        ForeignKey("auth_roles.role_id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    permission_id = Column(
        Integer, 
        ForeignKey("auth_permissions.permission_id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    # Relationships
    role = relationship("AuthRole", back_populates="role_permissions")
    permission = relationship("AuthPermission", back_populates="role_assignments")
    
    # Unique constraint (redundant with composite PK, but explicit)
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    
    def __repr__(self):
        return f"<AuthRolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
