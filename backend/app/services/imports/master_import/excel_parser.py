"""
Excel parser for Master Skills Import.
Parses Excel files with columns: Category | SubCategory | Skill Name | Alias

Single Responsibility: Excel file parsing and validation
"""
import logging
from typing import List, Dict
from dataclasses import dataclass
import pandas as pd
from io import BytesIO

logger = logging.getLogger(__name__)


@dataclass
class MasterSkillRow:
    """Represents a single row from the master skills import Excel file."""
    row_number: int
    category: str
    subcategory: str
    skill_name: str
    aliases: List[str]  # Parsed from comma-separated alias column
    
    # Normalized versions for matching
    category_norm: str
    subcategory_norm: str
    skill_name_norm: str
    aliases_norm: List[str]


class ExcelParser:
    """Parser for master skills import Excel files.
    
    Single Responsibility: Parse and validate Excel structure.
    """
    
    # Expected column names (case-insensitive)
    EXPECTED_COLUMNS = ["category", "subcategory", "skill name", "alias"]
    
    def __init__(self):
        self.errors: List[Dict] = []
    
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
        from app.utils.normalization import normalize_key
        
        self.errors = []
        
        # Read Excel file
        df = self._read_excel_file(file_content)
        
        # Validate column structure
        column_map = self._validate_columns(df)
        
        # Parse rows
        rows = self._parse_rows(df, column_map, normalize_key)
        
        logger.info(f"Parsing complete: {len(rows)} valid rows, {len(self.errors)} errors")
        return rows
    
    def _read_excel_file(self, file_content: bytes) -> pd.DataFrame:
        """Read Excel file into DataFrame."""
        try:
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
            logger.info(f"Excel loaded: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"Detected Excel columns: {', '.join(df.columns)}")
            return df
        except Exception as e:
            error_msg = f"Failed to parse Excel file: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    
    def _validate_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Validate Excel columns and create mapping.
        
        Returns:
            Dict mapping expected column names to actual column names
        """
        df_columns_lower = [col.strip().lower() for col in df.columns]
        
        if len(df_columns_lower) < 4:
            error_msg = (
                f"Excel file must have at least 4 columns: Category, SubCategory, Skill Name, Alias. "
                f"Found {len(df.columns)} columns: {', '.join(df.columns)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Map columns (case-insensitive)
        column_map = {}
        missing_columns = []
        
        for expected_col in self.EXPECTED_COLUMNS:
            found = False
            for idx, actual_col in enumerate(df_columns_lower):
                if expected_col == actual_col:
                    column_map[expected_col] = df.columns[idx]
                    found = True
                    break
            
            if not found:
                missing_columns.append(expected_col)
        
        if missing_columns:
            error_msg = (
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Available columns: {', '.join(df.columns)}. "
                f"Note: Column names are case-insensitive."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Column mapping successful: {column_map}")
        return column_map
    
    def _parse_rows(self, df: pd.DataFrame, column_map: Dict[str, str], 
                    normalize_key: callable) -> List[MasterSkillRow]:
        """Parse DataFrame rows into MasterSkillRow objects."""
        rows: List[MasterSkillRow] = []
        
        for idx, row in df.iterrows():
            row_number = idx + 2  # Excel row number (1-based + header row)
            
            try:
                master_row = self._parse_single_row(row, row_number, column_map, normalize_key)
                if master_row:
                    rows.append(master_row)
            except Exception as e:
                logger.warning(
                    f"Error parsing row {row_number}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                self.errors.append({
                    "row_number": row_number,
                    "error_type": "VALIDATION_ERROR",
                    "message": f"Error parsing row: {type(e).__name__}: {str(e)}"
                })
        
        return rows
    
    def _parse_single_row(self, row, row_number: int, column_map: Dict[str, str],
                         normalize_key: callable) -> MasterSkillRow:
        """Parse a single row into MasterSkillRow."""
        category = str(row[column_map["category"]]).strip()
        subcategory = str(row[column_map["subcategory"]]).strip()
        skill_name = str(row[column_map["skill name"]]).strip()
        alias_text = str(row[column_map["alias"]]).strip()
        
        # Skip empty rows
        if self._is_empty_row(category, subcategory, skill_name):
            return None
        
        # Validate required fields
        if not self._validate_row_fields(row_number, category, subcategory, skill_name):
            return None
        
        # Parse aliases (comma-separated)
        aliases = self._parse_aliases(alias_text)
        
        # Create normalized versions
        category_norm = normalize_key(category)
        subcategory_norm = normalize_key(subcategory)
        skill_name_norm = normalize_key(skill_name)
        aliases_norm = [normalize_key(a) for a in aliases]
        
        return MasterSkillRow(
            row_number=row_number,
            category=category,
            subcategory=subcategory,
            skill_name=skill_name,
            aliases=aliases,
            category_norm=category_norm,
            subcategory_norm=subcategory_norm,
            skill_name_norm=skill_name_norm,
            aliases_norm=aliases_norm
        )
    
    def _is_empty_row(self, category: str, subcategory: str, skill_name: str) -> bool:
        """Check if row is empty."""
        return (category in ["", "nan", "None"] and 
                subcategory in ["", "nan", "None"] and 
                skill_name in ["", "nan", "None"])
    
    def _validate_row_fields(self, row_number: int, category: str, 
                            subcategory: str, skill_name: str) -> bool:
        """Validate required fields in a row."""
        if category in ["", "nan", "None"]:
            self.errors.append({
                "row_number": row_number,
                "error_type": "VALIDATION_ERROR",
                "message": "Category is required"
            })
            return False
        
        if subcategory in ["", "nan", "None"]:
            self.errors.append({
                "row_number": row_number,
                "category": category,
                "error_type": "VALIDATION_ERROR",
                "message": "SubCategory is required"
            })
            return False
        
        if skill_name in ["", "nan", "None"]:
            self.errors.append({
                "row_number": row_number,
                "category": category,
                "subcategory": subcategory,
                "error_type": "VALIDATION_ERROR",
                "message": "Skill Name is required"
            })
            return False
        
        return True
    
    def _parse_aliases(self, alias_text: str) -> List[str]:
        """Parse comma-separated aliases."""
        if alias_text in ["", "nan", "None"]:
            return []
        return [a.strip() for a in alias_text.split(",") if a.strip()]
