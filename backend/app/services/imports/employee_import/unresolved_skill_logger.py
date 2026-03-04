"""
Unresolved skill logging for employee import.

Single Responsibility: Log unresolved skills to database and file.
"""
import logging
from typing import Dict
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError, OperationalError

from app.models.raw_skill_input import RawSkillInput
from app.models import Employee, SubSegment

logger = logging.getLogger(__name__)


class UnresolvedSkillLogger:
    """Logs unresolved skills to database and text file."""
    
    # Class-level flags to share state across all logger instances
    _schema_warning_logged = False
    _use_new_schema = True  # Assume new schema; detect if not
    
    def __init__(self, db: Session):
        self.db = db
        self.normalize_name = None  # Will be injected
        self.job_id = None  # Import job ID for tracking
    
    def set_name_normalizer(self, normalizer_func):
        """Inject name normalization function."""
        self.normalize_name = normalizer_func
    
    def set_job_id(self, job_id: str):
        """Set the import job ID for linking raw_skill_inputs to the import run."""
        self.job_id = job_id
    
    def record_unresolved_skill(self, skill_name: str, employee_id: int,
                                sub_segment_id: int, timestamp: datetime,
                                resolution_method: str = None,
                                resolution_confidence: float = None):
        """
        Log unresolved skill to raw_skill_inputs table for manual review.
        
        Backwards-compatible: works both before and after migration that adds
        job_id and status columns. Falls back to file-only logging if schema
        is outdated.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
            resolution_method: Optional resolution method ('needs_review', etc.)
            resolution_confidence: Optional confidence score (0.0-1.0) for embedding matches
        """
        normalized_text = self.normalize_name(skill_name) if self.normalize_name else skill_name.lower().strip()
        
        # Always log to file as backup
        self._log_to_file(skill_name, employee_id, sub_segment_id, timestamp, resolution_method, resolution_confidence)
        
        # Skip DB if we already know schema is outdated
        if not UnresolvedSkillLogger._use_new_schema:
            return
        
        # Use nested transaction (savepoint) to isolate this INSERT
        # If it fails, only this operation is rolled back, not the whole import
        try:
            with self.db.begin_nested():
                raw_input = RawSkillInput(
                    job_id=self.job_id,  # Link to import job
                    raw_text=skill_name,  # Original text from Excel
                    normalized_text=normalized_text,
                    sub_segment_id=sub_segment_id,
                    source_type="excel_import",  # Source identifier
                    employee_id=employee_id,
                    resolved_skill_id=None,  # Not resolved yet (or needs review)
                    resolution_method=resolution_method,  # e.g., 'needs_review' or None
                    resolution_confidence=resolution_confidence,  # e.g., 0.85 or None
                    status="UNRESOLVED",
                    created_at=timestamp
                )
                self.db.add(raw_input)
                # Force flush to detect schema issues early
                self.db.flush()
            
            self._log_success(skill_name, resolution_method, resolution_confidence)
        except (ProgrammingError, OperationalError) as e:
            # Check if this is a missing column error
            # Savepoint is automatically rolled back by context manager exit
            error_msg = str(e).lower()
            if "job_id" in error_msg or "status" in error_msg or "undefinedcolumn" in error_msg or "undefined" in error_msg:
                # Mark schema as outdated - skip DB for rest of import
                UnresolvedSkillLogger._use_new_schema = False
                if not UnresolvedSkillLogger._schema_warning_logged:
                    logger.warning(
                        "⚠️  raw_skill_inputs table missing job_id/status columns. "
                        "Falling back to file-only logging. "
                        "Run migration to enable DB logging: alembic upgrade head"
                    )
                    UnresolvedSkillLogger._schema_warning_logged = True
            else:
                # Different error - log and continue (don't break import)
                logger.error(f"Failed to log unresolved skill '{skill_name}' to DB: {e}")
        except Exception as e:
            # Savepoint automatically rolled back
            logger.error(f"Failed to log unresolved skill '{skill_name}': {e}")
            # Don't re-raise - logging failure shouldn't break the import
    
    def _log_success(self, skill_name: str, resolution_method: str = None, 
                     resolution_confidence: float = None):
        """Log successful skill recording."""
        if resolution_method == "needs_review":
            logger.info(f"📝 Logged skill '{skill_name}' needing review (confidence={resolution_confidence:.4f}) to raw_skill_inputs")
        else:
            logger.info(f"📝 Logged unresolved skill '{skill_name}' to raw_skill_inputs")

    def _log_to_file(self, skill_name: str, employee_id: int,
                     sub_segment_id: int, timestamp: datetime,
                     resolution_method: str = None,
                     resolution_confidence: float = None):
        """
        Log unresolved skill to a text file in backend folder for easy review.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
            resolution_method: Optional resolution method
            resolution_confidence: Optional confidence score
        """
        try:
            # Get backend folder path (parent of app folder)
            backend_folder = Path(__file__).parent.parent.parent.parent
            log_file = backend_folder / "unresolved_skills.txt"
            
            # Get employee info for better context
            employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
            employee_name = employee.full_name if employee else f"ID:{employee_id}"
            employee_zid = employee.zid if employee else "Unknown"
              # Get sub-segment info
            sub_segment = self.db.query(SubSegment).filter(SubSegment.sub_segment_id == sub_segment_id).first()
            sub_segment_name = sub_segment.sub_segment_name if sub_segment else f"ID:{sub_segment_id}"
            
            # Format log entry with resolution info
            status = "NEEDS_REVIEW" if resolution_method == "needs_review" else "UNRESOLVED"
            confidence_str = f" (confidence={resolution_confidence:.4f})" if resolution_confidence else ""
            
            log_entry = (
                f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{status}: \"{skill_name}\"{confidence_str} | "
                f"Employee: {employee_name} ({employee_zid}) | "
                f"Sub-Segment: {sub_segment_name}\n"
            )
            
            # Append to file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            logger.debug(f"Logged unresolved skill to {log_file}")
            
        except Exception as e:
            # Don't fail the import if file logging fails
            logger.warning(f"Failed to log unresolved skill to file: {e}")
