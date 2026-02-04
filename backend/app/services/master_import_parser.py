"""
Excel parser for Master Skills Import.
Parses Excel files with columns: Category | SubCategory | Skill Name | Alias
"""
import logging
from typing import List, Optional, Dict
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


class MasterImportParser:
    """Parser for master skills import Excel files."""
    
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
        
        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
            logger.info(f"Excel loaded: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            error_msg = f"Failed to parse Excel file: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
        
        # Log detected columns for debugging
        logger.info(f"Detected Excel columns: {', '.join(df.columns)}")
        
        # Validate columns
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
        
        # Parse rows
        rows: List[MasterSkillRow] = []
        
        for idx, row in df.iterrows():
            row_number = idx + 2  # Excel row number (1-based + header row)
            
            try:
                category = str(row[column_map["category"]]).strip()
                subcategory = str(row[column_map["subcategory"]]).strip()
                skill_name = str(row[column_map["skill name"]]).strip()
                alias_text = str(row[column_map["alias"]]).strip()
                
                # Skip empty rows
                if (category in ["", "nan", "None"] and 
                    subcategory in ["", "nan", "None"] and 
                    skill_name in ["", "nan", "None"]):
                    continue
                
                # Validate required fields
                if category in ["", "nan", "None"]:
                    self.errors.append({
                        "row_number": row_number,
                        "error_type": "VALIDATION_ERROR",
                        "message": "Category is required"
                    })
                    continue
                
                if subcategory in ["", "nan", "None"]:
                    self.errors.append({
                        "row_number": row_number,
                        "category": category,
                        "error_type": "VALIDATION_ERROR",
                        "message": "SubCategory is required"
                    })
                    continue
                
                if skill_name in ["", "nan", "None"]:
                    self.errors.append({
                        "row_number": row_number,
                        "category": category,
                        "subcategory": subcategory,
                        "error_type": "VALIDATION_ERROR",
                        "message": "Skill Name is required"
                    })
                    continue
                
                # Parse aliases (comma-separated)
                aliases = []
                if alias_text not in ["", "nan", "None"]:
                    aliases = [a.strip() for a in alias_text.split(",") if a.strip()]
                
                # Create normalized versions
                category_norm = normalize_key(category)
                subcategory_norm = normalize_key(subcategory)
                skill_name_norm = normalize_key(skill_name)
                aliases_norm = [normalize_key(a) for a in aliases]
                
                master_row = MasterSkillRow(
                    row_number=row_number,
                    category=category,
                    subcategory=subcategory,
                    skill_name=skill_name,
                    aliases=aliases,
                    category_norm=category_norm,
                    subcategory_norm=subcategory_norm,
                    skill_name_norm=skill_name_norm,
                    aliases_norm=aliases_norm                )
                
                rows.append(master_row)
                
            except Exception as e:
                # Log the exception with details for debugging
                logger.warning(
                    f"Error parsing row {row_number}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                self.errors.append({
                    "row_number": row_number,
                    "error_type": "VALIDATION_ERROR",
                    "message": f"Error parsing row: {type(e).__name__}: {str(e)}"
                })
                continue
        
        logger.info(f"Parsing complete: {len(rows)} valid rows, {len(self.errors)} errors")
        return rows
