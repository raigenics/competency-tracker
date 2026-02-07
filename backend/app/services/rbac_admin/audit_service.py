"""
Audit logging service for RBAC operations.

Records all administrative actions for compliance and security auditing.
"""
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.auth.auth_audit_log import AuthAuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating audit log entries."""

    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        performed_by_user_id: int,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            user_id: User ID being acted upon (target)
            action: Action performed (e.g., 'CREATE_USER', 'ASSIGN_ROLE', 'REVOKE_ROLE')
            entity_type: Type of entity (e.g., 'USER', 'ROLE_ASSIGNMENT')
            entity_id: ID of the entity
            performed_by_user_id: User ID of the admin performing the action (actor)
            details: Optional additional details as JSON
        """
        try:
            # Convert details dict to JSON string if provided
            metadata_json = None
            if details:
                # Include entity_type and entity_id in metadata
                full_details = {
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    **details
                }
                metadata_json = json.dumps(full_details)
            
            audit_entry = AuthAuditLog(
                actor_user_id=performed_by_user_id,
                action_code=action,
                target_user_id=user_id,
                metadata_json=metadata_json
            )
            db.add(audit_entry)
            logger.info(
                f"Audit log created: {action} for user {user_id} "
                f"by {performed_by_user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}", exc_info=True)
            # Don't raise - audit log failure should not block business operations
