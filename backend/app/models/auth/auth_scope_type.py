"""
AuthScopeType Model - Scope Type Definitions

PURPOSE:
Defines the types of scopes that roles can be assigned to.
Examples: GLOBAL, SEGMENT, SUB_SEGMENT, PROJECT, TEAM, EMPLOYEE

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuthScopeType(Base):
    """
    Scope type definition.
    
    Represents organizational levels at which roles can be assigned.
    Hierarchy: GLOBAL > SEGMENT > SUB_SEGMENT > PROJECT > TEAM > EMPLOYEE
    """
    
    __tablename__ = "auth_scope_types"
    
    # Primary Key
    scope_type_id = Column(Integer, primary_key=True, index=True)
    
    # Scope type identification
    scope_type_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "SUB_SEGMENT"
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relationships
    user_scope_assignments = relationship("AuthUserScopeRole", back_populates="scope_type")
    
    def __repr__(self):
        return f"<AuthScopeType(id={self.scope_type_id}, code='{self.scope_type_code}')>"
