"""
Unresolved skill logging for employee import.

Single Responsibility: Log unresolved skills to database and file.
"""
import logging
from typing import Dict
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.raw_skill_input import RawSkillInput
from app.models import Employee, SubSegment

logger = logging.getLogger(__name__)


class UnresolvedSkillLogger:
    """Logs unresolved skills to database and text file."""
    
    def __init__(self, db: Session):
        self.db = db
        self.normalize_name = None  # Will be injected
    
    def set_name_normalizer(self, normalizer_func):
        """Inject name normalization function."""
        self.normalize_name = normalizer_func
    
    def record_unresolved_skill(self, skill_name: str, employee_id: int,
                                sub_segment_id: int, timestamp: datetime):
        """
        Log unresolved skill to raw_skill_inputs table for manual review.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
        """
        try:
            # Use correct field names for RawSkillInput model
            raw_input = RawSkillInput(
                raw_text=skill_name,  # Original text from Excel
                normalized_text=self.normalize_name(skill_name) if self.normalize_name else skill_name.lower().strip(),
                sub_segment_id=sub_segment_id,
                source_type="excel_import",  # Source identifier
                employee_id=employee_id,
                resolved_skill_id=None,  # Not resolved yet
                resolution_method=None,
                resolution_confidence=None,
                created_at=timestamp
            )
            self.db.add(raw_input)
            logger.info(f"📝 Logged unresolved skill '{skill_name}' to raw_skill_inputs")
            
            # Also log to text file for easy review
            self._log_to_file(skill_name, employee_id, sub_segment_id, timestamp)
            
        except Exception as e:
            logger.error(f"Failed to log unresolved skill '{skill_name}': {e}")

    def _log_to_file(self, skill_name: str, employee_id: int,
                     sub_segment_id: int, timestamp: datetime):
        """
        Log unresolved skill to a text file in backend folder for easy review.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
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
            
            # Format log entry
            log_entry = (
                f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"UNRESOLVED: \"{skill_name}\" | "
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
