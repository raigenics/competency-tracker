"""
Master Import Parser - Facade for Excel parsing.

Single Responsibility: Provide backward-compatible interface to the new ExcelParser.
"""
import logging
from typing import List
from .excel_parser import ExcelParser, MasterSkillRow

logger = logging.getLogger(__name__)


class MasterImportParser:
    """Parser for master skills import Excel files.
    
    This is a backward-compatible wrapper around the refactored ExcelParser.
    """
    
    # Expected column names (case-insensitive)
    EXPECTED_COLUMNS = ["category", "subcategory", "skill name", "alias"]
    
    def __init__(self):
        self._parser = ExcelParser()
    
    @property
    def errors(self):
        """Expose errors from underlying parser."""
        return self._parser.errors
    
    def parse_excel(self, file_content: bytes) -> List[MasterSkillRow]:
        """
        Parse Excel file and return list of MasterSkillRow objects.
        
        Args:
            file_content: Bytes content of the Excel file
            
        Returns:
            List of MasterSkillRow objects
            
        Raises:
            ValueError: If file cannot be parsed or has invalid structure
        """
        return self._parser.parse_excel(file_content)
