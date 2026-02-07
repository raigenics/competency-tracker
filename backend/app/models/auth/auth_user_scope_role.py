"""
AuthUserScopeRole Model - Core RBAC Assignment Table

PURPOSE:
Assigns roles to users with optional scope constraints.
This is the heart of the RBAC system.

Examples:
- User X has SUPER_ADMIN role with GLOBAL scope (scope_id=NULL)
- User Y has SEGMENT_HEAD role for SUB_SEGMENT scope with scope_id=5
- User Z has TEAM_LEAD role for TEAM scope with scope_id=42

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Index, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuthUserScopeRole(Base):
    """
    User role assignment with scope.
    
    Core RBAC table tracking who has what role where.
    Supports role revocation via revoked_at timestamp.
    """
    
    __tablename__ = "auth_user_scope_roles"
    
    # Primary Key
    user_scope_role_id = Column(Integer, primary_key=True, index=True)
    
    # User assignment
    user_id = Column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Role assignment
    role_id = Column(
        Integer, 
        ForeignKey("auth_roles.role_id", ondelete="RESTRICT"), 
        nullable=False,
        index=True
    )
    
    # Scope definition
    scope_type_id = Column(
        Integer, 
        ForeignKey("auth_scope_types.scope_type_id", ondelete="RESTRICT"), 
        nullable=False,
        index=True
    )
    
    # Scope target (NULL for GLOBAL, otherwise ID of segment/project/team/employee)
    scope_id = Column(Integer, nullable=True, index=True)
    
    # Audit fields
    granted_by = Column(
        Integer, 
        ForeignKey("users.user_id", ondelete="SET NULL"), 
        nullable=True
    )
    granted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Derived status (for query optimization)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="scope_roles", foreign_keys=[user_id])
    role = relationship("AuthRole", back_populates="user_assignments")
    scope_type = relationship("AuthScopeType", back_populates="user_scope_assignments")
    granted_by_user = relationship("User", back_populates="granted_roles", foreign_keys=[granted_by])
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique active assignment per user/role/scope combination
        Index(
            'idx_active_user_role_scope',
            'user_id', 'role_id', 'scope_type_id', 'scope_id', 'is_active',
            unique=True,
            postgresql_where=(Column('is_active') == True)
        ),
        # Check: revoked assignments must have revoked_at timestamp
        CheckConstraint(
            '(is_active = true AND revoked_at IS NULL) OR (is_active = false AND revoked_at IS NOT NULL)',
            name='chk_active_revoked_consistency'
        ),
        # Check: GLOBAL scope must have NULL scope_id (enforced in app logic, documented here)
    )
    
    def __repr__(self):
        return (f"<AuthUserScopeRole(id={self.user_scope_role_id}, "
                f"user_id={self.user_id}, role_id={self.role_id}, "
                f"scope_type_id={self.scope_type_id}, scope_id={self.scope_id}, "
                f"active={self.is_active})>")
