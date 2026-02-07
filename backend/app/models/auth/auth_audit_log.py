"""
AuthAuditLog Model - Security Audit Trail

PURPOSE:
Tracks all security-relevant actions (role grants/revocations, permission changes, etc.).
Essential for compliance and security incident investigation.

SCHEMA ONLY - No logic implemented yet.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuthAuditLog(Base):
    """
    Audit log for authorization actions.
    
    Tracks who did what to whom and when.
    Immutable log (no updates or deletes).
    """
    
    __tablename__ = "auth_audit_log"
    
    # Primary Key
    audit_id = Column(Integer, primary_key=True, index=True)
    
    # Who performed the action
    actor_user_id = Column(
        Integer, 
        ForeignKey("users.user_id", ondelete="SET NULL"), 
        nullable=True,  # NULL if system action
        index=True
    )
    
    # What action was performed
    action_code = Column(String(100), nullable=False, index=True)  # e.g., "GRANT_ROLE", "REVOKE_ROLE"
    
    # Who was affected (optional)
    target_user_id = Column(
        Integer, 
        ForeignKey("users.user_id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    # Additional context (JSON)
    metadata_json = Column(Text, nullable=True)  # JSON string with action details
    
    # When it happened
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    actor = relationship("User", back_populates="audit_actions", foreign_keys=[actor_user_id])
    target = relationship("User", back_populates="audit_targets", foreign_keys=[target_user_id])
    
    def __repr__(self):
        return (f"<AuthAuditLog(id={self.audit_id}, "
                f"actor={self.actor_user_id}, action='{self.action_code}', "
                f"target={self.target_user_id})>")
