"""
User Model - Authentication Identity

PURPOSE:
Represents an authentication identity (login account).
NOT the same as Employee - some users are admins/segment heads who aren't employees.

SCHEMA ONLY - No auth logic implemented yet.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """
    User authentication identity.
    
    RBAC Foundation - represents who can log in to the system.
    Optionally linked to an Employee via user_employee_link table.
    """
    
    __tablename__ = "users"
    
    # Primary Key
    user_id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)  # NULL if using external auth provider
    
    # Account status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (will be populated by other models)
    employee_link = relationship("UserEmployeeLink", back_populates="user", uselist=False)
    scope_roles = relationship("AuthUserScopeRole", back_populates="user", foreign_keys="AuthUserScopeRole.user_id")
    granted_roles = relationship("AuthUserScopeRole", back_populates="granted_by_user", foreign_keys="AuthUserScopeRole.granted_by")
    audit_actions = relationship("AuthAuditLog", back_populates="actor", foreign_keys="AuthAuditLog.actor_user_id")
    audit_targets = relationship("AuthAuditLog", back_populates="target", foreign_keys="AuthAuditLog.target_user_id")
    
    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}', active={self.is_active})>"
