"""
Conflict detection for master import.

Single Responsibility: Detect conflicts and duplicates.
"""
import logging
from typing import List, Set, Dict
from .excel_parser import MasterSkillRow
from app.schemas.master_import import ImportError

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detects conflicts within file and against existing data."""
    
    def __init__(self):
        self.errors: List[ImportError] = []
    
    def detect_file_duplicates(self, rows: List[MasterSkillRow]) -> Set[int]:
        """
        Detect duplicate skills within the file itself.
        Returns set of row_numbers to skip.
        """
        seen_skills: Dict[str, int] = {}  # skill_norm -> first row_number
        skip_rows: Set[int] = set()
        
        for row in rows:
            if row.skill_name_norm in seen_skills:
                self.errors.append(ImportError(
                    row_number=row.row_number,
                    category=row.category,
                    subcategory=row.subcategory,
                    skill_name=row.skill_name,
                    error_type="DUPLICATE_IN_FILE",
                    message=f"Duplicate skill in file. First occurrence at row {seen_skills[row.skill_name_norm]}"
                ))
                skip_rows.add(row.row_number)
            else:
                seen_skills[row.skill_name_norm] = row.row_number
        
        if skip_rows:
            logger.warning(f"Detected {len(skip_rows)} duplicate rows in file")
        
        return skip_rows
